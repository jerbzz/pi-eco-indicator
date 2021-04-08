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

def deep_get(this_dict: dict, keys: str, default=None):
    """
    Example:
        this_dict = {'meta': {'status': 'OK', 'status_code': 200}}
        deep_get(this_dict, ['meta', 'status_code'])          # => 200
        deep_get(this_dict, ['garbage', 'status_code'])       # => None
        deep_get(this_dict, ['meta', 'garbage'], default='-') # => '-'
    """
    assert isinstance(keys, list)
    if this_dict is None:
        return default
    if not keys:
        return this_dict
    return deep_get(this_dict.get(keys[0]), keys[1:], default)

def get_config() -> dict:
    """
    Read config file and do some basic checks that we have what we need.
    If not, set sensible defaults or bail out.
    """
    try:
        config_file = open('config.yaml', 'r')
    except FileNotFoundError as no_config:
        raise SystemExit('Unable to find config.yaml') from no_config

    try:
        config = yaml.safe_load(config_file)
    except yaml.YAMLError as config_err:
        raise SystemExit('Error reading configuration: ' + str(config_err)) from config_err

    if config['DisplayType'] is None:
        raise SystemExit('Error: DisplayType not found in config.yaml')

    if config['DisplayType'] == 'blinkt':
        print ('Blinkt! display selected.')
        conf_brightness = deep_get(config, ['Blinkt', 'Brightness'])
        if not (isinstance(conf_brightness, int) and 5 <= conf_brightness <= 100):
            print('Misconfigured brightness value: ' + str(conf_brightness) +
                  '. Using default of ' + str(DEFAULT_BRIGHTNESS) + '.')
            config['Blinkt']['Brightness'] = DEFAULT_BRIGHTNESS
        if len(config['Blinkt']['Colours'].items()) < 2:
            raise SystemExit('Error: Less than two colour levels found in config.yaml')

    elif config['DisplayType'] == 'inkyphat':
        inky_eeprom = read_eeprom()

        if inky_eeprom is None:
            raise SystemExit('Error: Inky pHAT display not found')
        print ('Inky pHAT display selected.')

    else:
        raise SystemExit('Error: unknown DisplayType ' + config['DisplayType'] + ' in config.yaml' )

    return config

parser = argparse.ArgumentParser(description=('Update Blinkt! display using SQLite data'))
parser.add_argument('--demo', '-d', action='store_true',
                    help= 'display configured colours, one per pixel',)

args = parser.parse_args()

if args.demo:
    print ("Demo mode. Showing up to first 8 configured colours...")
    conf = get_config()
    print(str(len(conf['Blinkt']['Colours'].items())) + ' colour levels found in config.yaml')
    blinkt.clear()
    i = 0
    for level, data in conf['Blinkt']['Colours'].items():
        print(data)
        blinkt.set_pixel(i, data['R'], data['G'], data['B'], conf['Blinkt']['Brightness']/100)
        i += 1

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

    conf = get_config()
    blinkt.clear()
    i = 0

    for row in price_data_rows:
        slot_price = row[1]
        for level, data in conf['Blinkt']['Colours'].items():
            if slot_price >= data['Price']:
                print(str(i) + ': ' + str(slot_price) + 'p -> ' + data['Name'])
                blinkt.set_pixel(i, data['R'], data['G'], data['B'],
                                 conf['Blinkt']['Brightness']/100)
                break
        i += 1

    print ("Setting display...")
    blinkt.set_clear_on_exit(False)
    blinkt.show()
