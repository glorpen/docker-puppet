import os
import pathlib
import signal
import subprocess
import logging

class Renderer(object):
    def __init__(self, ca_path, cert_path, key_path, crl_path=None):
        super().__init__()

        self.ca_path = ca_path
        self.cert_path = cert_path
        self.key_path = key_path
        self.crl_path = crl_path

        self.logger = logging.getLogger(self.__class__.__name__)

    def _write(self, target, content):
        t = pathlib.Path(target)
        
        if not t.parent.exists():
            os.makedirs(t.parent)
        
        with open(t, "wt") as f:
            f.write(content)

    def render_cert(self, cert, private_key, ca_cert):
        self.logger.info("Rendering certs")

        self._write(self.ca_path, ca_cert)
        self._write(self.cert_path, cert)
        self._write(self.key_path, private_key)
        
        self.logger.info("Saved certs")

        self.on_render()
    
    def render_crl(self, crl):
        self.logger.info("Rendering crl")

        if self.crl_path:
            self._write(self.crl_path, crl)
        
        self.logger.info("Saved crl")

        self.on_render()
    
    def on_render(self):
        pass

class Runner(object):
    _proc = None

    def __init__(self, args):
        super().__init__()

        self.logger = logging.getLogger(self.__class__.__name__)
        self._args = args
    
    def send_signal(self, sig, stack=None):
        if self._proc:
            self.logger.debug("Sending signal %d", sig)
            self._proc.send_signal(sig)

    def setup_signals(self):
        signal.signal(signal.SIGTERM, self.send_signal)
        signal.signal(signal.SIGINT, self.send_signal)
        signal.signal(signal.SIGQUIT, self.send_signal)
        signal.signal(signal.SIGHUP, self.reload)

    def start(self):
        self.logger.info("Starting process")
        self.setup_signals()
        self._proc = subprocess.Popen(self._args)
        self.logger.debug("Started process on pid %d", self._proc.pid)

    def reload(self, *args):
        if self._proc:
            self.logger.info("Reloading process")
            self.do_reload(self._proc)
    
    def step(self):
        ret = self._proc.poll()
        if ret is not None:
            self.logger.info("Process exitted with %d", ret)
            return False
    
    def stop(self):
        if self._proc:
            self.logger.info("Stopping process")
            self.do_stop(self._proc)
    
    def do_stop(self, proc):
        proc.kill()
        return proc.wait()
    
    def do_reload(self, proc):
        self.logger.debug("Sending reload signal")
        proc.send_signal(signal.SIGHUP)
