#!/usr/bin/env python3

"""Recieve a parsed configuration file and price data from the database,
   as well as a flag indicating demo mode, and then update the Blinkt! 
   display appropriately."""

def update_inky(conf: dict, prices: dict, demo: bool):

    from inky.auto import auto
    from font_hanken_grotesk import HankenGroteskBold, HankenGroteskMedium
    from font_intuitive import Intuitive
    from font_fredoka_one import FredokaOne
    from PIL import Image, ImageFont, ImageDraw

    try:
        # detect display type automatically
        inky_display = auto(ask_user=False, verbose=True)
    except TypeError:
        raise TypeError("You need to update the Inky library to >= v1.1.0")

    img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
    draw = ImageDraw.Draw(img)

    if demo:
        print ("Demo mode...")

    else:

        font = ImageFont.truetype(HankenGroteskBold, 40)
        message = "{0:.1f}".format(prices[0][1]) + "p"
        w, h = font.getsize(message)
        x = (inky_display.WIDTH / 2) - (w / 2)
        y = (inky_display.HEIGHT / 2) - (h / 2)

        if (prices[0][1] > conf['InkyPHAT']['HighPrice']):
            draw.text((x, y), message, inky_display.RED, font)
            inky_display.set_border(inky_display.WHITE)
        else:
            draw.text((x, y), message, inky_display.BLACK, font)
            inky_display.set_border(inky_display.WHITE)

    inky_display.set_image(img)
    inky_display.show()