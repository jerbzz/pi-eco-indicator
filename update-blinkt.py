#!/usr/bin/env python3

import sqlite3
from urllib.request import pathname2url
import blinkt

# set brightness, IT BURNS MEEEEEE, 100 is the max
brightness = 10

# define colour values for LEDs. Edit as you please...
colourmap = { 'magenta': { 'r': 155, 'g': 0, 'b': 200 },
              'red': { 'r': 255, 'g': 0, 'b': 0 },
              'orange': { 'r': 255, 'g': 30, 'b': 0 },
              'yellow': { 'r': 180, 'g': 100, 'b': 2 },
              'green': { 'r': 0, 'g': 255, 'b': 0 },
              'cyan': { 'r': 0, 'g': 0, 'b': 255 },
              'blue': { 'r': 0, 'g': 0, 'b': 255 }, }

def price_to_colour(price):
# edit this function to change price thresholds - be careful that you 
# don't leave gaps in the numbers or strange things will very likely happen.
# prices are including VAT in p/kWh

    if price > 28: return 'magenta'
    elif 28 >= price > 17: return 'red'
    elif 17 >= price > 13.5: return 'orange'
    elif 13.5 >= price > 10: return 'yellow'
    elif 10 >= price > 5: return 'green'
    elif 5 >= price > 0: return 'cyan'
    elif price <= 0: return 'blue'
    else: raise SystemExit("Can't continue - price of " + str(price) +" doesn't make sense.")

try:
    # connect to the database in rw mode so we can catch the error if it doesn't exist
    dburi = 'file:{}?mode=rw'.format(pathname2url('agileprices.sqlite'))
    conn = sqlite3.connect(dburi, uri=True)
    cursor = conn.cursor()
    print('Connected to database...')
except sqlite3.OperationalError:
    # handle missing database case
    raise SystemExit('Database not found - you need to run store-prices.py first.')

cursor.execute("SELECT * FROM prices WHERE valid_from > datetime('now', '-30 minutes') LIMIT 8")
rows = cursor.fetchall()
 
# finish up the database operation
if (conn):
    conn.commit()
    conn.close()

if not (len(rows) >= 8): print('Not enough data to fill the display - we will get dark pixels.')

blinkt.clear()

i = 0

for row in rows:
    print(str(i) + ": " + str(row[1]) + "p - " + str(price_to_colour(row[1])))
    r = colourmap[price_to_colour(row[1])]['r']
    g = colourmap[price_to_colour(row[1])]['g']
    b = colourmap[price_to_colour(row[1])]['b']
    blinkt.set_pixel(i, r, g, b, brightness/100)
    i += 1

print ("Setting display...")
blinkt.set_clear_on_exit(False)
blinkt.show()
