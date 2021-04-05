#!/usr/bin/env python3

# set Blinkt! brightness, IT BURNS MEEEEEE, 100 is the max
BRIGHTNESS = 10

# define colour values for Blinkt! LEDs. Edit as you please...
COLOUR_MAP = { 'level6': { 'r': 155, 'g': 0, 'b': 200, 'name': 'magenta' },
              'level5': { 'r': 255, 'g': 0, 'b': 0, 'name': 'red' },
              'level4': { 'r': 255, 'g': 30, 'b': 0, 'name': 'orange' },
              'level3': { 'r': 180, 'g': 100, 'b': 0, 'name': 'yellow' },
              'level2': { 'r': 0, 'g': 255, 'b': 0, 'name': 'green' },
              'level1': { 'r': 0, 'g': 160, 'b': 180, 'name': 'cyan' },
              'plunge': { 'r': 0, 'g': 0, 'b': 255, 'name': 'blue' }, }

def price_to_colour(price: float) -> str:
    """edit this function to change price thresholds - be careful that you
    don't leave gaps in the numbers or strange things will very likely happen.
    prices are including VAT in p/kWh"""

    if price > 28:
        pixel_colour = 'level6'

    elif 28 >= price > 17:
        pixel_colour = 'level5'

    elif 17 >= price > 13.5:
        pixel_colour = 'level4'

    elif 13.5 >= price > 10:
        pixel_colour = 'level3'

    elif 10 >= price > 5:
        pixel_colour = 'level2'

    elif 5 >= price > 0:
        pixel_colour = 'level1'

    elif price <= 0:
        pixel_colour = 'plunge'

    else:
        raise SystemExit("Can't continue - price of " + str(price) +" doesn't make sense.")

    return pixel_colour
