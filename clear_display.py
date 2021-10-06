#!/usr/bin/env python3
# pylint: disable=invalid-name

"""Determine what type of display is connected and
   use the appropriate method to clear it."""

import yaml
import eco_indicator
import argparse

parser = argparse.ArgumentParser(description=('Clear the attached display'))
parser.add_argument('--conf', '-c', default='config.yaml', help='specify config file')

args = parser.parse_args()
conf_file = args.conf

config = eco_indicator.get_config(conf_file)

if "DisplayType" not in config:
    raise SystemExit("Error: DisplayType not found in " + conf_file)

if config['DisplayType'] == "blinkt":
    import blinkt
    print("Clearing Blinkt! display...")
    blinkt.clear()
    blinkt.show()
    print("Done.")

elif config['DisplayType'] == "inkyphat":
    from inky.eeprom import read_eeprom
    from inky.auto import auto
    from PIL import Image
    inky_eeprom = read_eeprom()
    if inky_eeprom is None:
        raise SystemExit("Error: Inky pHAT display not found")

    print("Clearing Inky pHAT display...")
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

    print("Done.")

else:
    raise SystemExit("Error: unknown DisplayType " + config['DisplayType'] + " in " + conf_file)
