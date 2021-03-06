#!/bin/bash

if [ "$(crontab -l | wc -c)" -eq 0 ]; then
  if [ -z "$1" ]; then
    echo "Can't install cron jobs, you must specify a region: './install_crontab.sh X'";
  else
    echo "Installing agile-blinkt-indicator cron jobs for region $1..."
    (crontab -l 2>/dev/null; echo "@reboot /bin/sleep 30; cd /home/pi/agile-blinkt-indicator && /usr/bin/python3 store_prices.py --region $1 > ./blinkt.log 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "@reboot /bin/sleep 40; cd /home/pi/agile-blinkt-indicator && /usr/bin/python3 update_blinkt.py > ./blinkt.log 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "*/30 * * * * /bin/sleep 5; cd /home/pi/agile-blinkt-indicator && /usr/bin/python3 update_blinkt.py > ./blinkt.log 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "30 16 * * * cd /home/pi/agile-blinkt-indicator && /usr/bin/python3 store_prices.py > ./blinkt.log 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "30 18 * * * cd /home/pi/agile-blinkt-indicator && /usr/bin/python3 store_prices.py > ./blinkt.log 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "30 20 * * * cd /home/pi/agile-blinkt-indicator && /usr/bin/python3 store_prices.py > ./blinkt.log 2>&1") | crontab -;
    echo "Done."
  fi
else
  echo 'crontab already exists. Please install cron jobs manually.'
fi
