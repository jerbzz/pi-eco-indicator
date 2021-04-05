#!/usr/bin/env python3

import blinkt
import yaml
from inky.eeprom import read_eeprom
from inky.auto import auto
from PIL import Image

try:
    config_file = open('config.yaml', 'r')
except FileNotFoundError:
    raise SystemExit('Unable to find config.yaml')

try:
    config = yaml.safe_load(config_file)
except yaml.YAMLError as err:
    raise SystemExit('Error reading configuration: ' + str(err))

if not 'DisplayType' in config:
    raise SystemExit('Error: DisplayType not found in config.yaml')

if config['DisplayType'] == 'blinkt':
    print ('Clearing Blinkt! display...')
    blinkt.clear()
    blinkt.show()
    print ('Done.')

elif config['DisplayType'] == 'inkyphat':
    inky_eeprom = read_eeprom()
    if inky_eeprom == None:
        raise SystemExit('Error: Inky pHAT display not found')

    else:
        print ('Clearing Inky pHAT display...')
        inky_display = auto(ask_user=True, verbose=True)
        colours = (inky_display.RED, inky_display.BLACK, inky_display.WHITE)
        img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))

        for c in colours:
            inky_display.set_border(c)
            for x in range(inky_display.WIDTH):
                for y in range(inky_display.HEIGHT):
                    img.putpixel((x, y), c)
            inky_display.set_image(img)
            inky_display.show()

        print ('Done.')

else:
    raise SystemExit('Error: unknown DisplayType ' + config['DisplayType'] + ' in config.yaml' )

