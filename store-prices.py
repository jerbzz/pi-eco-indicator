#!/usr/bin/env python3

import sqlite3
from urllib.request import pathname2url
from datetime import datetime, timezone
import requests
import argparse
from argparse import RawTextHelpFormatter
from reprlib import Repr
import time

# hopefully this won't ever change
AGILE_TARIFF_BASE = 'https://api.octopus.energy/v1/products/AGILE-18-02-21/electricity-tariffs/E-1R-AGILE-18-02-21-'
AGILE_TARIFF_TAIL = '/standard-unit-rates/'

# let's get the region from the command line and make sure it's allowed!
parser = argparse.ArgumentParser(description='Retrieve Octopus Agile prices and store in a SQLite database', 
                                 formatter_class=RawTextHelpFormatter)
parser.add_argument('--region', '-r', nargs=1, type=str, metavar='X', action='store', required=True,
                    help= """
https://en.wikipedia.org/wiki/Distribution_network_operator
A = East England
B = East Midlands
C = London
D = North Wales, Merseyside and Cheshire
E = West Midlands
F = North East England
G = North West England
P = North Scotland
N = South and Central Scotland
J = South East England
H = Southern England
K = South Wales
L = South West England
M = Yorkshire""",
                    choices = ['A','B','C','D','E','F','G','P','N','J','H','K','L','M'])
args = parser.parse_args()
print('Selected region ' + args.region[0])
agile_tariff_region = args.region[0]

try:
    # connect to the database in rw mode so we can catch the error if it doesn't exist
    dburi = 'file:{}?mode=rw'.format(pathname2url('agileprices.sqlite'))
    conn = sqlite3.connect(dburi, uri=True)
    cursor = conn.cursor()
    print('Connected to database...')
except sqlite3.OperationalError:
    # handle missing database case
    print('No database found. Creating a new one...')
    conn = sqlite3.connect('agileprices.sqlite')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE prices (valid_from STRING UNIQUE ON CONFLICT FAIL, value_inc_vat REAL)')
    # UNIQUE constraint prevents duplication of data on multiple runs of this script
    # ON CONFLICT FAIL allows us to count how many times this happens
    conn.commit()
    print('Database created... ')

# Build the API request - public API so no authentication required
agile_tariff_uri=(AGILE_TARIFF_BASE + agile_tariff_region + AGILE_TARIFF_TAIL)
print('Requesting Agile prices from Octopus API...')

# Try to handle issues with the API - rare but do happen, using an
# exponential sleep time up to 2**14 (16384) seconds, approx 4.5 hours.
# We will keep trying for over 9 hours and then give up.
retry_count = 0
max_retries = 15
request_success = False
myrepr = Repr()
myrepr.maxstring = 80 # let's avoid truncating our error messages too much

while retry_count <= max_retries:
    if retry_count == max_retries: raise SystemExit ('API retry limit exceeded.')
    try:
        response = requests.get(agile_tariff_uri, timeout=5)
        response.raise_for_status
        if response.status_code // 100 == 2: success = True
        pricedata = response.json()
    except requests.exceptions.HTTPError as error:
        print('API HTTP error ' + str(response.status_code) + ', retrying in ' + str(2**retrycount) + 's')
        time.sleep(2**retrycount)
        retrycount += 1
    except requests.exceptions.ConnectionError as error:
        print('API connection error: ' + myrepr.repr(str(error)) + ', retrying in ' + str(2**retrycount) + 's')
        time.sleep(2**retrycount)
        retrycount += 1
    except requests.exceptions.Timeout:
        print('API request timeout, retrying in ' + str(2**retrycount) + 's')
        time.sleep(2**retrycount)
        retrycount += 1
    except requests.exceptions.RequestException as error:
        raise SystemExit('API Request error: ' + str(error))
    if success:
        print('API request successful, status ' + str(response.status_code) + '.')
        break

numprices = 0
numerrors = 0

for result in pricedata['results']:
    # make the date/time work for SQLite, it's picky about the format, easier to use the built in SQLite datetime functions
    # when figuring out what records we want rather than trying to roll our own
    valid_from_formatted = datetime.strftime(datetime.strptime(result['valid_from'],"%Y-%m-%dT%H:%M:%SZ"),"%Y-%m-%d %H:%M:%S")

    data_tuple = (valid_from_formatted, result['value_inc_vat'])

    # now store in the database safely
    try: 
        cursor.execute("INSERT INTO 'prices'('valid_from', 'value_inc_vat') VALUES (?, ?);", data_tuple)
    except sqlite3.Error as error:
        if (str.find(str(error), 'UNIQUE') == -1): # ignore expected UNIQUE constraint errors when trying to duplicate prices
            raise SystemExit('Database error: ' + str(error))
        else:
            numerrors += 1
    else:
        numprices += 1

print('Ignoring ' + str(numerrors) + ' duplicate prices...')

if (numprices > 0):
    lastslot = datetime.strftime(datetime.strptime(pricedata['results'][0]['valid_to'],"%Y-%m-%dT%H:%M:%SZ"),"%H:%M on %A %d %b")
    print(str(numprices) + ' prices were inserted, ending at ' + lastslot + '.')
else:
    print('No prices were inserted - maybe we have them already or Octopus are late with their update.')
    
# prune old prices from the database, we don't want to display those and we don't want to grow too big
try:
    cursor.execute("SELECT COUNT(*) FROM prices WHERE valid_from < datetime('now', '-2 days')")
    rows = cursor.fetchall()
    num_old_rows = rows[0][0] # I don't know why this doesn't just return an int rather than a list of a list of an int
    if num_old_rows > 0:
        cursor.execute("DELETE FROM prices WHERE valid_from < datetime('now', '-2 days')")
        print(str(num_old_rows) + ' unneeded prices from the past were deleted.')
    else:
        print('There were no old prices to delete.')
except sqlite3.Error as error:
    print('Failed while trying to remove old prices from database: ', error)

# finish up the database operation
if (conn):
    conn.commit()
    conn.close()   
