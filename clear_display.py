#!/usr/bin/env python3
# pylint: disable=invalid-name

"""Determine what type of display is connected and
   use the appropriate method to clear it."""

import eco_indicator
import argparse

parser = argparse.ArgumentParser(description=('Clear the attached display'))
parser.add_argument('--conf', '-c', default='config.yaml', help='specify config file')

args = parser.parse_args()
conf_file = args.conf

config = eco_indicator.get_config(conf_file)

eco_indicator.clear_display(config)
