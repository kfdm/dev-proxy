import asyncio
import logging

import click

from .proxy import main

logger = logging.getLogger(__name__)


@click.group()
def cli():
    logging.basicConfig(level=logging.WARNING)


@cli.command()
@click.option("--server", default="localhost")
@click.option("--port", default=8080)
def web(server, port):
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(main(server, port))
    except KeyboardInterrupt:
        pass
    loop.close()
