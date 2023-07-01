from http.server import HTTPServer

import click

from .proxy import ProxyHTTPRequestHandler


@click.group()
def cli():
    pass


@cli.command()
@click.option("--server", default="localhost")
@click.option("--port", default=8080)
def web(server, port):
    httpd = HTTPServer((server, port), ProxyHTTPRequestHandler)
    print("http server is running", httpd.server_port)
    httpd.serve_forever()
