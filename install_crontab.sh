#!/bin/bash

if [ "$(crontab -l | wc -c)" -eq 0 ]; then
  if [ -z "$1" ]; then
    echo "Can't install cron jobs, you must specify a region: './install_crontab.sh X'";
  else
    if [[ "$1" =~ ^(A|B|C|D|E|F|G|P|N|J|H|K|L|M)$ ]]; then
      echo "Installing agile-pi-ndicator cron jobs for region $1..."
      (crontab -l 2>/dev/null; echo "@reboot /bin/sleep 30; cd /home/pi/agile-pi-ndicator && /usr/bin/python3 store_prices.py --region $1 > ./logs/agile.log 2>&1") | crontab -
      (crontab -l 2>/dev/null; echo "@reboot /bin/sleep 40; cd /home/pi/agile-pi-ndicator && /usr/bin/python3 update.py > ./logs/agile.log 2>&1") | crontab -
      (crontab -l 2>/dev/null; echo "*/30 * * * * /bin/sleep 5; cd /home/pi/agile-pi-ndicator && /usr/bin/python3 update.py > ./logs/agile.log 2>&1") | crontab -
      (crontab -l 2>/dev/null; echo "30 16 * * * cd /home/pi/agile-pi-ndicator && /usr/bin/python3 store_prices.py --region $1 > ./logs/agile.log 2>&1") | crontab -
      (crontab -l 2>/dev/null; echo "30 18 * * * cd /home/pi/agile-pi-ndicator && /usr/bin/python3 store_prices.py --region $1 > ./logs/agile.log 2>&1") | crontab -
      (crontab -l 2>/dev/null; echo "30 20 * * * cd /home/pi/agile-pi-ndicator && /usr/bin/python3 store_prices.py --region $1 > ./logs/agile.log 2>&1") | crontab -;
      echo "Done."
    else
      echo "Can't install crontab, $1 is not a valid DNO region".
    fi
  fi
else
  echo 'crontab already exists. Please install cron jobs manually.'
fi
