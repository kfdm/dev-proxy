import logging
from http.server import ThreadingHTTPServer

import click

from .proxy import ProxyHTTPRequestHandler

logger = logging.getLogger(__name__)


@click.group()
def cli():
    logging.basicConfig(level=logging.WARNING)


@cli.command()
@click.option("--server", default="localhost")
@click.option("--port", default=8080)
def web(server, port):
    httpd = ThreadingHTTPServer((server, port), ProxyHTTPRequestHandler)
    logger.info("http server is running %s", httpd.server_port)
    httpd.serve_forever()
