#!/usr/bin/env python3
# pylint: disable=invalid-name

"""Read Octopus Agile price data from an existing SQLite database and update a
   Pimoroni Blinkt! display."""

import sqlite3
import os
import sys
from urllib.request import pathname2url
import argparse
import eco_indicator

# Blinkt! defaults
DEFAULT_BRIGHTNESS = 10

# Inky pHAT defaults
DEFAULT_HIGHPRICE = 15.0
DEFAULT_LOWSLOTDURATION = 3

parser = argparse.ArgumentParser(description=('Update Eco Indicator display using SQLite data'))
parser.add_argument('--demo', '-d', action='store_true', help='display demo data')
parser.add_argument('--conf', '-c', default='config.yaml', help='specify config file')

args = parser.parse_args()
conf_file = args.conf

os.chdir(os.path.dirname(sys.argv[0]))

try:
    # connect to the database in rw mode so we can catch the error if it doesn't exist
    DB_URI = 'file:{}?mode=rw'.format(pathname2url('eco_indicator.sqlite'))
    conn = sqlite3.connect(DB_URI, uri=True)
    cursor = conn.cursor()
    print('Connected to database...')

except sqlite3.OperationalError as error:
    # handle missing database case
    raise SystemExit('Database not found - you need to run store_data.py first.') from error

config = eco_indicator.get_config(conf_file)

if config['Mode'] == 'agile_price':
    field_name = 'value_inc_vat'

elif config['Mode'] == 'carbon':
    field_name = 'intensity'

else:
    raise SystemExit('Error: invalid mode ' + config['Mode'] + 'in config.')

cursor.execute("SELECT * FROM eco WHERE valid_from > datetime('now', '-30 minutes') AND " + field_name + " IS NOT NULL")
data_rows = cursor.fetchall()

if len(data_rows) == 0:
    raise SystemExit('Error: No data found - perhaps you need to run store_data.py.')

if config['DisplayType'] == 'blinkt':
    eco_indicator.update_blinkt(config, data_rows, args.demo)

elif config['DisplayType'] == 'inkyphat':
    eco_indicator.update_inky(config, data_rows, args.demo)

else:
    raise SystemExit('Error: invalid display type ' + config['DisplayType'] + 'in config.')

# finish up the database operation
if conn:
    conn.commit()
    conn.close()