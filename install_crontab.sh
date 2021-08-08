#!/bin/bash

CONFIG_FILE="config.yaml"
INSTALL_DIR="/home/pi/octopus-agile-indicator"
PYTHON_BIN="/usr/bin/python3"

function parse_yaml {
    local prefix=$2
    local s='[[:space:]]*' w='[a-zA-Z0-9_]*' fs=$(echo @|tr @ '\034')
    sed -ne "s|^\($s\):|\1|" \
        -e "s|^\($s\)\($w\)$s:$s[\"']\(.*\)[\"']$s\$|\1$fs\2$fs\3|p" \
        -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p"  $1 |
    awk -F$fs '{
       indent = length($1)/2;
       vname[indent] = $2;
       for (i in vname) {if (i > indent) {delete vname[i]}}
       if (length($3) > 0) {
           vn=""; for (i=0; i<indent; i++) {vn=(vn)(vname[i])("_")}
           printf("%s%s%s=\"%s\"\n", "'$prefix'",vn, $2, $3);
      }
   }'
}

if crontab -l 2>/dev/null | grep -q $INSTALL_DIR; then
    echo "It looks like our crontab may already exist. Aborting..."
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "$CONFIG_FILE does not exist."
    exit 1
fi

eval $(parse_yaml config.yaml "CONF_")

if [ "$CONF_Mode" = "carbon" ]; then
    DELAY=$(( RANDOM % 60 ))
	DELAYPLUS=$(( DELAY + 5 ))
    echo "Installing pi-eco-indicator cron jobs for carbon mode..."
	(crontab -l 2>/dev/null; echo "@reboot /bin/sleep 30; $PYTHON_BIN $INSTALL_DIR/store_data.py > ./eco_indicator.log 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "@reboot /bin/sleep 40; $PYTHON_BIN $INSTALL_DIR/update_display.py > ./eco_indicator.log 2>&1") | crontab -
	(crontab -l 2>/dev/null; echo "*/30 * * * * /bin/sleep $DELAY; $PYTHON_BIN $INSTALL_DIR/store_data.py > ./eco_indicator.log 2>&1") | crontab -
	(crontab -l 2>/dev/null; echo "*/30 * * * * /bin/sleep $DELAYPLUS; $PYTHON_BIN $INSTALL_DIR/update_display.py > ./eco_indicator.log 2>&1") | crontab -
	echo "Done."
	exit 0
elif [ "$CONF_Mode" = "agile_price" ]; then
    MINUTES=$(( 30 + RANDOM % 29 ))
    echo "Installing pi-eco-indicator cron jobs for agile_price mode..."
    (crontab -l 2>/dev/null; echo "@reboot /bin/sleep 30; $PYTHON_BIN $INSTALL_DIR/store_data.py > ./eco_indicator.log 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "@reboot /bin/sleep 40; $PYTHON_BIN $INSTALL_DIR/update_display.py > ./eco_indicator.log 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "*/30 * * * * /bin/sleep 5; $PYTHON_BIN $INSTALL_DIR/update_display.py > ./eco_indicator.log 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "$MINUTES 16 * * * $PYTHON_BIN $INSTALL_DIR/store_data.py > ./eco_indicator.log 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "$MINUTES 18 * * * $PYTHON_BIN $INSTALL_DIR/store_data.py > ./eco_indicator.log 2>&1") | crontab -
    (crontab -l 2>/dev/null; echo "$MINUTES 20 * * * $PYTHON_BIN $INSTALL_DIR/store_data.py > ./eco_indicator.log 2>&1") | crontab -;
    echo "Done."
    exit 0
else
    echo "Unknown mode in $CONFIG_FILE: $CONF_Mode"
	exit 1
fi
