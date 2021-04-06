#!/usr/bin/env python3

"""Read Octopus Agile price data from an existing SQLite database and update a
   Pimoroni Blinkt! or Inky pHAT display."""

import argparse
import blinkt
import blinkt_config as cfg
from read_prices import get_prices

def set_pixel(index: int, this_colour: str):
    """This function looks up the R, G, and B values for a given colour
    in the 'COLOUR_MAP' dictionary and passes them to the blinkt! set_pixel method."""

    pixel_value_red = cfg.COLOUR_MAP[this_colour]['r']
    pixel_value_green = cfg.COLOUR_MAP[this_colour]['g']
    pixel_value_blue = cfg.COLOUR_MAP[this_colour]['b']
    blinkt.set_pixel(index, pixel_value_red,
                     pixel_value_green, pixel_value_blue, cfg.BRIGHTNESS/100)

def update_blinkt():
    parser = argparse.ArgumentParser(description=('Update Blinkt! display using SQLite data'))
    parser.add_argument('--demo', '-d', action='store_true',
                        help= 'display configured Blinkt! colours, one per pixel',)

    args = parser.parse_args()

    if args.demo:
        blinkt.clear()
        i = 0
        for colour in cfg.COLOUR_MAP:
            set_pixel(i, colour)
            i += 1
        print ("Blinkt! in demo mode. Run again without --demo to update with SQLite data.")
        blinkt.set_clear_on_exit(False)
        blinkt.show()

    else:
        prices = get_prices(8)
        blinkt.clear()

        i = 0
        for price in prices:
            this_pixel_colour = cfg.price_to_colour(price) # pylint: disable=I0011,C0103
            print(str(i) + ": " + str(price) + "p = " + cfg.COLOUR_MAP[this_pixel_colour]['name'] + " (" + this_pixel_colour + ")")
            set_pixel(i, this_pixel_colour)
            i += 1

        print ("Setting Blinkt! display...")
        blinkt.set_clear_on_exit(False)
        blinkt.show()
