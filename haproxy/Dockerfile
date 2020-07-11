FROM haproxy:2.2-alpine

COPY ./config/ /usr/local/etc/haproxy/config/
COPY ./entrypoint.sh /usr/local/bin/glorpen-entrypoint

ENTRYPOINT [ "glorpen-entrypoint" ]
