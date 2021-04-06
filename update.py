#!/usr/bin/env python3

"""Read Octopus Agile price data from an existing SQLite database and update a
   Pimoroni Blinkt! or Inky pHAT display if connected."""

from inky.eeprom import read_eeprom
from blinkt_updater import update_blinkt
from inky_updater import update_inky

find_inky = read_eeprom()

if find_inky is None:
    print("No Inky found, trying Blinkt!")
    update_blinkt()
else:
    print("Trying Inky")
    update_inky()
