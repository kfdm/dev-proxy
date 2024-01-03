import asyncio
import logging
import os
import plistlib
import subprocess
import sys
from pathlib import Path

import click

from . import config, proxy

logger = logging.getLogger(__name__)


@click.group()
def cli():
    logging.basicConfig(level=logging.WARN)
    logging.getLogger("devserver").setLevel(logging.DEBUG)


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
def install():
    label = "net.kungfudiscomonkey.dev-server"
    path = Path.home() / "Library" / "LaunchAgents" / (label + ".plist")
    print(path)
    logs = Path.home() / "Library" / "Logs" / label
    # https://launchd.info/
    pl = plistlib.loads(b'<plist version="1.0"><dict></dict></plist>')
    pl["Label"] = label
    pl["ProgramArguments"] = [
        str(Path(sys.argv[0]).absolute()),
        "web",
        "--port",
        "7999",
    ]
    pl["RunAtLoad"] = True
    pl["StandardOutPath"] = str(logs)
    pl["StandardErrorPath"] = str(logs)
    pl["EnvironmentVariables"] = {"PATH": os.environ["PATH"]}
    with path.open("wb+") as fp:
        print("Writing to ", fp.name)
        plistlib.dump(pl, fp=fp)

    print(f"Unload {path}")
    subprocess.check_call(["launchctl", "unload", path])
    print(f"Load {path}")
    subprocess.check_call(["launchctl", "load", path])


# launchctl enable user/`id -u`/com.ionic.python.ionic-fs-watcher.startup
