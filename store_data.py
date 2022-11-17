#!/usr/bin/env python3
# pylint: disable=invalid-name

"""Use the public Octopus Energy API to request the half-hourly rates for the Agile tariff
for a particular region, and insert these into an SQLite database, dealing with duplicate
requests and pruning old data so that the DB doesn't grow infinitely."""

import sqlite3
import os
import sys
import time
from reprlib import Repr
from datetime import datetime
from urllib.request import pathname2url
import pytz
import requests
import argparse
import eco_indicator

AGILE_API_BASE = ('https://api.octopus.energy/v1/products/')

AGILE_IMPORT_35 = ('AGILE-18-02-21/electricity-tariffs/E-1R-AGILE-18-02-21-')
AGILE_IMPORT_55 = ('AGILE-22-07-22/electricity-tariffs/E-1R-AGILE-22-07-22-')
AGILE_IMPORT_78 = ('AGILE-22-08-31/electricity-tariffs/E-1R-AGILE-22-08-31-')
AGILE_IMPORT_VAR_100 = ('AGILE-VAR-22-10-19/electricity-tariffs/E-1R-AGILE-VAR-22-10-19-')

AGILE_EXPORT = ('AGILE-OUTGOING-19-05-13/electricity-tariffs/E-1R-AGILE-OUTGOING-19-05-13-')

AGILE_REGIONS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'P', 'N', 'J', 'H', 'K', 'L', 'M']

AGILE_API_TAIL = "/standard-unit-rates/"

CARBON_API_BASE = ('https://api.carbonintensity.org.uk')

CARBON_REGIONS = {'A': '/regional/intensity/{from_time}/fw48h/regionid/10',
                  'B': '/regional/intensity/{from_time}/fw48h/regionid/9',
                  'C': '/regional/intensity/{from_time}/fw48h/regionid/13',
                  'D': '/regional/intensity/{from_time}/fw48h/regionid/6',
                  'E': '/regional/intensity/{from_time}/fw48h/regionid/8',
                  'F': '/regional/intensity/{from_time}/fw48h/regionid/4',
                  'G': '/regional/intensity/{from_time}/fw48h/regionid/3',
                  'P': '/regional/intensity/{from_time}/fw48h/regionid/1',
                  'N': '/regional/intensity/{from_time}/fw48h/regionid/2',
                  'J': '/regional/intensity/{from_time}/fw48h/regionid/14',
                  'H': '/regional/intensity/{from_time}/fw48h/regionid/12',
                  'K': '/regional/intensity/{from_time}/fw48h/regionid/7',
                  'L': '/regional/intensity/{from_time}/fw48h/regionid/11',
                  'M': '/regional/intensity/{from_time}/fw48h/regionid/5',
                  'Z': '/intensity/{from_time}/fw48h'}

MAX_RETRIES = 15 # give up once we've tried this many times to get the prices from the API

parser = argparse.ArgumentParser(description=('Read data from a remote API and store it in a local SQlite database'))
parser.add_argument('--conf', '-c', default='config.yaml', help='specify config file')
parser.add_argument('--print', '-p', action='store_true', help='print data which was retrieved (JSON format)')

args = parser.parse_args()
conf_file = args.conf

def get_data_from_api(_request_uri: str) -> dict:
    """using the provided URI, request data from the API and return a JSON object.
    Try to handle errors gracefully with retries when appropriate."""

    # Try to handle issues with the API - rare but do happen, using an
    # exponential sleep time up to 2**14 (16384) seconds, approx 4.5 hours.
    # We will keep trying for over 9 hours and then give up.

    retry_count = 0
    my_repr = Repr()
    my_repr.maxstring = 80 # let's avoid truncating our error messages too much

    while retry_count <= MAX_RETRIES:

        if retry_count == MAX_RETRIES:
            raise SystemExit('API retry limit exceeded.')

        try:
            success = False
            response = requests.get(_request_uri, timeout=5)
            response.raise_for_status()
            if response.status_code // 100 == 2:
                success = True

        except requests.exceptions.HTTPError as error:
            print(('API HTTP error ' + str(response.status_code) +
                   ',retrying in ' + str(2**retry_count) + 's'))
            time.sleep(2**retry_count)
            retry_count += 1

        except requests.exceptions.ConnectionError as error:
            print(('API connection error: ' + my_repr.repr(str(error)) +
                   ', retrying in ' + str(2**retry_count) + 's'))
            time.sleep(2**retry_count)
            retry_count += 1

        except requests.exceptions.Timeout:
            print('API request timeout, retrying in ' + str(2**retry_count) + 's')
            time.sleep(2**retry_count)
            retry_count += 1

        except requests.exceptions.RequestException as error:
            raise SystemExit('API Request error: ' + str(error)) from error

        if success:
            print('API request successful, status ' + str(response.status_code) + '.')
            if args.print: print(response.json())
            return response.json()

