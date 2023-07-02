import asyncio
import logging
import subprocess
from pathlib import Path

from aiohttp import client, web

from . import config, upstream

logger = logging.getLogger(__name__)


config_map = config.load(config.DEFAULT)

configs = {
    config_map["service"][name]["host"]: upstream.HostConfig(
        name=name, config=config_map["service"][name]
    )
    for name in config_map["service"]
}


class ProxyDispatch:
    def __init__(self, fn: Path = config.DEFAULT):
        self.config = config.load(fn)
        self.services = {
            config_map["service"][name]["host"]: upstream.HostConfig(
                name=name, config=config_map["service"][name]
            )
            for name in config_map["service"]
        }

    async def process(self, request: web.Request, config: upstream.HostConfig):
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

    async def handler(self, request: web.Request):
        try:
            config = self.services[request.host]
        except KeyError:
            logger.warning("Unknown host: %s%s", request.host, request)
            return web.Response(status=500, text=f"Unknown host: {request.host}")
        else:
            async with config.lock:
                return await self.process(request, config)

    async def main(self, host, port):
        server = web.Server(self.handler)
        runner = web.ServerRunner(server)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()

        logger.info("=== Serving on http://%s:%s ===", host, port)

        # pause here for very long time by serving HTTP requests and
        # waiting for keyboard interruption
        await asyncio.sleep(100 * 3600)
