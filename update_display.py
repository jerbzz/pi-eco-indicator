#!/usr/bin/env python3

"""Read Octopus Agile price data from an existing SQLite database and update a
   Pimoroni Blinkt! display."""

import sqlite3
from urllib.request import pathname2url
import argparse
import blinkt
import yaml
from inky.eeprom import read_eeprom

DEFAULT_BRIGHTNESS = 10

def deep_get(d, keys, default=None):
    """
    Example:
        d = {'meta': {'status': 'OK', 'status_code': 200}}
        deep_get(d, ['meta', 'status_code'])          # => 200
        deep_get(d, ['garbage', 'status_code'])       # => None
        deep_get(d, ['meta', 'garbage'], default='-') # => '-'
    """
    assert type(keys) is list
    if d is None:
        return default
    if not keys:
        return d
    return deep_get(d.get(keys[0]), keys[1:], default)

def get_config() -> dict:
    """
    Read config file and do some basic checks that we have what we need.
    If not, set sensible defaults or bail out.
    """
    try:
        config_file = open('config.yaml', 'r')
    except FileNotFoundError:
        raise SystemExit('Unable to find config.yaml')

    try:
        config = yaml.safe_load(config_file)
    except yaml.YAMLError as err:
        raise SystemExit('Error reading configuration: ' + str(err))

    if config['DisplayType'] == None:
        raise SystemExit('Error: DisplayType not found in config.yaml')

    if config['DisplayType'] == 'blinkt':
        print ('Blinkt! display selected.')
        conf_brightness = deep_get(config, ['Blinkt', 'Brightness'])
        if not (type(conf_brightness) == int and 5 <= conf_brightness <= 100):
            print('Misconfigured brightness value: ' + str(conf_brightness) +
                  '. Using default of ' + str(DEFAULT_BRIGHTNESS) + '.')
            config['Blinkt']['Brightness'] = DEFAULT_BRIGHTNESS

    elif config['DisplayType'] == 'inkyphat':
        inky_eeprom = read_eeprom()

        if inky_eeprom == None:
            raise SystemExit('Error: Inky pHAT display not found')
        else:
            print ('Inky pHAT display selected.')
            
    else:
        raise SystemExit('Error: unknown DisplayType ' + config['DisplayType'] + ' in config.yaml' )
    
    return config

# define colour values for leds. edit as you please...
COLOUR_MAP = { 'magenta': { 'r': 155, 'g': 0, 'b': 200 },
              'red': { 'r': 255, 'g': 0, 'b': 0 },
              'orange': { 'r': 255, 'g': 30, 'b': 0 },
              'yellow': { 'r': 180, 'g': 100, 'b': 0 },
              'green': { 'r': 0, 'g': 255, 'b': 0 },
              'cyan': { 'r': 0, 'g': 160, 'b': 180 },
              'blue': { 'r': 0, 'g': 0, 'b': 255 }, }

def price_to_colour(price: float) -> str:
    """Edit this function to change price thresholds - be careful that you
    don't leave gaps in the numbers or strange things will very likely happen.
    prices are including VAT in p/kWh"""

    if price > 28:
        pixel_colour = 'magenta'

    elif 28 >= price > 17:
        pixel_colour = 'red'

    elif 17 >= price > 13.5:
        pixel_colour = 'orange'

    elif 13.5 >= price > 10:
        pixel_colour = 'yellow'

    elif 10 >= price > 5:
        pixel_colour = 'green'

    elif 5 >= price > 0:
        pixel_colour = 'cyan'

    elif price <= 0:
        pixel_colour = 'blue'

    else:
        raise SystemExit("Can't continue - price of " + str(price) +" doesn't make sense.")

    return pixel_colour

def set_pixel(index: int, this_colour: str, this_brightness: int):
    """This function looks up the R, G, and B values for a given colour
    in the 'COLOUR_MAP' dictionary and passes them to the blinkt! set_pixel method."""

    pixel_value_red = COLOUR_MAP[this_colour]['r']
    pixel_value_green = COLOUR_MAP[this_colour]['g']
    pixel_value_blue = COLOUR_MAP[this_colour]['b']
    blinkt.set_pixel(index, pixel_value_red,
                     pixel_value_green, pixel_value_blue, this_brightness/100)

parser = argparse.ArgumentParser(description=('Update Blinkt! display using SQLite data'))
parser.add_argument('--demo', '-d', action='store_true',
                    help= 'display configured colours, one per pixel',)

args = parser.parse_args()

if args.demo:
    blinkt.clear()
    i = 0
    for colour in COLOUR_MAP:
        set_pixel(i, colour, 10)
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
    price_data_rows = cursor.fetchall()

    # finish up the database operation
    if conn:
        conn.commit()
        conn.close()

    if len(price_data_rows) < 8:
        print('Not enough data to fill the display - we will get dark pixels.')

    config = get_config()
    
    for colour, data in config['Blinkt']['Colours'].items():
        print(colour)
        for key in data:
            print(key + ':', data[key])
    blinkt.clear()

    i = 0
    for row in price_data_rows:
        slot_price = row[1]
        this_pixel_colour = price_to_colour(slot_price) # pylint: disable=I0011,C0103
        print(str(i) + ": " + str(slot_price) + "p = " + this_pixel_colour)
        set_pixel(i, this_pixel_colour, config['Blinkt']['Brightness'])
        i += 1

    print ("Setting display...")
    blinkt.set_clear_on_exit(False)
    blinkt.show()
