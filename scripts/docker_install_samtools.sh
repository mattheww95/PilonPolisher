#!/bin/bash

cd /opt
wget https://github.com/samtools/samtools/releases/download/1.17/samtools-1.17.tar.bz2 -O samtools.tar.bz2
bunzip2 samtools.tar.bz2 && tar -xf samtools.tar
cd ./samtools-1.17
autoheader
autoconf -Wno-syntax
./configure
make
make install
make clean
cd /opt