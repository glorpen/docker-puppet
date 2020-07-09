#!/bin/sh

exec consul-template -config=/config.hcl \
-vault-addr=${VAULT_ADDR} \
-log-level=debug \
-exec="dumb-init /docker-entrypoint.sh $@"
