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
    logger.debug("Processing: %s %s%s", request.method, request.host, request.path)
    try:
        return await config.proxy(request)
    except ClientConnectorError:
        await config.launch()

    logger.debug("Retrying: %s %s%s", request.method, request.host, request.path)
    try:
        return await config.proxy(request)
    except ClientConnectorError:
        return web.Response(text="Service not yet running", status=503)


async def handler(request: web.Request):
    try:
        config = configs[request.host]
    except KeyError:
        logger.warning("Unknown host: %s%s", request.host, request)
        return web.Response(status=500, text=f"Unknown host: {request.host}")
    else:
        async with config.lock:
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
