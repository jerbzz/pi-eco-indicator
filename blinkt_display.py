#!/usr/bin/env python3

"""Recieve a parsed configuration file and price data from the database,
   as well as a flag indicating demo mode, and then update the Blinkt!
   display appropriately."""

import blinkt

def update_blinkt(conf: dict, prices: dict, demo: bool):
# pylint: disable=C0116
    if demo:
        print ("Demo mode. Showing up to first 8 configured colours...")
        print(str(len(conf['Blinkt']['Colours'].items())) + ' colour levels found in config.yaml')
        blinkt.clear()
        i = 0
        for level, data in conf['Blinkt']['Colours'].items():
            print(level, data)
            blinkt.set_pixel(i, data['R'], data['G'], data['B'], conf['Blinkt']['Brightness']/100)
            i += 1

        blinkt.set_clear_on_exit(False)
        blinkt.show()

    else:
        blinkt.clear()
        i = 0

        if len(prices) < 8:
            print('Not enough data to fill the display - we will get dark pixels.')

        for row in prices:
            slot_price = row[1]
            for level, data in conf['Blinkt']['Colours'].items():
                if slot_price >= data['Price']:
                    print(str(i) + ': ' + str(slot_price) + 'p -> ' + data['Name'])
                    blinkt.set_pixel(i, data['R'], data['G'], data['B'],
                                     conf['Blinkt']['Brightness']/100)
                    break
            i += 1
            if i == 7:
                break

        print ("Setting display...")
        blinkt.set_clear_on_exit(False)
        blinkt.show()
