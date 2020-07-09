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
import tarfile
import argparse
import datetime

class ScriptCreator(object):
    script = """#!/bin/sh -e

#
# author: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
#

echo "Installing puppet-agent ..."
if yum --version &> /dev/null;
then
    echo "Using yum"
    yum -y --nogpgcheck localinstall https://yum.puppetlabs.com/puppet6/puppet6-release-el-8.noarch.rpm 
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

    def generate_script(self, common_name, server_name, server_port):
        agent_dir = "/etc/puppetlabs/puppet"

        payload = self.generate_payload(common_name)

        return self.script.format(
            payload_offset=len(self.script.split("\n")),
            name = common_name,
            puppet_agent_dir = agent_dir,
            puppet_agent_ssl_dir = f"{agent_dir}/ssl",
            puppetserver_port = server_port,
            puppetserver_name = server_name
        ).encode() + payload
    
    def generate_payload(self, common_name):
        data = io.BytesIO()
        t = tarfile.open(fileobj=data, mode="w:gz")

        files = {
            f"private_keys/{common_name}.pem": self.ssl_key,
            f"certs/{common_name}.pem": self.ssl_cert,
            f"certs/ca.pem": self.ssl_ca_cert,
            f"crl.pem": self.ssl_crl
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


    def load_certs(self, path, role, cn, lease_ttl):
        client = hvac.Client(
            url=os.environ['VAULT_ADDR'],
            token=os.environ['VAULT_TOKEN'],
            # TODO
            # cert=(client_cert_path, client_key_path),
            # verify=server_cert_path,
        )

        cert_response = client.secrets.pki.generate_certificate(
            mount_point=path,
            name=role,
            common_name=cn,
            extra_params={
                "ttl": lease_ttl.total_seconds() if lease_ttl else None
            }
        )

        self.ssl_crl = client.secrets.pki.read_crl(path)
        self.ssl_cert = cert_response["data"]["certificate"]
        self.ssl_ca_cert = cert_response["data"]["issuing_ca"]
        self.ssl_key = cert_response["data"]["private_key"]

def timedelta(v):
    time_map = {
        "d": "days",
        "s": "seconds",
        "m": "minutes",
        "h": "hours",
        "w": "weeks"
    }

    types = re.escape("".join(time_map.keys()))
    kwargs = {}
    for m in re.finditer(f"(?P<value>[0-9]+)(?P<type>[{types}])", v):
        m = m.groupdict()
        kwargs[time_map[m["type"]]] = int(m["value"])

    return datetime.timedelta(**kwargs)

if __name__ == "__main__":
    p = argparse.ArgumentParser()

    p.add_argument("server_name")
    p.add_argument("cn")
    p.add_argument("--path", "-p", default="pki")
    p.add_argument("--lease-ttl", "-l", default=None, type=timedelta)
    p.add_argument("--role", "-r", default="agent")
    p.add_argument("--server-port", default=8140, type=int)

    ns = p.parse_args()

    s = ScriptCreator()
    print("Collecting certificates", file=sys.stderr)
    s.load_certs(ns.path, ns.role, ns.cn, ns.lease_ttl)

    print("Generating script", file=sys.stderr)
    ret = s.generate_script(ns.cn, ns.server_name, ns.server_port)

    sys.stdout.buffer.write(ret)
