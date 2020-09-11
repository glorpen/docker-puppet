FROM puppet/puppetdb:6.11.0

LABEL maintainer="Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>"

RUN apt-get update \
    && DEBIAN_FRONTEND="noninteractive" apt-get install --no-install-recommends -y python3-minimal python3-cryptography python3-requests python3-pip python3-dateutil \
    && pip3 install hvac==0.10.4 \
    && apt-get purge -y python3-pip \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /root/.cache \
    && find /var/log /var/cache -type f -delete

COPY glorpen_entrypoint/ /usr/lib/python3/dist-packages/glorpen_entrypoint/
COPY puppetdb/entrypoint.py /usr/lib/python3/dist-packages/glorpen_entrypoint/__main__.py

ENV USE_PUPPETSERVER=false

ENTRYPOINT ["dumb-init", "-c", "python3", "-m", "glorpen_entrypoint"]
CMD ["--", "/docker-entrypoint.sh", "foreground"]
