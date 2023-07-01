from http.server import BaseHTTPRequestHandler
from subprocess import STDOUT, check_call
from threading import Semaphore
import logging
from requests import ConnectionError, HTTPError, Session


logger = logging.getLogger(__name__)

configs = {
    "tsun.localhost": {
        "name": "tsundere",
        "port": 8000,
        "cwd": "/Users/paultraylor/Projects/tsundere",
        "command": "make web",
    },
}


class ProxyRequest(BaseHTTPRequestHandler):
    def lookup_host(self, **kwargs):
        try:
            self.process_host(host=self.headers["Host"], **kwargs)
        except KeyError:
            self.send_error(500, "Missing Host Header")

    def process_host(self, host, **kwargs):
        try:
            config = configs[host]
        except KeyError:
            self.send_error(500, f"Unknown host: {host}")
        else:
            with config.get("lock", Semaphore()):
                self.process_request(host=host, config=config, **kwargs)

    def process_request(self, host, config, **kwargs):
        client = Session()
        try:
            response = client.get(
                url=f"http://localhost:{config['port']}{self.path}",
                headers=self.headers,
            )
            response.raise_for_status()
        except HTTPError:
            self.send_error(response.status_code)
        except ConnectionError:
            check_call(
                [
                    "tmux",
                    "new-session",
                    "-s",
                    config["name"],
                    "-d",
                    config["command"],
                ],
                cwd=config["cwd"],
                stderr=STDOUT,
            )
            self.send_error(500, "Service not running yet")
        else:
            self.send_response(response.status_code)
            self.wfile.write(response.content)


class ProxyHTTPRequestHandler(ProxyRequest):
    protocol_version = "HTTP/1.0"

    def do_GET(self, body=True):
        self.lookup_host(method="GET")

    def do_POST(self, body=True):
        self.lookup_host(method="POST")
