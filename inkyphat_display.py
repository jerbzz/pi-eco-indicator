#!/usr/bin/env python3

"""Recieve a parsed configuration file and price data from the database,
   as well as a flag indicating demo mode, and then update the Blinkt! 
   display appropriately."""

def update_inky(conf: dict, prices: dict, demo: bool):

    import math
    from datetime import datetime, timedelta
    import pytz
    from tzlocal import get_localzone
    from inky.auto import auto
    from PIL import Image, ImageFont, ImageDraw
    from font_roboto import Roboto, RobotoMedium, RobotoBlack

    local_tz = get_localzone()

    try:
        # detect display type automatically
        inky_display = auto(ask_user=False, verbose=True)
    except TypeError:
        raise TypeError("You need to update the Inky library to >= v1.1.0")

    img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
    draw = ImageDraw.Draw(img)
    
    # deal with scaling for newer SSD1608 pHATs
    if inky_display.resolution == (250, 122):
        graph_x_unit = 2.5
        graph_y_unit = 4
        font_scale_factor = 1.2
        x_padding_factor = 1.18
        y_padding_factor = 1.20

    # original Inky pHAT
    if inky_display.resolution == (212, 104):
        graph_x_unit = 2
        graph_y_unit = 3
        font_scale_factor = 1
        x_padding_factor = 1
        y_padding_factor = 1

    if demo:
        print ("Demo mode...")

    else:
        min_slot = min(prices, key = lambda prices: prices[1])

        # draw graph...
        # shift axis for negative prices
        if (min_slot[1] < 0):
            graph_bottom = inky_display.HEIGHT + abs(min_slot[1]) * graph_x_unit
        else:
            graph_bottom = inky_display.HEIGHT

        i = 0
        for slot, price in prices:
            # highlight the lowest prices

            if price - min_slot[1] <= conf['InkyPHAT']['LowSlotDelta']:
                colour = inky_display.BLACK
            else:
                colour = inky_display.RED

            bar_x_height = price * graph_x_unit
            draw.rectangle((i * graph_y_unit, graph_bottom, ((i * graph_y_unit) - graph_y_unit), (graph_bottom - bar_x_height)), colour)
            i += 1

        # draw current price, in colour if it's high
        # also highlight with a coloured border if current price is high
        font = ImageFont.truetype(RobotoBlack, size = int(45 * font_scale_factor))
        message = "{0:.1f}".format(prices[0][1]) + "p"
        x = 0 * x_padding_factor
        y = 12 * y_padding_factor

        if (prices[0][1] > conf['InkyPHAT']['HighPrice']):
            draw.text((x, y), message, inky_display.RED, font)
            inky_display.set_border(inky_display.RED)
        else:
            draw.text((x, y), message, inky_display.BLACK, font)
            inky_display.set_border(inky_display.WHITE)

        # draw time info above current price
        font = ImageFont.truetype(RobotoMedium, size = int(15 * font_scale_factor))
        slot_start = str(datetime.strftime(pytz.utc.localize(datetime.strptime(prices[0][0], 
            "%Y-%m-%d %H:%M:%S"), is_dst=None).astimezone(local_tz), "%H:%M"))
        message = "Price at " + slot_start + "    " # trailing spaces prevent text clipping
        x = 4 * x_padding_factor
        y = 0 * y_padding_factor
        draw.text((x, y), message, inky_display.BLACK, font)

        # draw next 3 slot times
        font = ImageFont.truetype(RobotoMedium, size = int(15 * font_scale_factor))
        x = 130 * x_padding_factor
        for i in range(3): 
            message = "+" + str(30 * (i + 1)) + ":    " # trailing spaces prevent text clipping
            y = i * 18 * y_padding_factor + 3 * y_padding_factor
            draw.text((x, y), message, inky_display.BLACK, font)
        
        # draw next 3 slot prices
        x = 163 * x_padding_factor
        for i in range(3):
            message = "{0:.1f}".format(prices[i+1][1]) + "p    " # trailing spaces prevent text clipping
            y = i * 18 * y_padding_factor + 3 * y_padding_factor
            if (prices[i+1][1] > conf['InkyPHAT']['HighPrice']):
                draw.text((x, y), message, inky_display.RED, font)
            else:
                draw.text((x, y), message, inky_display.BLACK, font)

        # draw separator line
        ypos = 5 * y_padding_factor + (3 * 18 * y_padding_factor)
        draw.line((130 * x_padding_factor, ypos, inky_display.WIDTH - 5, ypos), fill=inky_display.BLACK, width=2)

        # draw lowest slot info

        x = 130 * x_padding_factor
        y = 10 * y_padding_factor + (3 * 18 * y_padding_factor)
        min_slot_price = "{0:.1f}".format(min_slot[1])
        draw.text((x, y), "Low: " + min_slot_price + "p    ", inky_display.BLACK, font)

        font = ImageFont.truetype(RobotoMedium, size = int(13 * font_scale_factor))
        y = 16 * (y_padding_factor * 0.6) + (4 * 18 * y_padding_factor)
        min_slot_time = str(datetime.strftime(pytz.utc.localize(datetime.strptime(
                        min_slot[0], "%Y-%m-%d %H:%M:%S"), is_dst=None).astimezone(local_tz), 
                        "%H:%M"))
        min_slot_timedelta = datetime.strptime(min_slot[0], "%Y-%m-%d %H:%M:%S") - datetime.strptime(prices[0][0], "%Y-%m-%d %H:%M:%S")
        draw.text((x, y), min_slot_time + "/" + str(min_slot_timedelta.total_seconds() / 3600) + "h    ", inky_display.BLACK, font)

    inky_display.set_image(img)
    inky_display.show()