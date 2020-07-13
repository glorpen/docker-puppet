#!/bin/sh

#
# Author: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
#

set -e

config_dir="/usr/local/etc/haproxy/config"
config_file="/usr/local/etc/haproxy/haproxy.cfg"

cat ${config_dir}/03-frontend.conf.tpl \
| sed -e "s/\${port}/${LISTEN_PORT-8140}/g" \
> ${config_dir}/03-frontend.conf

lines="$(grep '#each-target:' ${config_dir}/03-frontend.conf.tpl | sed -e 's/#each-target:\s\+//g')"

# handle args: <domain>:<host>[:port] ... -some -haproxy -args
# - convert domain/port proxy to configs
# - passthrough optional haproxy arguments
for i in "$@";
do
    # break on first arguemnt starting with "-"
    if [ "${i#-}" != "$i" ];
    then
        break
    fi

    shift

    hostname="$(echo "${i}" | cut -d: -f1)"
    target="$(echo "${i}" | cut -d: -f2)"
    target_port="$(echo "${i}" | cut -d: -f3)"
    if [ "x${target_port}" == "x" ];
    then
        target_port=8140
    fi

    backend_name="${target}-${target_port}"

    echo "${lines}" | sed \
    -e "s/\${hostname}/${hostname}/g" \
    -e "s/\${backend_name}/${backend_name}/g" \
    >> ${config_dir}/03-frontend.conf

    cat ${config_dir}/02-backend.conf.tpl | sed \
    -e "s/\${name}/${backend_name}/g" \
    -e "s/\${host}/${target}/g" \
    -e "s/\${port}/${target_port}/g" \
    > ${config_dir}/02-backend-${backend_name}.conf
done

cat ${config_dir}/04-dns.conf.tpl \
| sed -e "s/\${dns}/${DNS-127.0.0.11}/g" \
> ${config_dir}/04-dns.conf

# collect generated configs
cat ${config_dir}/*.conf > ${config_file}

set -- haproxy -W -db -f "${config_file}" "$@"
exec "$@"
