#!/usr/bin/env python

"""
@author Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
"""

import io
import re
import os
import sys
import hvac
import string
import logging
import tarfile
import argparse
import datetime
import glorpen_entrypoint.cli
from glorpen_entrypoint.cert_watcher import CertWatcher

class ScriptCreator(object):
    script = """#!/bin/sh -e

#
# author: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
#

echo "Installing puppet-agent ..."
if yum --version &> /dev/null;
then
    echo "Using yum"
    yum -y --nogpgcheck localinstall https://yum.puppetlabs.com/puppet6/puppet6-release-el-$(rpm -E %{{rhel}}).noarch.rpm 
    yum -y install puppet-agent
elif emerge --version &> /dev/null;
then
    echo "Using portage"
    emerge puppet-agent --ask
elif apt --version &> /dev/null;
then
    echo "Using apt"
    curl https://apt.puppetlabs.com/puppet6-release-$(lsb_release -cs).deb > puppet-repo.deb 
    dpkg -i puppet-repo.deb
    rm puppet-repo.deb
    apt update
    apt install -y puppet-agent
else
    echo "Unknown package manager, exitting."
    exit 1
fi

echo "Creating configuration"
cat << EOS > "{puppet_agent_dir}/puppet.conf"
[agent]
server = {puppetserver_name}
masterport = {puppetserver_port}
certname = {name}
EOS

echo "Installing certificates"
mkdir -p "{puppet_agent_ssl_dir}"
tail -n +{payload_offset} $0 | tar -xvzpf - -C "{puppet_agent_ssl_dir}"

echo "Puppet agent was installed and configured."
echo "You can now test installation with 'puppet agent --test --noop'"

exit 0
"""

    def generate_script(self, common_name, server_name, server_port, certs):
        agent_dir = "/etc/puppetlabs/puppet"

        payload = self.generate_payload(common_name, certs)

        return self.script.format(
            payload_offset=len(self.script.split("\n")),
            name = common_name,
            puppet_agent_dir = agent_dir,
            puppet_agent_ssl_dir = f"{agent_dir}/ssl",
            puppetserver_port = server_port,
            puppetserver_name = server_name
        ).encode() + payload
    
    def generate_payload(self, common_name, certs):
        data = io.BytesIO()
        t = tarfile.open(fileobj=data, mode="w:gz")

        files = {
            f"private_keys/{common_name}.pem": certs["key"],
            f"certs/{common_name}.pem": certs["cert"],
            f"certs/ca.pem": certs["ca"],
            f"crl.pem": certs["crl"]
        }
        
        for ssl_path, ssl_content in files.items():
            ssl_data = ssl_content.encode()
            f = io.BytesIO(ssl_data)
            info = tarfile.TarInfo(name=ssl_path)
            info.uid = info.gid = 0
            info.size = len(ssl_data)

            t.addfile(info, fileobj=f)
        
        t.close()
        return data.getvalue()
    

p = argparse.ArgumentParser("glorpen-entrypoint")

p.add_argument("cn")
p.add_argument("--server-name", default=os.environ.get("PUPPETSERVER_HOSTNAME", "puppetserver"))
p.add_argument("--server-port", default=int(os.environ.get("PUPPETSERVER_PORT", 8140)), type=int)

glorpen_entrypoint.cli.add_vault_auth_arguments(p)
glorpen_entrypoint.cli.add_vault_cert_arguments(p, cn=False)
glorpen_entrypoint.cli.add_verbosity_argument(p)

ns = p.parse_args()

logging.basicConfig(level=glorpen_entrypoint.cli.get_verbosity(ns.verbose))

print("Collecting certificates", file=sys.stderr)

watcher = CertWatcher(ns.path, ns.role, ns.cn, ns.lease_ttl)
watcher.login(
    addr=ns.vault_addr,
    token=ns.vault_token,
    app_role=ns.vault_app_role,
    app_secret=ns.vault_app_secret,
    client_cert_path=ns.vault_client_cert,
    client_key_path=ns.vault_client_key,
    server_cert_path=ns.vault_server_cert
)
certs = watcher.get_certs()
watcher.logout()

print("Generating script", file=sys.stderr)
s = ScriptCreator()
ret = s.generate_script(ns.cn, ns.server_name, ns.server_port, certs)

sys.stdout.buffer.write(ret)
