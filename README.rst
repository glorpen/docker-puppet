============
Puppet Suite
============

Set of containers to run PuppetServer, PuppetDB with Hashicorp Vault,
supports multiple masters on single port and comes with agent installation script generator.

Common Vault configuration
==========================

All images allow authenticating with Vault using ``app-role``, ``token`` or TLS cert.

Common available arguments and env variables.

Vault auth:

- ``--vault-addr``, ``VAULT_ADDR``
- ``--vault-token``, ``VAULT_TOKEN``
- ``--vault-app-role``, ``VAULT_APP_ROLE``
- ``--vault-app-secret``, ``VAULT_APP_SECRET``
- ``--vault-client-cert``, ``VAULT_CLIENT_CERT``
- ``--vault-client-key`` , ``VAULT_CLIENT_KEY``
- ``--vault-server-cert``, ``VAULT_SERVER_CERT``

Certificate generation:

- ``--path``, ``VAULT_PATH`` - Vault backend mountpoint, defaults to `pki`
- ``--role``, ``VAULT_ROLE`` - Vault role to use
- ``--lease-ttl``, ``VAULT_LEASE_TTL`` - Time until certificate expiration, eg. 2w(eeks), 1d10m3s

To make connection to Vault with custom CA use env ``REQUESTS_CA_BUNDLE=/path/to/ca-certs.pem``.

Token and certificate renewal
=============================

Containers will automatically renew Vault token when past 1/3 of the lease duration.

Certificates will be recreated and deployed when over 85%-95% of the lease duration.

Images
======

Proxy
*****

Based on *HAproxy*, allows to run multiple *PuppetServers* on single port.

Arguments: ``[external-domain:internal-service:internal-port]... [haproxy options]``

To start proxy handling ``puppet.example.com`` domain and forwarding it to ``my-puppet-svc`` on port ``8140`` use:

.. sourcecode:: sh

    docker run --rm glorpen/puppet-proxy:2.0.0 puppet.example.com:my-puppet-svc:8140


PuppetDB
********

Use ``CERTNAME`` env var to set *PuppetDB* host name and certificate "common name".


PuppetServer
************

Use ``PUPPETSERVER_HOSTNAME`` env var to set *PuppetServer* host name and certificate "common name".

Agent Bootstraper
*****************

Creates ``sh`` script with certificates as payload. upon runninbg installs puppet-agent from official repo and creates initial configuration for agent.

Remember to use same major version as *PuppetServer*.

.. sourcecode:: bash

    docker run --rm glorpen/puppet-packager:2.0.0
    --vault-app-role xxxxx --vault-app-secret xxxxx --vault-addr http://vault.local:8200
    --lease-ttl 10m --server-name woblink.puppet.glorpen.it test.example.com > installer.sh

