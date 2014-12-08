#!/bin/bash

# Contributed by Marius Wigger

IP=$1
PASSWORD=ahkdante
COOKIEJAR=$( mktemp ./cookies-XXXX )
curl -k -c $COOKIEJAR  -d idle_timeout=0\&password_value=$PASSWORD https://$IP/cgi-bin/login >/dev/null
curl -k  -b $COOKIEJAR  -e "https://$IP/diagnostics/host_cpu.html" https://$IP/cgi-bin/diagnostics/host_cpu --data "device_type=blade&host_power_control=s5_hard" >/dev/null
rm $COOKIEJAR
 
while ping -c1  $IP &>/dev/null; do echo "host still up" ; done
mac=$(arp -a | grep $IP | cut -d' ' -f4 )
wol $mac
