import re
import datetime
import os
import time
import logging

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

def get_verbosity(v):
    levels = [
        logging.ERROR,
        logging.WARNING,
        logging.INFO,
        logging.DEBUG,
    ]
    return levels[min(len(levels)-1, v)]

def add_vault_auth_arguments(parser):
    parser.add_argument('--vault-addr', default=os.environ.get("VAULT_ADDR", None))
    parser.add_argument('--vault-token', default=os.environ.get("VAULT_TOKEN", None))
    parser.add_argument('--vault-app-role', default=os.environ.get("VAULT_APP_ROLE", None))
    parser.add_argument('--vault-app-secret', default=os.environ.get("VAULT_APP_SECRET", None))
    parser.add_argument('--vault-auth-mount', default=os.environ.get("VAULT_AUTH_MOUNT", None))

    parser.add_argument('--vault-client-cert', type=str, default=os.environ.get("VAULT_CLIENT_CERT", None))
    parser.add_argument('--vault-client-key', type=str, default=os.environ.get("VAULT_CLIENT_KEY", None))
    parser.add_argument('--vault-server-cert', type=str, default=os.environ.get("VAULT_SERVER_CERT", None))

def add_vault_cert_arguments(parser, cn=True):
    parser.add_argument('--path', default=os.environ.get("VAULT_PATH", "pki"), help="Vault backend mountpoint")
    parser.add_argument('--role', default=os.environ.get("VAULT_ROLE"), help="Vault role to use")
    if cn:
        parser.add_argument('--cn', default=os.environ.get("VAULT_CN"))
    parser.add_argument('--lease-ttl', default=os.environ.get("VAULT_LEASE_TTL"), type=type_timedelta, help="Time until certificate expiration, eg. 2w(eeks), 1d10m3s")

def add_catchall_argument(parser):
    parser.add_argument('args', nargs='*')

def add_verbosity_argument(parser):
    parser.add_argument('--verbose', '-v', action="count", default=0)

def steps_runner(watcher, runner, interval=5, watch_crl=False):
    logger = logging.getLogger("StepsRunner")

    ret = 1
    started = []
    running = True

    try:
        watcher.load_certs()
        if watch_crl:
            watcher.load_crl()
        started.append(watcher)
        runner.start()
        started.append(runner)
        
        while running:
            logger.debug("Running steps")
            for i in started:
                if i.step() is False:
                    running = False
                    break
            
            if running:
                time.sleep(interval)
    finally:
        logger.debug("Cleaning up")
        if watcher in started:
            try:
                watcher.logout()
            except:
                pass
        if runner in started:
            ret = runner.stop()
    
    return ret
