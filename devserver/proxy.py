import asyncio
import logging
import subprocess

from aiohttp import client, web

from . import config, upstream

logger = logging.getLogger(__name__)


config_map = config.load(config.DEFAULT)
configs = {k: upstream.HostConfig(config_map[k]) for k in config_map}


async def process(request: web.Request, config: upstream.HostConfig):
    logger.debug("Processing: %s %s%s", request.method, request.host, request.path)
    try:
        return await config.proxy(request)
    except client.ClientConnectorError:
        try:
            await config.launch()
        except subprocess.CalledProcessError:
            return web.Response(text="Error launching process", status=500)

    logger.debug("Retrying: %s %s%s", request.method, request.host, request.path)
    try:
        return await config.proxy(request)
    except client.ClientConnectorError:
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
