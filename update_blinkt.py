#!/usr/bin/env python3

"""Read Octopus Agile price data from an existing SQLite database and update a
   Pimoroni Blinkt! display."""

import sqlite3
from urllib.request import pathname2url
import argparse
import blinkt

# set brightness, IT BURNS MEEEEEE, 100 is the max
BRIGHTNESS = 10

# define colour values for LEDs. Edit as you please...
colourmap = { 'magenta': { 'r': 155, 'g': 0, 'b': 200 },
              'red': { 'r': 255, 'g': 0, 'b': 0 },
              'orange': { 'r': 255, 'g': 30, 'b': 0 },
              'yellow': { 'r': 180, 'g': 100, 'b': 0 },
              'green': { 'r': 0, 'g': 255, 'b': 0 },
              'cyan': { 'r': 0, 'g': 160, 'b': 180 },
              'blue': { 'r': 0, 'g': 0, 'b': 255 }, }

def price_to_colour(price):
    """edit this function to change price thresholds - be careful that you
    don't leave gaps in the numbers or strange things will very likely happen.
    prices are including VAT in p/kWh"""

    if price > 28:
        return 'magenta'
    if 28 >= price > 17:
        return 'red'
    if 17 >= price > 13.5:
        return 'orange'
    if 13.5 >= price > 10:
        return 'yellow'
    if 10 >= price > 5:
        return 'green'
    if 5 >= price > 0:
        return 'cyan'
    if price <= 0:
        return 'blue'
    raise SystemExit("Can't continue - price of " + str(price) +" doesn't make sense.")

parser = argparse.ArgumentParser(description=('Update Blinkt! display using SQLite data'))
parser.add_argument('--demo', '-d', action='store_true',
                    help= 'display configured colours, one per pixel',)

args = parser.parse_args()

if args.demo: 
    blinkt.clear()
    i = 0
    for colour in colourmap:
        blinkt.set_pixel(i, colourmap[colour]['r'],
            colourmap[colour]['g'], colourmap[colour]['b'], BRIGHTNESS/100)
        i += 1
    print ("Demo mode...")
    blinkt.set_clear_on_exit(False)
    blinkt.show()
    
else:
    try:
        # connect to the database in rw mode so we can catch the error if it doesn't exist
        DB_URI = 'file:{}?mode=rw'.format(pathname2url('agileprices.sqlite'))
        conn = sqlite3.connect(DB_URI, uri=True)
        cursor = conn.cursor()
        print('Connected to database...')
    except sqlite3.OperationalError as error:
        # handle missing database case
        raise SystemExit('Database not found - you need to run store_prices.py first.') from error

    cursor.execute("SELECT * FROM prices WHERE valid_from > datetime('now', '-30 minutes') LIMIT 8")
    rows = cursor.fetchall()

    # finish up the database operation
    if conn:
        conn.commit()
        conn.close()

    if not len(rows) >= 8:
        print('Not enough data to fill the display - we will get dark pixels.')

    blinkt.clear()

    i = 0

    for row in rows:
        print(str(i) + ": " + str(row[1]) + "p - " + str(price_to_colour(row[1])))
        PIXEL_VALUE_RED = colourmap[price_to_colour(row[1])]['r']
        PIXEL_VALUE_GREEN = colourmap[price_to_colour(row[1])]['g']
        PIXEL_VALUE_BLUE = colourmap[price_to_colour(row[1])]['b']
        blinkt.set_pixel(i, PIXEL_VALUE_RED,
            PIXEL_VALUE_GREEN, PIXEL_VALUE_BLUE, BRIGHTNESS/100)
        i += 1

    print ("Setting display...")
    blinkt.set_clear_on_exit(False)
    blinkt.show()
