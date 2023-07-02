import asyncio
import logging

import click

from . import proxy

logger = logging.getLogger(__name__)


@click.group()
def cli():
    logging.basicConfig(level=logging.WARN)
    logging.getLogger("devserver").setLevel(logging.DEBUG)


@cli.command()
@click.option("--server", default="localhost")
@click.option("--port", default=8080)
def web(server, port):
    loop = asyncio.get_event_loop()

    try:
        proxy_server = proxy.ProxyDispatch()
        loop.run_until_complete(proxy_server.main(server, port))
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
