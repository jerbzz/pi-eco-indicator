# agile-blinkt-indicator
Display upcoming Octopus Agile prices on the Pimoroni Blinkt! display for Raspberry Pi.

![Display in action](https://raw.githubusercontent.com/jerbzz/agile-blinkt-indicator/main/images/DSC_5094.jpg)

Read it from left to right. Each pixel represents a half hour slot, so you get 3.5 to 4 hours of data depending on when you look at it! The leftmost pixel represents the current price. On the half hour, every half hour, everything shifts one pixel to the left.

Magenta is the most expensive, then red if it's under 28p, orange if it's under 17p, yellow if it's under 13.5p, green if it's under 10p, cyan if it's under 5p, and blue if it's a plunge. You can change these quite easily by editing the code.

# Hardware needed

- Pimoroni Blinkt!, https://shop.pimoroni.com/products/blinkt
- A Raspberry Pi of any flavour, as long as you can connect the Blinkt! to it. This has been tested on a Pi Zero W and a Pi 3B+.

# Software needed

- This has been tested on Raspberry Pi OS Buster only.
- You will need the Pimoroni Blinkt! Python library, https://github.com/pimoroni/blinkt
- Install the Blinkt! library like so, making sure you answer YES to the questions.
```
curl https://get.pimoroni.com/blinkt | bash
```

# How to get this code
Once you have installed the Blinkt! software as above, the easiest way to download this software is to type the following commands, which will make a copy of all the files in a folder called **agile-blinkt-indicator** in your home directory.

```
cd ~ && git clone https://github.com/jerbzz/agile-blinkt-indicator.git
```

# How to use this code

This code runs unprivileged - no sudo required. It will drop a SQLite database file in there when it runs. Make the files executable:

```
cd ~/agile-blinkt-indicator && chmod +x *.py *.sh
```

(https://en.wikipedia.org/wiki/Distribution_network_operator):  
A = East England  
B = East Midlands  
C = London  
D = North Wales, Merseyside and Cheshire  
E = West Midlands  
F = North East England  
G = North West England  
P = North Scotland  
N = South and Central Scotland  
J = South East England  
H = Southern England  
K = South Wales  
L = South West England  
M = Yorkshire  

You should initially run manually to check everything works, replacing X with your DNO region:
```
./store_prices.py --region X
```

The code will tell you what it's doing and whether it worked. You can run this as many times as you like without causing too many problems. 

Then, a separate command to update the display:

```
./update_blinkt.py
```

This will also tell you what it's doing, as well as showing you the colours it is setting. If you want to see all the colours available, you can run 

```
./update_blinkt.py --demo
```

If it's all a bit much, you can blank the display:

```
./clear_blinkt.py
```

# Running automatically
I really can't be bothered to make a systemd timer/service for this. `cron` is so much easier!
I've included a script to install the cron jobs listed below. Run it like this, replacing X with your region:
```
./install_crontab.sh X
```
You can check it's worked by running `crontab -l`, you should see this:
```
@reboot /bin/sleep 30; cd /home/pi/agile-blinkt-indicator && /usr/bin/python3 store_prices.py --region X > ./blinkt.log 2>&1
@reboot /bin/sleep 40; cd /home/pi/agile-blinkt-indicator && /usr/bin/python3 update_blinkt.py > ./blinkt.log 2>&1
*/30 * * * * /bin/sleep 5; cd /home/pi/agile-blinkt-indicator && /usr/bin/python3 update_blinkt.py > ./blinkt.log 2>&1
30 16 * * * cd /home/pi/agile-blinkt-indicator && /usr/bin/python3 store_prices.py > ./blinkt.log 2>&1
30 18 * * * cd /home/pi/agile-blinkt-indicator && /usr/bin/python3 store_prices.py > ./blinkt.log 2>&1
30 20 * * * cd /home/pi/agile-blinkt-indicator && /usr/bin/python3 store_prices.py > ./blinkt.log 2>&1
```
- line 1: wait 30 seconds at startup, get new prices
- line 2: wait a further 10 seconds at startup and update the display
- line 3: wait till 5 seconds past every half hour and update the display
- lines 4, 5, and 6: update the price database at 4.30pm, 6.30pm, and 8.30pm to cover late arrival of data

If anything stops working, log in and run `store_prices.py` and `update_blinkt.py` and see what they moan about!

# To Do:

- better retry if data is late, 3 cron jobs is hacky
- colours could depend on daily average rather than fixed values
- configuration options?
- logging of issues

# Thanks to:

Garry Hayne on the Octopus Agile forums (https://forum.octopus.energy) for the original idea  
pufferfish-tech's **octopus-agile-pi-prices** for inspiration (https://github.com/pufferfish-tech/octopus-agile-pi-prices)

