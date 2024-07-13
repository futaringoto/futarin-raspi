#!/bin/sh
sudo apt update
sudo apt install unzip
cd /tmp
curl -OL "https://github.com/futaringoto/futarin-raspi/archive/main.zip"
unzip -d /opt main.zip
mv /opt/futarin-raspi-main /opt/futarin
cd /opt/futarin/
./setup.sh
