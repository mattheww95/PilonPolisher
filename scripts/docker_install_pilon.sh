#!/bin/bash

cd /opt
mkdir pilon
cd pilon
wget https://github.com/broadinstitute/pilon/releases/download/v1.24/pilon-1.24.jar -O pilon.jar
mv pilon.jar /usr/bin/
cd /opt