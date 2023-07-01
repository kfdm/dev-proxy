from http.server import BaseHTTPRequestHandler
from subprocess import STDOUT, check_call
from threading import Semaphore

from requests import ConnectionError, HTTPError, Session

configs = {
    "tsun.localhost": {
        "name": "tsundere",
        "port": 8000,
        "cwd": "/Users/paultraylor/Projects/tsundere",
        "command": "make web",
    },
}


class ProxyHTTPRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def do_GET(self, body=True):
        try:
            host = self.headers["Host"]
            config = configs[host]
        except KeyError:
            self.send_error(500, f"Unknown host: {host}")
            return

        client = Session()

        with config.get("lock", Semaphore()):
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
                    cwd=config['cwd'],
                    stderr=STDOUT,
                )
                self.send_error(500, "Service not running yet")
            else:
                self.send_response(response.status_code)
                self.wfile.write(response.content)
