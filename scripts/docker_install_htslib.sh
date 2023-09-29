#!/bin/bash

cd /opt
wget https://github.com/samtools/htslib/releases/download/1.17/htslib-1.17.tar.bz2 -O htslib.tar.bz2
bunzip2 htslib.tar.bz2 && tar -xf htslib.tar
cd ./htslib-1.17
autoreconf -i -f 
./configure
make
make install
make clean
cd /opt