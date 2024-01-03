import asyncio
import logging
from pathlib import Path

import click
from setproctitle import setproctitle

from . import config, launchd, proxy

logger = logging.getLogger(__name__)


def level(value):
    value = value.upper()
    if value not in logging._nameToLevel:
        raise click.BadParameter(f"{value} is not a valid log level")

    return value


@click.group()
@click.option("-l", "--level", default="WARN", type=level, help="Logging Level")
def cli(level):
    setproctitle("dev-server-proxy")
    logging.basicConfig(
        level=logging.getLevelName(level),
        format="%(asctime)s %(levelname)s:%(name)s:%(message)s",
    )


@cli.command()
@click.option("--config", default=config.DEFAULT, type=Path, show_default=True)
@click.option("--host", default="localhost", show_default=True)
@click.option("--port", default=8080, show_default=True)
def web(config, **kwargs):
    loop = asyncio.get_event_loop()

    try:
        proxy_server = proxy.ProxyDispatch(config)
        loop.run_until_complete(proxy_server.main(**kwargs))
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()


@cli.command()
@click.option("--label", default="net.kungfudiscomonkey.dev-server")
def install(label):
    path = launchd.install(label)
    click.echo(f"Installed to {path}")
