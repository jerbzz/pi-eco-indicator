#!/usr/bin/env python3

"""Use the public Octopus Energy API to request the half-hourly rates for the Agile tariff
for a particular region, and insert these into an SQLite database, dealing with duplicate
requests and pruning old data so that the DB doesn't grow infinitely."""

import sqlite3
import time
from reprlib import Repr
from datetime import datetime
from urllib.request import pathname2url
import requests
import yaml

DNO_REGIONS = ['A','B','C','D','E','F','G','P','N','J','H','K','L','M']

# hopefully these won't ever change
AGILE_TARIFF_BASE = (
  'https://api.octopus.energy/v1/products/AGILE-18-02-21/electricity-tariffs/E-1R-AGILE-18-02-21-')
AGILE_TARIFF_TAIL = "/standard-unit-rates/"

MAX_RETRIES = 15 # give up once we've tried this many times to get the prices from the API


def get_prices_from_api(request_uri: str) -> dict:
    """using the provided URI, request data from the Octopus API and return a JSON object.
    Try to handle errors gracefully with retries when appropriate."""

    # Try to handle issues with the API - rare but do happen, using an
    # exponential sleep time up to 2**14 (16384) seconds, approx 4.5 hours.
    # We will keep trying for over 9 hours and then give up.

    print('Requesting Agile prices from Octopus API...')
    retry_count = 0
    my_repr = Repr()
    my_repr.maxstring = 80 # let's avoid truncating our error messages too much

    while retry_count <= MAX_RETRIES:

        if retry_count == MAX_RETRIES:
            raise SystemExit ('API retry limit exceeded.')

        try:
            success = False
            response = requests.get(request_uri, timeout=5)
            response.raise_for_status()
            if response.status_code // 100 == 2:
                success = True
                return response.json()

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
            break


def insert_data (data: dict):
    """Insert our data records one by one, keep track of how many were successfully inserted
    and print the results of the insertion."""

    num_prices_inserted = 0
    num_duplicates = 0

    for result in data['results']:

        # insert_record returns false if it was a duplicate record
        # or true if a record was successfully entered.
        if insert_record(result['valid_from'], result['value_inc_vat']):
            num_prices_inserted += 1
        else:
            num_duplicates += 1

    if num_duplicates > 0:
        print('Ignoring ' + str(num_duplicates) + ' duplicate prices...')

    if num_prices_inserted > 0:
        lastslot = datetime.strftime(datetime.strptime(
            data['results'][0]['valid_to'],"%Y-%m-%dT%H:%M:%SZ"),"%H:%M on %A %d %b")
        print(str(num_prices_inserted) + ' prices were inserted, ending at ' + lastslot + '.')
    else:
        print('No prices were inserted - maybe we have them'
               ' already or Octopus are late with their update.')


def insert_record(valid_from: str, value_inc_vat: float) -> bool:
    """Assuming we still have a cursor, take a tuple and stick it into the database.
       Return False if it was a duplicate record (not inserted) and True if a record
       was successfully inserted."""
    if not cursor:
        raise SystemExit('Database connection lost!')

    # make the date/time work for SQLite, it's picky about the format,
    # easier to use the built in SQLite datetime functions
    # when figuring out what records we want rather than trying to roll our own
    valid_from_formatted = datetime.strftime(
        datetime.strptime(valid_from, "%Y-%m-%dT%H:%M:%SZ"), "%Y-%m-%d %H:%M:%S")

    data_tuple = (valid_from_formatted, value_inc_vat)

    try:
        cursor.execute(
            "INSERT INTO 'prices'('valid_from', 'value_inc_vat') VALUES (?, ?);", data_tuple)

    except sqlite3.Error as error:
        # ignore expected UNIQUE constraint errors when trying to duplicate prices
        # this will only raise SystemExit if it's **not** a 'UNIQUE' error
        if str.find(str(error), 'UNIQUE') == -1:
            raise SystemExit('Database error: ' + str(error)) from error

        return False # it was a duplicate record and wasn't inserted

    else:
        return True # the record was inserted


def remove_old_prices(age: str):
    """Delete old prices from the database, we don't want to display those and we don't want it
    to grow too big. 'age' must be a string that SQLite understands"""
    if not cursor:
        raise SystemExit('Database connection lost before pruning prices!')
    try:
        cursor.execute("SELECT COUNT(*) FROM prices "
            "WHERE valid_from < datetime('now', '-" + age + "')")
        selected_rows = cursor.fetchall()
        num_old_rows = selected_rows[0][0]
        # I don't know why this doesn't just return an int rather than a list of a list of an int
        if num_old_rows > 0:
            cursor.execute("DELETE FROM prices WHERE valid_from < datetime('now', '-" + age + "')")
            print(str(num_old_rows) + ' unneeded prices from the past were deleted.')
        else:
            print('There were no old prices to delete.')
    except sqlite3.Error as error:
        print('Failed while trying to remove old prices from database: ', error)

try:
    config_file = open('config.yaml', 'r')
except FileNotFoundError as no_config:
    raise SystemExit('Unable to find config.yaml') from no_config

try:
    config = yaml.safe_load(config_file)
except yaml.YAMLError as config_err:
    raise SystemExit('Error reading configuration: ' + str(config_err)) from config_err

if not 'DNORegion' in config:
    raise SystemExit('Error: DNORegion not found in config.yaml')

DNO_REGION = config['DNORegion']

if DNO_REGION in DNO_REGIONS:
    print('Selected region ' + DNO_REGION)
else:
    raise SystemExit('Error: DNO region ' + DNO_REGION + ' is not a valid choice.')

# Build the API for the request - public API so no authentication required
AGILE_TARIFF_URI = (AGILE_TARIFF_BASE + DNO_REGION + AGILE_TARIFF_TAIL)

data_rows = get_prices_from_api(AGILE_TARIFF_URI)

try:
    # connect to the database in rw mode so we can catch the error if it doesn't exist
    DB_URI = 'file:{}?mode=rw'.format(pathname2url('agileprices.sqlite'))
    conn = sqlite3.connect(DB_URI, uri=True)
    cursor = conn.cursor()
    print('Connected to database...')

except sqlite3.OperationalError:
    # handle missing database case
    print('No database found. Creating a new one...')
    conn = sqlite3.connect('agileprices.sqlite')
    cursor = conn.cursor()
    # UNIQUE constraint prevents duplication of data on multiple runs of this script
    # ON CONFLICT FAIL allows us to count how many times this happens
    cursor.execute('CREATE TABLE prices (valid_from STRING UNIQUE ON CONFLICT FAIL, '
                    'value_inc_vat REAL)')
    conn.commit()
    print('Database created... ')

insert_data(data_rows)

remove_old_prices('2 days')

# finish up the database operation
if conn:
    conn.commit()
    conn.close()
