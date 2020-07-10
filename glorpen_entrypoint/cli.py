import re
import datetime
import os

def type_timedelta(v):
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

def add_vault_auth_arguments(parser):
    parser.add_argument('--vault-addr', default=os.environ.get("VAULT_ADDR", None))
    parser.add_argument('--vault-token', default=os.environ.get("VAULT_TOKEN", None))
    parser.add_argument('--vault-app-role', default=os.environ.get("VAULT_APP_ROLE", None))
    parser.add_argument('--vault-app-secret', default=os.environ.get("VAULT_APP_SECRET", None))

    parser.add_argument('--vault-client-cert', type=str, default=None)
    parser.add_argument('--vault-client-key', type=str, default=None)
    parser.add_argument('--vault-server-cert', type=str, default=None)

def add_vault_cert_arguments(parser, cn=True):
    parser.add_argument('--path', default=os.environ.get("VAULT_PATH"))
    parser.add_argument('--role', default=os.environ.get("VAULT_ROLE"))
    if cn:
        parser.add_argument('--cn', default=os.environ.get("VAULT_CN"))
    parser.add_argument('--lease-ttl', default=os.environ.get("VAULT_LEASE_TTL"), type=type_timedelta)

def add_catchall_argument(parser):
    parser.add_argument('args', nargs='*')
