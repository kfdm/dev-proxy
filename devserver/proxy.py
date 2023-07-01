import asyncio
import logging
from subprocess import STDOUT, check_call
from threading import Semaphore

from aiohttp import ClientSession, web
from requests import ConnectionError, HTTPError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


configs = {
    "tsun.localhost": {
        "name": "tsundere",
        "port": 8000,
        "cwd": "/Users/paultraylor/Projects/tsundere",
        "command": "make web",
    },
}


async def process(request: web.Request, config):
    try:
        async with ClientSession() as session:
            async with session.get(
                url=f"http://localhost:{config['port']}{request.path}",
                headers=request.headers,
            ) as response:
                response.raise_for_status()
                return web.Response(
                    text=await response.text(),
                    status=response.status,
                    headers=response.headers,
                )

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


async def handler(request: web.Request):
    try:
        config = configs[request.host]
    except KeyError:
        logger.warning("Unknown host: %s%s", request.host, request.path)
        return web.Response(status=500, text=f"Unknown host: {request.host}")
    else:
        with config.get("lock", Semaphore()):
            logger.debug("Processing: %s%s", request.host, request.path)
            return await process(request, config)


async def main(host, port):
    server = web.Server(handler)
    runner = web.ServerRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()

    logger.info("=== Serving on http://%s:%s ===", host, port)

    # pause here for very long time by serving HTTP requests and
    # waiting for keyboard interruption
    await asyncio.sleep(100 * 3600)
