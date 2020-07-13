#!/usr/bin/env python3

import os
import sys
import logging
import argparse
import subprocess
import glorpen_entrypoint.cli
from glorpen_entrypoint.cert_watcher import CertWatcher
from glorpen_entrypoint.renderer import Renderer, Runner

p = argparse.ArgumentParser("glorpen-entrypoint")

glorpen_entrypoint.cli.add_vault_auth_arguments(p)
glorpen_entrypoint.cli.add_vault_cert_arguments(p, cn=False)
glorpen_entrypoint.cli.add_catchall_argument(p)
glorpen_entrypoint.cli.add_verbosity_argument(p)

ns = p.parse_args()

logging.basicConfig(level=glorpen_entrypoint.cli.get_verbosity(ns.verbose))

cn = os.environ["PUPPETSERVER_HOSTNAME"]
watcher = CertWatcher(ns.path, ns.role, cn, ns.lease_ttl)
renderer = Renderer(
    "/etc/puppetlabs/puppet/ssl/certs/ca.pem",
    f"/etc/puppetlabs/puppet/ssl/certs/{cn}.pem",
    f"/etc/puppetlabs/puppet/ssl/private_keys/{cn}.pem",
    "/etc/puppetlabs/puppet/ssl/crl.pem"
)

def reload(proc):
    subprocess.run(["/opt/puppetlabs/bin/puppetserver", "reload"])
def stop(proc):
    subprocess.run(["/opt/puppetlabs/bin/puppetserver", "stop"])

runner = Runner(ns.args)
runner.do_reload = reload
runner.do_stop = stop

watcher.on_cert = renderer.render
renderer.on_render = runner.refresh

watcher.login(
    addr=ns.vault_addr,
    token=ns.vault_token,
    app_role=ns.vault_app_role,
    app_secret=ns.vault_app_secret,
    client_cert_path=ns.vault_client_cert,
    client_key_path=ns.vault_client_key,
    server_cert_path=ns.vault_server_cert
)

sys.exit(glorpen_entrypoint.cli.steps_runner(watcher, runner))
