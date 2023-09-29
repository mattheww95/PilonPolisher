#!/bin/bash

cd /opt
wget https://www.python.org/ftp/python/3.11.3/Python-3.11.3.tgz
tar -xf ./Python-3.11.*.tgz
cd ./Python-3.11.*/
./configure --enable-optimizations
make -j 8
make install
export PATH=$PWD:$PATH
cd /opt