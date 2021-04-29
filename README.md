# octopus-agile-indicator
Display upcoming Octopus Agile prices on the Pimoroni Blinkt! display or the Pimoroni Inky pHAT display for Raspberry Pi, with no external dependencies - prices are fetched directly from Octopus's public API and stored locally. Designed to be simple to set up and use for people with no coding knowledge. Other displays will be supported in the future.

Should you wish to purchase a preconfigured device, I have an [Etsy shop here](https://www.etsy.com/uk/listing/968401316/octopus-energy-agile-tariff-price).

![Display in action](https://raw.githubusercontent.com/jerbzz/agile-blinkt-indicator/main/images/DSC_5094.jpg)

Read it from left to right. Each pixel represents a half hour slot, so you get 3.5 to 4 hours of data depending on when you look at it! The leftmost pixel represents the current price. On the half hour, every half hour, everything shifts one pixel to the left.

Magenta is the most expensive, then red if it's under 28p, orange if it's under 17p, yellow if it's under 13.5p, green if it's under 10p, cyan if it's under 5p, and blue if it's a plunge. You can change these quite easily by editing the code.

# Hardware needed

- Pimoroni Blinkt!, https://shop.pimoroni.com/products/blinkt, or a
- Pimoroni Inky pHAT, https://shop.pimoroni.com/products/inky-phat
- A Raspberry Pi of any flavour, as long as you can connect the display to it, and it can connect to the internet. This software has been tested on a Pi Zero W and a Pi 3B+.

# Software needed

- This has been tested on Raspberry Pi OS Buster only.
- Establish network access and enable SSH on the device.
- You will need the Pimoroni Blinkt! Python library, https://github.com/pimoroni/blinkt or the
- Pimoroni Inky Python library: https://github.com/pimoroni/inky
- Install the appropriate library like so, making sure you answer YES to the questions.

```
curl https://get.pimoroni.com/blinkt | bash
```
or
```
curl https://get.pimoroni.com/inky | bash
```

# How to get this code
Once you have installed the Pimoroni software as above, the easiest way to download this software is to copy and paste the following command, which will make a copy of all the files in a folder called **agile-blinkt-indicator** in your home directory. This won't work unless you've installed the Blinkt! library above (or installed `git` yourself).

```
cd ~ && git -c advice.detachedHead=false clone --depth 1 -b support-other-displays https://github.com/jerbzz/octopus-agile-indicator.git
```

# How to use this code

This code runs unprivileged - no sudo required. It will drop a SQLite database file in its own directory when it runs.

The settings for the software are stored in `config.yaml`.

Open config.yaml:
```
cd ~\octopus-agile-indicator
nano config.yaml
```
and look for `DNORegion: B` at the very top. Replace this with your correct DNO region code from the list. Exit `nano` by typing Ctrl-W then Ctrl-X.

You should initially run manually to check everything works
```
./store_prices.py
```

The code will tell you what it's doing and whether it worked. You can run this as many times as you like without causing too many problems. 

Then, a separate command to update the display:

```
./update_display.py
```

This will also tell you what it's doing. If you want to show a display of dummy data you can run:

```
./update_display.py --demo
```

If it's all a bit much, you can blank the display:

```
./clear_display.py
```

# Running automatically
I really can't be bothered to make a systemd timer/service for this. `cron` is so much easier!
I've included a script to install the cron jobs listed below. Run it like this:
```
./install_crontab.sh
```
You can check it's worked by running `crontab -l`, you should see this:
```
@reboot /bin/sleep 30; cd /home/pi/octopus-agile-indicator && usr/bin/python3 store_prices.py > ./indicator.log 2>&1
@reboot /bin/sleep 40; cd /home/pi/octopus-agile-indicator && /usr/bin/python3 update_display.py > ./indicator.log 2>&1
*/30 * * * * /bin/sleep 5; cd /home/pi/octopus-agile-indicator && /usr/bin/python3 update_display.py > ./indicator.log 2>&1
30 16 * * * cd /home/pi/octopus-agile-indicator && /usr/bin/python3 store_prices.py > ./indicator.log 2>&1
30 18 * * * cd /home/pi/octopus-agile-indicator && /usr/bin/python3 store_prices.py > ./indicator.log 2>&1
30 20 * * * cd /home/pi/octopus-agile-indicator && /usr/bin/python3 store_prices.py > ./indicator.log 2>&1
```
- line 1: wait 30 seconds at startup, get new prices
- line 2: wait a further 10 seconds at startup and update the display
- line 3: wait till 5 seconds past every half hour and update the display
- lines 4, 5, and 6: update the price database at 4.30pm, 6.30pm, and 8.30pm to cover late arrival of data

# Troubleshooting

If something isn't working, run 
```
less ~/octopus-agile-indicator/indicator.log
```
This will show you the most recent message from any of the scripts (that were run automatically by `cron`). If this doesn't shed any light, run `./store_prices.py` and `./update_display.py` and see what they moan about!

# Modification

If you want to change price thresholds or fine-tune the colours, they are located in `config.yaml`. Open it using `nano update_blinkt.py` or your favourite editor. 

It's really important that you don't change the layout of the file otherwise you will encounter errors when tryingt o run the software. Each option has comments describing its effects - read, and change to your heart's content.

# To Do:

- better retry if data is late, 3 cron jobs is hacky
- more options to change display
  - maybe Blinkt! colours could depend on the averages
  - maybe Inky could show a minimum price for a duration rather than a single slot


# Thanks to:

Garry Hayne on the Octopus Agile forums (https://forum.octopus.energy) for the original idea  
pufferfish-tech's **octopus-agile-pi-prices** for inspiration (https://github.com/pufferfish-tech/octopus-agile-pi-prices)

