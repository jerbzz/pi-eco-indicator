#!/usr/bin/env python3

"""Read Octopus Agile price data from an existing SQLite database and update a
   Pimoroni Blinkt! display."""

import sqlite3
from urllib.request import pathname2url
import argparse
import yaml

# Blinkt! defaults
DEFAULT_BRIGHTNESS = 10

# Inky pHAT defaults
DEFAULT_HIGHPRICE = 15.0
DEFAULT_LOWSLOTDURATION = 3

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
        _config = yaml.safe_load(config_file)
    except yaml.YAMLError as config_err:
        raise SystemExit('Error reading configuration: ' + str(config_err)) from config_err

    if _config['DisplayType'] is None:
        raise SystemExit('Error: DisplayType not found in config.yaml')

    if _config['DisplayType'] == 'blinkt':
        print ('Blinkt! display selected.')
        conf_brightness = deep_get(_config, ['Blinkt', 'Brightness'])
        if not (isinstance(conf_brightness, int) and 5 <= conf_brightness <= 100):
            print('Misconfigured brightness value: ' + str(conf_brightness) +
                  '. Using default of ' + str(DEFAULT_BRIGHTNESS) + '.')
            _config['Blinkt']['Brightness'] = DEFAULT_BRIGHTNESS
        if len(_config['Blinkt']['Colours'].items()) < 2:
            raise SystemExit('Error: Less than two colour levels found in config.yaml')

    elif _config['DisplayType'] == 'inkyphat':
        print ('Inky pHAT display selected.')
        from inky.eeprom import read_eeprom # pylint: disable=C0415
        inky_eeprom = read_eeprom()
        if inky_eeprom is None:
            raise SystemExit('Error: Inky pHAT display not found')

        conf_highprice = deep_get(_config, ['InkyPHAT', 'HighPrice'])
        if not (isinstance(conf_highprice, (int, float)) and 0 <= conf_highprice <= 35):
            print('Misconfigured high price value: ' + str(conf_highprice) +
                  '. Using default of ' + str(DEFAULT_HIGHPRICE) + '.')
            _config['InkyPHAT']['HighPrice'] = DEFAULT_HIGHPRICE

        conf_lowslotduration = deep_get(_config, ['InkyPHAT', 'LowSlotDuration'])
        if not (conf_lowslotduration % 0.5 == 0 and 0.5 <= conf_lowslotduration <= 6):
            print('Low slot duration misconfigured: ' + str(conf_lowslotduration) +
                  ' (must be between 0.5 and 6 hours in half hour increments).' + 
                  ' Using default of ' + str(DEFAULT_LOWSLOTDURATION) + '.')
            _config['InkyPHAT']['LowSlotDuration'] = DEFAULT_LOWSLOTDURATION
    else:
        raise SystemExit('Error: unknown DisplayType ' + config['DisplayType'] + ' in config.yaml' )

    return _config

parser = argparse.ArgumentParser(description=('Update Blinkt! display using SQLite data'))
parser.add_argument('--demo', '-d', action='store_true',
                    help= 'display configured colours, one per pixel',)

args = parser.parse_args()


try:
    # connect to the database in rw mode so we can catch the error if it doesn't exist
    DB_URI = 'file:{}?mode=rw'.format(pathname2url('agileprices.sqlite'))
    conn = sqlite3.connect(DB_URI, uri=True)
    cursor = conn.cursor()
    print('Connected to database...')

except sqlite3.OperationalError as error:
    # handle missing database case
    raise SystemExit('Database not found - you need to run store_prices.py first.') from error

cursor.execute("SELECT * FROM prices WHERE valid_from > datetime('now', '-30 minutes')")
price_data_rows = cursor.fetchall()

# finish up the database operation
if conn:
    conn.commit()
    conn.close()

config = get_config()

if config['DisplayType'] == 'blinkt':
    import blinkt_display
    blinkt_display.update_blinkt(config, price_data_rows, args.demo)

if config['DisplayType'] == 'inkyphat':
    import inkyphat_display
    inkyphat_display.update_inky(config, price_data_rows, args.demo)
