#!/bin/zsh

IP=$1
FIRMWARE=firmware.all
PASSWORD=ahkdante

# Here we go

COOKIEJAR=$( mktemp ./cookies-XXXX )

echo cookiejar is in $COOKIEJAR

echo Logging in...
curl -k -c $COOKIEJAR  -d idle_timeout=0\&password_value=$PASSWORD https://$IP/cgi-bin/login

# TODO: grep the cookiejar to check we logged in

echo Sending firmware...
curl -k -b $COOKIEJAR -F upload_type=FW -F upload_file=@$FIRMWARE -F upload_button=Upload https://$IP/cgi-bin/upload/firmware_upload > /dev/null

echo Removing temporary cookie jar
rm $COOKIEJAR