def insert_data(data: dict):
    """Insert our data records one by one, keep track of how many were successfully inserted
    and print the results of the insertion."""

    num_rows_inserted = 0

    if config['Mode'] == 'agile_import' or 'agile_export':
        for result in data['results']:
            # insert_record returns false if it was a duplicate record
            # or true if a record was successfully entered.
            if insert_record(result['valid_from'], result['value_inc_vat']):
                num_rows_inserted += 1

        if num_rows_inserted > 0:
            lastslot = datetime.strftime(datetime.strptime(
                data['results'][0]['valid_to'], "%Y-%m-%dT%H:%M:%SZ"), "%H:%M on %A %d %b")
            print(str(num_rows_inserted) + ' prices were inserted, ending at ' + lastslot + '.')
        else:
            print('No prices were inserted - maybe we have them'
                  ' already, or Octopus are late with their update.')

    if config['Mode'] == 'carbon':
        if config['DNORegion'] == 'Z':
            carbon_data = data['data']
        else:
            carbon_data = data['data']['data']

        for result in carbon_data:
            if insert_record(result['from'], result['intensity']['forecast']):
                num_rows_inserted += 1

        if num_rows_inserted > 0:
            lastslot = datetime.strftime(datetime.strptime(
                carbon_data[47]['from'], "%Y-%m-%dT%H:%MZ"), "%H:%M on %A %d %b")
            print(str(num_rows_inserted) + ' intensities were inserted, '
                  'ending at ' + lastslot + '.')
        else:
            print('No values were inserted - maybe we have them'
                  ' already, or carbonintensity.org.uk are late with their update.')

def insert_record(valid_from: str, data_value: float) -> bool:
    """Assuming we still have a cursor, take a tuple and stick it into the database.
       Return False if it was a duplicate record (not inserted) and True if a record
       was successfully inserted."""
    if not cursor:
        raise SystemExit('Database connection lost!')

    if config['Mode'] == 'agile_import' or 'agile_export':
        # make the date/time work for SQLite, it's picky about the format,
        # easier to use the built in SQLite datetime functions
        # when figuring out what records we want rather than trying to roll our own
        valid_from_formatted = datetime.strftime(
            datetime.strptime(valid_from, "%Y-%m-%dT%H:%M:%SZ"), "%Y-%m-%d %H:%M:%S")

        data_tuple = (valid_from_formatted, data_value)
        # print(data_tuple) # debug

        try:
            cursor.execute(
                "INSERT INTO 'eco'('valid_from', 'value_inc_vat') VALUES (?, ?) ON CONFLICT(valid_from) DO UPDATE SET value_inc_vat=excluded.value_inc_vat;", data_tuple)

        except sqlite3.Error as error:
            raise SystemError('Database error: ' + str(error)) from error

        else:
            return True # the record was inserted

    if config['Mode'] == 'carbon':
        valid_from_formatted = datetime.strftime(
            datetime.strptime(valid_from, "%Y-%m-%dT%H:%MZ"), "%Y-%m-%d %H:%M:%S")

        data_tuple = (valid_from_formatted, data_value)
        # print(data_tuple) # debug

        try:
            cursor.execute(
                "INSERT INTO 'eco'('valid_from', 'intensity') VALUES (?, ?) ON CONFLICT(valid_from) DO UPDATE SET intensity=excluded.intensity;", data_tuple)

        except sqlite3.Error as error:
            raise SystemError('Database error: ' + str(error)) from error

        else:
            return True # the record was inserted

    return False

