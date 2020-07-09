FROM puppet/puppetdb:6.11.0

LABEL maintainer="Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>"

RUN curl https://releases.hashicorp.com/consul-template/0.25.0/consul-template_0.25.0_linux_amd64.tgz | tar -C /usr/local/bin -xvzpf -

COPY ./glorpen-entrypoint.sh /
COPY ./config.hcl /

ENTRYPOINT ["/glorpen-entrypoint.sh"]
CMD ["foreground"]
