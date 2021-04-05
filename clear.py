#!/usr/bin/env python3

"""
MIT License
Copyright (c) 2018 Pimoroni Ltd.
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import argparse
import time
import blinkt
from inky.eeprom import read_eeprom
from inky.auto import auto
from PIL import Image

find_inky = read_eeprom()

if find_inky is None:
    print("Clearing any Blinkt! display present")
    blinkt.clear()
    blinkt.show()
else:
    print("""Inky pHAT: Clean
    Displays solid blocks of black, white, and the third colour to clean the Inky pHAT
    display of any ghosting.
    """)

    inky_display = auto(ask_user=True, verbose=True)

    # Command line arguments to determine number of cycles to run
    parser = argparse.ArgumentParser()
    parser.add_argument('--number', '-n', type=int, required=False, help="number of cycles")
    args = parser.parse_args()

    # The number of red / black / white refreshes to run

    if args.number:
        cycles = args.number
    else:
        cycles = 3

    colours = (inky_display.RED, inky_display.BLACK, inky_display.WHITE)
    colour_names = (inky_display.colour, "black", "white")

    # Create a new canvas to draw on

    img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))

    # Loop through the specified number of cycles and completely
    # fill the display with each colour in turn.

    for i in range(cycles):
        print("Inky cleaning cycle %i\n" % (i + 1))
        for j, c in enumerate(colours):
            print("- updating with %s" % colour_names[j])
            inky_display.set_border(c)
            for x in range(inky_display.WIDTH):
                for y in range(inky_display.HEIGHT):
                    img.putpixel((x, y), c)
            inky_display.set_image(img)
            inky_display.show()
            time.sleep(1)
        print("\n")

    print("Inky cleaning complete!")


