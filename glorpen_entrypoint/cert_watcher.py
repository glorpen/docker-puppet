import hvac
import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import threading
import logging
import random

class CertWatcher(object):
    _timer_cert = None
    _timer_token = None

    _ssl_crl = None
    _ssl_cert = None
    _ssl_ca_cert = None
    _ssl_key = None

    def __init__(self, path, role, cn, lease_ttl: datetime.timedelta):
        super().__init__()

        self.path = path
        self.role = role
        self.cn = cn
        self.lease_ttl = lease_ttl

        self.logger = logging.getLogger(self.__class__.__name__)

    
    def login(self, addr, token=None, app_role=None, app_secret=None, client_cert_path=None, client_key_path=None, server_cert_path=None):
        # url=os.environ['VAULT_ADDR'],
        # token=os.environ['VAULT_TOKEN'],

        self.client = hvac.Client(
            url = addr,
            cert = (client_cert_path, client_key_path) if client_cert_path else None,
            verify = server_cert_path,
        )

        if token:
            self.logger.info("Using Vault token")
            self.client.token = token
        elif app_role and app_secret:
            self.logger.info("Using Vault app-role auth")
            self.client.auth_approle(app_role, app_secret)
        else:
            raise Exception("No auth data provided")

        self.schedule_token_renew()

    def load_certs(self):
        self.logger.info("Loading certs")
        # TODO: error when no vault?
        cert_response = self.client.secrets.pki.generate_certificate(
            mount_point=self.path,
            name=self.role,
            common_name=self.cn,
            extra_params={
                "ttl": int(self.lease_ttl.total_seconds()) if self.lease_ttl else None,
            }
        )

        self._ssl_crl = self.client.secrets.pki.read_crl(self.path)
        self._ssl_cert = cert_response["data"]["certificate"]
        self._ssl_ca_cert = cert_response["data"]["issuing_ca"]
        self._ssl_key = cert_response["data"]["private_key"]

        self.schedule_certs_renew()

        self.on_cert(self._ssl_cert, self._ssl_key, self._ssl_ca_cert, self._ssl_crl)
    
    def renew_token(self):
        self.logger.info("Renewing vault token")
        self.client.renew_self_token()

    def schedule_certs_renew(self):
        # https://github.com/hashicorp/consul-template/blob/master/dependency/vault_common.go
        # Use a stagger over 85%-95% of the lease duration so that many clients do not hit Vault simultaneously
        # sleep = sleep * (.85 + rand.Float64()*0.1)

        self._cancel_timer("cert")

        # we ignore CA ttl since it always should be bigger than out cert
        
        cert = x509.load_pem_x509_certificate(self._ssl_cert.encode(), default_backend())
        sleep_seconds = (cert.not_valid_after - datetime.datetime.utcnow()).total_seconds() * (0.85 + random.random() * 0.1)
        
        self._timer_cert = threading.Timer(sleep_seconds, self.load_certs)
        self._timer_cert.start()
    
    def schedule_token_renew(self):
        # https://github.com/hashicorp/consul-template/blob/master/dependency/vault_common.go
        # Renew at 1/3 the remaining lease. This will give us an opportunity to retry at least one more time should the first renewal fail.
		# sleep = sleep / 3.0
		# Use some randomness so many clients do not hit Vault simultaneously.
		# sleep = sleep * (rand.Float64() + 1) / 2.0

        self._cancel_timer("token")

        info = self.client.lookup_token()

        if not info["renewable"]:
            return
        
        if info["ttl"] > 0:
            self._timer_token = threading.Timer(
                info["ttl"] / 3.0 * (random.random() + 1) / 2.0,
                self.renew_token
            )
            self._timer_token.start()
        else:
            self.renew_token()
            self.schedule_token_renew()

    def on_cert(self, cert, private_key, ca_cert, crl):
        pass

    def _cancel_timer(self, name):
        attr = f"_timer_{name}"
        timer = getattr(self, attr)
        if timer:
            timer.cancel()
            setattr(self, attr, None)

    def logout(self):
        self._cancel_timer("token")
        self._cancel_timer("cert")

        self.client.logout()