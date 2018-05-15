FROM glorpen/puppetizer-base:centos-latest

LABEL maintainer="Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>"

ADD ./puppetizer /opt/puppetizer/sources/main

RUN /opt/puppetizer/bin/build
