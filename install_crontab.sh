#!/bin/bash

if [ "$(crontab -l | wc -c)" -eq 0 ]; then
      echo "Installing agile-blinkt-indicator cron jobs..."
      (crontab -l 2>/dev/null; echo "@reboot /bin/sleep 30; cd /home/pi/agile-blinkt-indicator && /usr/bin/python3 store_prices.py > ./agile_indicator.log 2>&1") | crontab -
      (crontab -l 2>/dev/null; echo "@reboot /bin/sleep 40; cd /home/pi/agile-blinkt-indicator && /usr/bin/python3 update_display.py > ./agile_indicator.log 2>&1") | crontab -
      (crontab -l 2>/dev/null; echo "*/30 * * * * /bin/sleep 5; cd /home/pi/agile-blinkt-indicator && /usr/bin/python3 update_display.py > ./agile_indicator.log 2>&1") | crontab -
      (crontab -l 2>/dev/null; echo "30 16 * * * cd /home/pi/agile-blinkt-indicator && /usr/bin/python3 store_prices.py > ./agile_indicator.log 2>&1") | crontab -
      (crontab -l 2>/dev/null; echo "30 18 * * * cd /home/pi/agile-blinkt-indicator && /usr/bin/python3 store_prices.py > ./agile_indicator.log 2>&1") | crontab -
      (crontab -l 2>/dev/null; echo "30 20 * * * cd /home/pi/agile-blinkt-indicator && /usr/bin/python3 store_prices.py > ./agile_indicator.log 2>&1") | crontab -;
      echo "Done."
else
      echo 'crontab already exists. Please install cron jobs manually.'
fi
