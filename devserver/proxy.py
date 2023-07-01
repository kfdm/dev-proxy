import asyncio
import logging
from subprocess import STDOUT, check_call
from threading import Semaphore

from aiohttp import web
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


async def process(request: web.Request, config):
    client = Session()
    try:
        response = client.get(
            url=f"http://localhost:{config['port']}{request.path}",
            headers=request.headers,
        )
        response.raise_for_status()
    except HTTPError:
        return web.Response(body=response.content, status=response.status_code)
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
        return web.Response(text="Service not yet running", status=500)
    else:
        content_type = response.headers["Content-Type"]

        return web.Response(
            body=response.content,
            status=response.status_code,
            content_type=content_type.split(";", 1)[0]
            if ";" in content_type
            else content_type,
        )


async def handler(request: web.Request):
    try:
        config = configs[request.host]
    except KeyError:
        return web.Response(status=500, text=f"Unknown host: {request.host}")
    else:
        with config.get("lock", Semaphore()):
            return await process(request, config)


async def main(host, port):
    server = web.Server(handler)
    runner = web.ServerRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()

    print(f"======= Serving on http://{host}:{port}/ ======")

    # pause here for very long time by serving HTTP requests and
    # waiting for keyboard interruption
    await asyncio.sleep(100 * 3600)
