import asyncio
import logging
from pathlib import Path

import click

from . import config, proxy

logger = logging.getLogger(__name__)


@click.group()
def cli():
    logging.basicConfig(level=logging.WARN)
    logging.getLogger("devserver").setLevel(logging.DEBUG)


@cli.command()
@click.option("--config", "cfg", default=config.DEFAULT, type=Path, show_default=True)
@click.option("--host", default="localhost", show_default=True)
@click.option("--port", default=8080, show_default=True)
def web(cfg, **kwargs):
    loop = asyncio.get_event_loop()

    try:
        proxy_server = proxy.ProxyDispatch(cfg)
        loop.run_until_complete(proxy_server.main(**kwargs))
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()


@cli.command()
@click.option("--config", "cfg", default=config.DEFAULT, type=Path, show_default=True)
def list(cfg):
    for service, data in config.load(cfg)["service"].items():
        print(service, data["host"], data["port"])
