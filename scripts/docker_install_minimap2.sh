#!/bin/bash

cd /opt
git clone https://github.com/lh3/minimap2
cd ./minimap2
make
cp -s $PWD/minimap2 /usr/bin/
cd /opt