import asyncio
import logging

from aiohttp import ClientConnectorError, web

from .config import HostConfig

logger = logging.getLogger(__name__)


config_map = {
    "tsun.localhost": {
        "name": "tsundere",
        "port": 8000,
        "cwd": "/Users/paultraylor/Projects/tsundere",
        "command": "make web",
    },
}


configs = {k: HostConfig(config_map[k]) for k in config_map}


async def process(request: web.Request, config: HostConfig):
    try:
        return await config.proxy(request)
    except ClientConnectorError:
        await config.launch()

    try:
        return await config.proxy(request)
    except ClientConnectorError:
        return web.Response(text="Service not yet running", status=500)


async def handler(request: web.Request):
    try:
        config = configs[request.host]
    except KeyError:
        logger.warning("Unknown host: %s%s", request.host, request.path)
        return web.Response(status=500, text=f"Unknown host: {request.host}")
    else:
        async with config.lock:
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
