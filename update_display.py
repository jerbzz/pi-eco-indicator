#!/usr/bin/env python3

"""Read Octopus Agile price data from an existing SQLite database and update a
   Pimoroni Blinkt! display."""

import sqlite3
from urllib.request import pathname2url
import argparse
import yaml
import eco_indicator

# Blinkt! defaults
DEFAULT_BRIGHTNESS = 10

# Inky pHAT defaults
DEFAULT_HIGHPRICE = 15.0
DEFAULT_LOWSLOTDURATION = 3

parser = argparse.ArgumentParser(description=('Update Eco Indicator display using SQLite data'))
parser.add_argument('--demo', '-d', action='store_true',
                    help= 'display demo data',)

args = parser.parse_args()

try:
    # connect to the database in rw mode so we can catch the error if it doesn't exist
    DB_URI = 'file:{}?mode=rw'.format(pathname2url('eco_indicator.sqlite'))
    conn = sqlite3.connect(DB_URI, uri=True)
    cursor = conn.cursor()
    print('Connected to database...')

except sqlite3.OperationalError as error:
    # handle missing database case
    raise SystemExit('Database not found - you need to run store_data.py first.') from error

cursor.execute("SELECT * FROM eco WHERE valid_from > datetime('now', '-30 minutes')")
data_rows = cursor.fetchall()

# finish up the database operation
if conn:
    conn.commit()
    conn.close()

config = eco_indicator.get_config()

if config['DisplayType'] == 'blinkt':
    eco_indicator.update_blinkt(config, data_rows, args.demo)

if config['DisplayType'] == 'inkyphat':
    eco_indicator.update_inky(config, data_rows, args.demo)
