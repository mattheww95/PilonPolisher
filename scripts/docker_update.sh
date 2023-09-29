#!/bin/bash

# Script to update ubuntu in docker image
export DEBIAN_FRONTEND=nointeractive
# apt-get update
apt-get install autoconf bzip2 libbz2-dev liblzma-dev wget gcc zlib1g-dev build-essential libncurses-dev git python3 python python3-pip default-jre cmake -y
apt-get install python3-pip libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev pkg-config -y
pip3 install setuptools
export LC_ALL=C.UTF-8
export LANG=C.UTF-8