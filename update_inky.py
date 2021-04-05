#!/usr/bin/env python3

from inky.auto import auto
#from font_hanken_grotesk import HankenGroteskBold, HankenGroteskMedium  # should you choose to switch to gross fonts
#from font_intuitive import Intuitive
from font_fredoka_one import FredokaOne  # this is the font we're currently using
from PIL import Image, ImageFont, ImageDraw

from read_prices import get_prices
import datetime
import pytz
import time

def convert_offset_to_time_string(offset: int) -> str:
  now = datetime.datetime.utcnow()
  now_segment_starts = now - (now - datetime.datetime.min) % datetime.timedelta(minutes=30)
  cheapest = now_segment_starts + datetime.timedelta(minutes=offset)
  cheapest_local = pytz.timezone("Europe/London").fromutc(cheapest)
  print("cheapest at " + str(cheapest_local))
  print("which is: " + cheapest_local.strftime("%H.%M"))
  cheapest_formatted = "at " + cheapest_local.strftime("%H.%M")
  return cheapest_formatted

def update_inky():
  try:
    # detect display type automatically
    inky_display = auto(ask_user=False, verbose=True)
  except TypeError:
    raise TypeError("You need to update the Inky library to >= v1.1.0")

  prices = get_prices(48)

  inky_display.set_border(inky_display.WHITE)
  img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
  draw = ImageDraw.Draw(img)

  current_price = prices[0]
  next_price = prices[1]
  nextp1_price = prices[2]
  nextp2_price = prices[3]

  if (inky_display.WIDTH == 212): #low res display
    font = ImageFont.truetype(FredokaOne, 60)
    message = "{0:.1f}".format(current_price) + "p"
    w, h = font.getsize(message)
    #x = (inky_display.WIDTH / 2) - (w / 2)
    #y = (inky_display.HEIGHT / 2) - (h / 2)
    x = 0
    y = -5

    if (current_price > 14.8):
      draw.text((x, y), message, inky_display.RED, font)
    else:
      draw.text((x, y), message, inky_display.BLACK, font)

    right_column = 145

    # NEXT
    message = "2:" + "{0:.1f}".format(next_price) + "p"
    font = ImageFont.truetype(FredokaOne, 20)
    w2, h2 = font.getsize(message)
    x = right_column
    y = 0
    if (next_price > 14.8):
      draw.text((x,y), message, inky_display.RED, font)
    else:
      draw.text((x, y), message, inky_display.BLACK, font)

    # NEXT
    message = "3:" + "{0:.1f}".format(nextp1_price) + "p"
    font = ImageFont.truetype(FredokaOne, 20)
    w3, h3 = font.getsize(message)
    x = right_column
    y = 20

    if (nextp1_price > 14.8):
      draw.text((x,y), message, inky_display.RED, font)
    else:
      draw.text((x, y), message, inky_display.BLACK, font)

    # NEXT
    message = "4:" + "{0:.1f}".format(nextp2_price) + "p"
    font = ImageFont.truetype(FredokaOne, 20)
    w3, h3 = font.getsize(message)
    x = right_column
    y = 40

    if (nextp2_price > 14.8):
      draw.text((x,y), message, inky_display.RED, font)
    else:
      draw.text((x, y), message, inky_display.BLACK, font)

    pixels_per_h = 2  # how many pixels 1p is worth
    pixels_per_w = 3  # how many pixels 1/2 hour is worth
    chart_base_loc = 104  # location of the bottom of the chart on screen in pixels
    #chart_base_loc = 85  # location of the bottom of the chart on screen in pixels
    number_of_vals_to_display = 48 # 36 half hours = 18 hours

    # plot the graph
    #lowest_price_next_24h = min(i for i in prices if i > 0)
    lowest_price_next_24h = min(i for i in prices)
    if (lowest_price_next_24h < 0):
      chart_base_loc = 104 + lowest_price_next_24h*pixels_per_h - 2 # if we have any negative prices, shift the base of the graph up! 

    print("lowest price Position:", prices.index(lowest_price_next_24h))
    print("low Value:", lowest_price_next_24h)

    # go through each hour and get the value

    for i in range(0,number_of_vals_to_display):
      if prices[i] < 999:
        scaled_price = prices[i] * pixels_per_h # we're scaling it by the value above

        if prices[i] <= (lowest_price_next_24h + 1):   # if within 1p of the lowest price, display in black
          ink_color = inky_display.BLACK
        else:
          ink_color = inky_display.RED

        # takes a bit of thought this next bit, draw a rectangle from say x =  2i to 2(i-1) for each plot value
        # pixels_per_w defines the horizontal scaling factor (2 seems to work)
        draw.rectangle((pixels_per_w*i,chart_base_loc,((pixels_per_w*i)-pixels_per_w),(chart_base_loc-scaled_price)),ink_color)

    # draw minimum value on chart  <- this doesn't seem to work yet
    # font = ImageFont.truetype(FredokaOne, 15)
    # msg = "{0:.1f}".format(lowest_price_next_24h) + "p"
    # draw.text((4*(minterval-1),110),msg, inky_display.BLACK, font)

    # draw the bottom right min price and how many hours that is away
    font = ImageFont.truetype(FredokaOne, 15)
    msg = "min:"+"{0:.1f}".format(lowest_price_next_24h) + "p"
    draw.text((right_column,60), msg, inky_display.BLACK, font)
    
    # we know how many half hours to min price, now figure it out in hours.
    minterval = (round(prices.index(lowest_price_next_24h)/2))
    print ("minterval:"+str(minterval))
    msg = "in:"+str(minterval)+"hrs"
    draw.text((right_column,75), msg, inky_display.BLACK, font)

    # convert that to an actual time, accounting for BST as required
    min_offset = prices.index(lowest_price_next_24h) * 30
    time_of_cheapest_formatted = convert_offset_to_time_string(min_offset)
    font = ImageFont.truetype(FredokaOne, 15)
    draw.text((right_column,90), time_of_cheapest_formatted, inky_display.BLACK, font)

  else: #high res display

    font = ImageFont.truetype(FredokaOne, 72)
    message = "{0:.1f}".format(current_price) + "p"
    w, h = font.getsize(message)
    #x = (inky_display.WIDTH / 2) - (w / 2)
    #y = (inky_display.HEIGHT / 2) - (h / 2)
    x = 0
    y = -10

    if (current_price > 14.8):
      draw.text((x, y), message, inky_display.RED, font)
    else:
      draw.text((x, y), message, inky_display.BLACK, font)

    right_column = 172

    # NEXT
    message = "2:" + "{0:.1f}".format(next_price) + "p"
    font = ImageFont.truetype(FredokaOne, 23)
    w2, h2 = font.getsize(message)
    x = right_column
    y = 0
    if (next_price > 14.8):
      draw.text((x,y), message, inky_display.RED, font)
    else:
      draw.text((x, y), message, inky_display.BLACK, font)

    # NEXT
    message = "3:" + "{0:.1f}".format(nextp1_price) + "p"
    font = ImageFont.truetype(FredokaOne, 23)
    w3, h3 = font.getsize(message)
    x = right_column
    y = 23

    if (nextp1_price > 14.8):
      draw.text((x,y), message, inky_display.RED, font)
    else:
      draw.text((x, y), message, inky_display.BLACK, font)

    # NEXT
    message = "4:" + "{0:.1f}".format(nextp2_price) + "p"
    font = ImageFont.truetype(FredokaOne, 23)
    w3, h3 = font.getsize(message)
    x = right_column
    y = 46

    if (nextp2_price > 14.8):
      draw.text((x,y), message, inky_display.RED, font)
    else:
      draw.text((x, y), message, inky_display.BLACK, font)

    pixels_per_h = 2.3  # how many pixels 1p is worth
    pixels_per_w = 3.5  # how many pixels 1/2 hour is worth
    chart_base_loc = 121  # location of the bottom of the chart on screen in pixels
    #chart_base_loc = 85  # location of the bottom of the chart on screen in pixels
    number_of_vals_to_display = 48 # 36 half hours = 18 hours

    # plot the graph
    #lowest_price_next_24h = min(i for i in prices if i > 0)
    lowest_price_next_24h = min(i for i in prices)
    if (lowest_price_next_24h < 0):
      chart_base_loc = 104 + lowest_price_next_24h*pixels_per_h - 2 # if we have any negative prices, shift the base of the graph up! 

    print("lowest price Position:", prices.index(lowest_price_next_24h))
    print("low Value:", lowest_price_next_24h)

    # go through each hour and get the value

    for i in range(0,number_of_vals_to_display):
      if prices[i] < 999:
        scaled_price = prices[i] * pixels_per_h # we're scaling it by the value above

        if prices[i] <= (lowest_price_next_24h + 1):   # if within 1p of the lowest price, display in black
          ink_color = inky_display.BLACK
        else:
          ink_color = inky_display.RED

        # takes a bit of thought this next bit, draw a rectangle from say x =  2i to 2(i-1) for each plot value
        # pixels_per_w defines the horizontal scaling factor (2 seems to work)
        draw.rectangle((pixels_per_w*i,chart_base_loc,((pixels_per_w*i)-pixels_per_w),(chart_base_loc-scaled_price)),ink_color)

    # draw minimum value on chart  <- this doesn't seem to work yet
    # font = ImageFont.truetype(FredokaOne, 15)
    # msg = "{0:.1f}".format(lowest_price_next_24h) + "p"
    # draw.text((4*(minterval-1),110),msg, inky_display.BLACK, font)

    # draw the bottom right min price and how many hours that is away
    font = ImageFont.truetype(FredokaOne, 16)
    msg = "min:"+"{0:.1f}".format(lowest_price_next_24h) + "p"
    draw.text((right_column,69), msg, inky_display.BLACK, font)
    # we know how many half hours to min price, now figure it out in hours.
    minterval = (round(prices.index(lowest_price_next_24h)/2))
    print ("minterval:"+str(minterval))
    msg = "in:"+str(minterval)+"hrs"
    draw.text((right_column,85), msg, inky_display.BLACK, font)

    # convert that to an actual time, accounting for BST as required
    min_offset = prices.index(lowest_price_next_24h) * 30
    time_of_cheapest_formatted = convert_offset_to_time_string(min_offset)
    font = ImageFont.truetype(FredokaOne, 16)
    draw.text((right_column,101), time_of_cheapest_formatted, inky_display.BLACK, font)

  # render the actual image onto the display
  inky_display.set_image(img)
  inky_display.show()
