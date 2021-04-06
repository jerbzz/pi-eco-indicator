#!/usr/bin/env python3

from urllib.request import pathname2url
import sqlite3
import datetime
import time

def get_prices(count: int) -> list:
    prices = []

    try:
        # connect to the database in rw mode so we can catch the error if it doesn't exist
        DB_URI = 'file:{}?mode=rw'.format(pathname2url('agileprices.sqlite'))
        conn = sqlite3.connect(DB_URI, uri=True)
        cur = conn.cursor()
        print('Connected to database...')
    except sqlite3.OperationalError as error:
        # handle missing database case
        raise SystemExit('Database not found - you need to run store_prices.py first.') from error

    # find current time (in UTC, as stored in sqlite)
    the_now = datetime.datetime.now(datetime.timezone.utc)
    
    # create range to iterate over
    slots = [the_now + datetime.timedelta(minutes=m) for m in range(0, 30*count, 30)]

    for i, slot in enumerate(slots):
      # convert to year month day hour segment
      the_year = slot.year
      the_month = slot.month
      the_day = slot.day
      the_hour = slot.hour
      if slot.minute < 30:
        the_segment = 0
      else:
        the_segment = 1

      print("Slot", i, "at", slot.strftime("%d/%m/%Y"), "hour:", the_hour, "segment:", the_segment)

      # select from db where record == the above
      cur.execute("SELECT * FROM prices WHERE year=? AND month=? AND day=? AND hour=? AND segment=?",
          (the_year, the_month, the_day, the_hour, the_segment))

      # get price
      row = cur.fetchone()
      if row is None:
        prices.append(999) # we don't have that price yet!
      else:
        # we're getting the fifth field from a hardcoded tuple on the assumption that it's price
        # DON'T ADD ANY EXTRA FIELDS TO THAT TABLE on the sqlite db or everything will go wrong.
        print(row[5], "p/kWh")
        prices.append(row[5])

    return prices