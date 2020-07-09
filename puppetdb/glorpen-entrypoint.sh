#!/bin/sh

# consul-template -vault-addr=http://vault:8200 -config=/config.hcl -exec id -log-level=debug

exec consul-template -config=/config.hcl \
-vault-addr=${VAULT_ADDR} \
-log-level=debug \
-exec="dumb-init /docker-entrypoint.sh $@"