def remove_old_data(age: str):
    """Delete old data from the database, we don't want to display those and we don't want it
    to grow too big. 'age' must be a string that SQLite understands"""
    if not cursor:
        raise SystemExit('Database connection lost before pruning data!')
    try:
        cursor.execute("SELECT COUNT(*) FROM eco "
                       "WHERE valid_from < datetime('now', '-" + age + "')")
        selected_rows = cursor.fetchall()
        num_old_rows = selected_rows[0][0]
        # I don't know why this doesn't just return an int rather than a list of a list of an int
        if num_old_rows > 0:
            cursor.execute("DELETE FROM eco WHERE valid_from < datetime('now', '-" + age + "')")
            print(str(num_old_rows) + ' unneeded data points from the past were deleted.')
        else:
            print('There were no old data points to delete.')
    except sqlite3.Error as error:
        print('Failed while trying to remove old data points from database: ', error)

os.chdir(os.path.dirname(sys.argv[0]))
config = eco_indicator.get_config(conf_file)

if config['Mode'] == 'agile_import':
    DNO_REGION = config['DNORegion']
    AGILE_CAP = config['AgileCap']

    if DNO_REGION in AGILE_REGIONS:
        print('Selected region ' + DNO_REGION)
    else:
        raise SystemExit('Error: DNO region ' + DNO_REGION + ' is not a valid choice.')
        
    if AGILE_CAP == 35:
        AGILE_VERSION = AGILE_IMPORT_35
    elif AGILE_CAP == 55:
        AGILE_VERSION = AGILE_IMPORT_55
    elif AGILE_CAP == 78:
        AGILE_VERSION = AGILE_IMPORT_78
    elif AGILE_CAP == 100:
        AGILE_VERSION = AGILE_IMPORT_VAR_100
    else:
        raise SystemExit('Error: Agile cap of ' + str(AGILE_CAP) + ' refers to an unknown tariff.')

    # Build the API for the request - public API so no authentication required
    request_uri = (AGILE_API_BASE + AGILE_VERSION + DNO_REGION + AGILE_API_TAIL)

elif config['Mode'] == 'carbon':
    DNO_REGION = config['DNORegion']

    if DNO_REGION in CARBON_REGIONS:
        print('Selected region ' + DNO_REGION)
    else:
        raise SystemExit('Error: DNO region ' + DNO_REGION + ' is not a valid choice.')

    # Build the API for the request - public API so no authentication required
    request_time = datetime.now().astimezone(pytz.utc).isoformat()
    request_uri = (CARBON_API_BASE + CARBON_REGIONS[DNO_REGION])
    request_uri = request_uri.format(from_time=request_time)

elif config['Mode'] == 'agile_export':
    DNO_REGION = config['DNORegion']

    if DNO_REGION in AGILE_REGIONS:
        print('Selected region ' + DNO_REGION)
    else:
        raise SystemExit('Error: DNO region ' + DNO_REGION + ' is not a valid choice.')

    # Build the API for the request - public API so no authentication required
    request_uri = (AGILE_API_BASE + AGILE_EXPORT + DNO_REGION + AGILE_API_TAIL)

else:
    raise SystemExit('Error: Invalid mode ' + config['Mode'] + ' passed to store_data.py')

try:
    # connect to the database in rw mode so we can catch the error if it doesn't exist
    DB_URI = 'file:{}?mode=rw'.format(pathname2url('eco_indicator.sqlite'))
    conn = sqlite3.connect(DB_URI, uri=True)
    cursor = conn.cursor()
    print('Connected to database...')

except sqlite3.OperationalError:
    # handle missing database case
    print('No database found. Creating a new one...')
    conn = sqlite3.connect('eco_indicator.sqlite')
    cursor = conn.cursor()
    # UNIQUE constraint prevents duplication of data on multiple runs of this script
    # ON CONFLICT FAIL allows us to count how many times this happens
    cursor.execute('CREATE TABLE eco (valid_from STRING PRIMARY KEY ON CONFLICT REPLACE, '
                   'value_inc_vat REAL, intensity REAL)')
    conn.commit()
    print('Database created... ')

data_rows = get_data_from_api(request_uri)

insert_data(data_rows)

remove_old_data('2 days')

# finish up the database operation
if conn:
    conn.commit()
    conn.close()
