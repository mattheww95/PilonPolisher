FROM ubuntu:20.04
LABEL version="v0.0.1" description="Iterative pilong polishing"

COPY dist/pilonpolisher-0.0.1-py3-none-any.whl /opt
COPY scripts/docker*.sh /opt

RUN apt-get update
ARG DEBIAN_FRONTEND=nointeractive
ARG LC_ALL=C.UTF-8
ARG LANG_ALL=C
RUN apt-get install autoconf bzip2 libbz2-dev liblzma-dev wget gcc zlib1g-dev build-essential libncurses-dev git python3 python python3-pip default-jre cmake -y
RUN apt-get install python3-pip libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev pkg-config -y
RUN pip3 install setuptools
#RUN /opt/docker_update.sh
RUN ["chmod", "+x", "/opt/docker_install_python3.11.sh"]
RUN ["chmod", "+x", "/opt/docker_install_polisher.sh"]
RUN ["chmod", "+x", "/opt/docker_install_pilon.sh"]
RUN ["chmod", "+x", "/opt/docker_install_htslib.sh"]
RUN ["chmod", "+x", "/opt/docker_install_samtools.sh"]
RUN ["chmod", "+x", "/opt/docker_install_minimap2.sh"]

RUN /opt/docker_install_python3.11.sh
RUN /opt/docker_install_polisher.sh
RUN /opt/docker_install_pilon.sh
RUN /opt/docker_install_htslib.sh
RUN /opt/docker_install_samtools.sh
RUN /opt/docker_install_minimap2.sh
# RUN export LC_ALL=C; export PATH=/usr/bin:$PATH; export PATH=/opt/Python-3.11.3:$PATH
