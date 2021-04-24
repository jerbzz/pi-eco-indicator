#!/usr/bin/env python3

"""Recieve a parsed configuration file and price data from the database,
   as well as a flag indicating demo mode, and then update the Blinkt!
   display appropriately.
   
   Notes: list 'prices' as passed from update_display.py is an ordered
   list of tuples. In each tuple, index [0] is the time in SQLite date
   format and index [1] is the price in p/kWh as a float."""

from datetime import datetime, timedelta
import pytz
from tzlocal import get_localzone
from inky.auto import auto
from PIL import Image, ImageFont, ImageDraw
from font_roboto import RobotoMedium, RobotoBlack

def update_inky(conf: dict, prices: dict, demo: bool):
# pylint: disable=C0116
    local_tz = get_localzone()

    try:
        # detect display type automatically
        inky_display = auto(ask_user=False, verbose=True)
    except TypeError as inky_version:
        raise TypeError("You need to update the Inky library to >= v1.1.0") from inky_version

    img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
    draw = ImageDraw.Draw(img)

    # deal with scaling for newer SSD1608 pHATs
    if inky_display.resolution == (250, 122):
        graph_y_unit = 2.3
        graph_x_unit = 4 # needs to be int to avoid aliasing
        font_scale_factor = 1.2
        x_padding_factor = 1.2
        y_padding_factor = 1.2

    # original Inky pHAT
    if inky_display.resolution == (212, 104):
        graph_y_unit = 2
        graph_x_unit = 3 # needs to be int to avoid aliasing
        font_scale_factor = 1
        x_padding_factor = 1
        y_padding_factor = 1

    if demo:
        print ("Demo mode...")

    else:
        # figure out cheapest slots
        low_slot_duration = conf['InkyPHAT']['LowSlotDuration']
        num_low_slots = int(2 * low_slot_duration)
        prices_only = [price[1] for price in prices]
        low_slots_list = []
        for i in range(0, len(prices_only) - num_low_slots - 1):
            low_slots_list.append(sum(prices_only[i:i+num_low_slots])/num_low_slots)
        low_slots_start_idx = low_slots_list.index(min(low_slots_list))
        low_slots_average = "{0:.1f}".format(min(low_slots_list))

        low_slots_start_time = str(datetime.strftime(pytz.utc.localize(
                              datetime.strptime(prices[low_slots_start_idx][0], 
                              "%Y-%m-%d %H:%M:%S"), 
                              is_dst=None).astimezone(local_tz), "%H:%M"))
        print("Cheapest " + str(low_slot_duration) + " hours: average " + 
              low_slots_average + "p/kWh at " + low_slots_start_time + ".")
        
        min_slot = min(prices, key = lambda prices: prices[1])

        # figure out the cheapest slot

        # draw graph solid bars...
        # shift axis for negative prices
        if min_slot[1] < 0:
            graph_bottom = (inky_display.HEIGHT + min_slot[1] * graph_y_unit) - 13 * y_padding_factor
        else:
            graph_bottom = inky_display.HEIGHT - 13 * y_padding_factor

        i = 0
        for price in prices:
            # draw the lowest slots in black and the highest in red/yellow

            if (i + 1) * graph_x_unit > 128 * x_padding_factor:
                break # don't scribble on the small text
                
            if low_slots_start_idx <= i < low_slots_start_idx + num_low_slots:
                colour = inky_display.BLACK
            elif price[1] > conf['InkyPHAT']['HighPrice']:
                colour = inky_display.RED
            else:
                colour = inky_display.WHITE

            bar_y_height = price[1] * graph_y_unit

            draw.rectangle(((i + 1) * graph_x_unit, graph_bottom,
                          (((i + 1) * graph_x_unit) - graph_x_unit),
                          (graph_bottom - bar_y_height)), colour)
            i += 1
        # graph solid bars finished

        # draw current price, in colour if it's high...
        # also highlight display with a coloured border if current price is high
        font = ImageFont.truetype(RobotoBlack, size = int(45 * font_scale_factor))
        message = "{0:.1f}".format(prices[0][1]) + "p"
        x = 0 * x_padding_factor
        y = 8 * y_padding_factor

        if prices[0][1] > conf['InkyPHAT']['HighPrice']:
            draw.text((x, y), message, inky_display.RED, font)
            inky_display.set_border(inky_display.RED)
        else:
            draw.text((x, y), message, inky_display.BLACK, font)
            inky_display.set_border(inky_display.WHITE)

        # draw time info above current price...
        font = ImageFont.truetype(RobotoMedium, size = int(15 * font_scale_factor))
        slot_start = str(datetime.strftime(pytz.utc.localize(datetime.strptime(prices[0][0],
            "%Y-%m-%d %H:%M:%S"), is_dst=None).astimezone(local_tz), "%H:%M"))
        message = "Price at " + slot_start + "    " # trailing spaces prevent text clipping
        x = 4 * x_padding_factor
        y = 0 * y_padding_factor
        draw.text((x, y), message, inky_display.BLACK, font)

        # draw next 3 slot times...
        font = ImageFont.truetype(RobotoMedium, size = int(15 * font_scale_factor))
        x = 130 * x_padding_factor
        for i in range(3):
            message = "+" + str(30 * (i + 1)) + ":    " # trailing spaces prevent text clipping
            y = i * 18 * y_padding_factor + 3 * y_padding_factor
            draw.text((x, y), message, inky_display.BLACK, font)

        # draw next 3 slot prices...
        x = 163 * x_padding_factor
        for i in range(3):
            message = "{0:.1f}".format(prices[i+1][1]) + "p    "
            # trailing spaces prevent text clipping
            y = i * 18 * y_padding_factor + 3 * y_padding_factor
            if prices[i+1][1] > conf['InkyPHAT']['HighPrice']:
                draw.text((x, y), message, inky_display.RED, font)
            else:
                draw.text((x, y), message, inky_display.BLACK, font)

        # draw separator line...
        ypos = 5 * y_padding_factor + (3 * 18 * y_padding_factor)
        draw.line((130 * x_padding_factor, ypos, inky_display.WIDTH - 5, ypos),
                   fill=inky_display.BLACK, width=2)

        # draw lowest slots info...
        x = 130 * x_padding_factor
        y = 10 * y_padding_factor + (3 * 18 * y_padding_factor)
        font = ImageFont.truetype(RobotoMedium, size = int(13 * font_scale_factor))
        
        if '.' in str(low_slot_duration): 
            lsd_text = str(low_slot_duration).rstrip('0').rstrip('.')
        else:
            lsd_text = str(low_slot_duration)
        
        draw.text((x, y), lsd_text + "h @" + low_slots_average + "p    ", inky_display.BLACK, font)
        
        y = 16 * (y_padding_factor * 0.6) + (4 * 18 * y_padding_factor)

        min_slot_timedelta = datetime.strptime(prices[low_slots_start_idx][0], 
                              "%Y-%m-%d %H:%M:%S") - datetime.strptime(
                             prices[0][0], "%Y-%m-%d %H:%M:%S")
        draw.text((x, y), low_slots_start_time + "/" + str(min_slot_timedelta.total_seconds() / 3600) +
                   "h    ", inky_display.BLACK, font)

        # draw graph outline (last so it's over the top of everything else)
        i = 0
        for i, price in enumerate(prices):
            colour = inky_display.BLACK
            bar_y_height = price[1] * graph_y_unit
            prev_bar_y_height = prices[i-1][1] * graph_y_unit

            if (i + 1) * graph_x_unit > 128 * x_padding_factor: # don't scribble on the small text
                break

            # horizontal lines...
            draw.line(((i + 1) * graph_x_unit, graph_bottom - bar_y_height,
                     ((i + 1) * graph_x_unit) - graph_x_unit, 
                     graph_bottom - bar_y_height), colour)

            # vertical lines...
            if i == 0: # skip the first vertical line
                continue 
            draw.line((i * graph_x_unit, graph_bottom - bar_y_height, 
                     i * graph_x_unit, graph_bottom - prev_bar_y_height), colour)

            i += 1

        # draw graph x axis
        draw.line((0, graph_bottom, 126 * x_padding_factor, graph_bottom), inky_display.BLACK)

        # draw graph hour marker text...
        for i in range(2, 24, 3):
            colour = inky_display.BLACK
            font = ImageFont.truetype(RobotoMedium, size = int(10 * font_scale_factor))
            x = (i - 0.5) * graph_x_unit * 2 # it's half hour slots!!
            hours = datetime.strftime(datetime.now() + timedelta(hours=i),"%H")
            hours_w, hours_h = font.getsize(hours) # we want to centre the labels
            y = graph_bottom + 1
            if x + hours_w / 2 > 128 * x_padding_factor:
                break # don't draw past the end of the x axis
            draw.text((x - hours_w / 2, y + 1), hours + "  ", inky_display.BLACK, font)
            # and the tick marks for each one            
            draw.line((x, y + 2 * y_padding_factor, x, graph_bottom), inky_display.BLACK)

        # draw average line...
        # extract just prices from the list of tuples and put in descending order        
        price_list = sorted(list(zip(*prices))[1], reverse=True)
        # now slice off the first (highest) 6 entries
        del price_list[:6]
        # and calculate the mean
        average_price = sum(price_list) / len(price_list)

        average_line_ypos = graph_bottom - average_price * graph_y_unit

        for x in range (0, int(126 * x_padding_factor)):
            if x % 6 == 2: # repeat every 6 pixels starting at 2
                draw.line((x, average_line_ypos, x + 2, average_line_ypos), inky_display.BLACK)

    inky_display.set_image(img)
    inky_display.show()
