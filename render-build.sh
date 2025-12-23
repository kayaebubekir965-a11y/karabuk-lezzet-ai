#!/usr/bin/env bash
# exit on error
set -o errexit

STORAGE_DIR=/opt/render/project/src/chrome
mkdir -p $STORAGE_DIR
cd $STORAGE_DIR

# Chrome'u İndir
echo "...Downloading Chrome"
wget -P ./ https://storage.googleapis.com/chrome-for-testing-public/114.0.5735.90/linux64/chrome-linux64.zip
unzip -q chrome-linux64.zip
rm chrome-linux64.zip
cd $HOME/project/src

# Python Paketlerini Kur
echo "...Installing Python Dependencies"
pip install -r requirements.txt