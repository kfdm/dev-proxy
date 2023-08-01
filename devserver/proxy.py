import logging
from asyncio import locks
from pathlib import Path

from aiohttp import client, web
from watchfiles import awatch

from . import config, upstream

logger = logging.getLogger(__name__)


class ProxyDispatch:
    def __init__(self, fn: Path = config.DEFAULT):
        self.config_file = fn
        self.servicelock = locks.Lock()

    async def process(self, request: web.Request, config: upstream.HostConfig):
        logger.debug("Processing: %s %s%s", request.method, request.host, request.path_qs)

        # Test for open connection
        await config.test()

        # Try reading upstream
        try:
            return await config.proxy(request)
        except client.ClientConnectorError:
            return web.Response(text="dev-proxy Service not yet running", status=503)

    async def handler(self, request: web.Request):
        try:
            async with self.servicelock:
                config = self.services[request.host]
        except KeyError:
            logger.warning("Unknown host: %s%s", request.host, request)
            return web.Response(status=500, text=f"dev-proxy: Unknown host: {request.host}")
        else:
            return await self.process(request, config)

    async def load(self, config_file: Path):
        async with self.servicelock:
            logger.info("Loading config %s", config_file)
            self.config = config.load(config_file)
            self.services = {
                self.config["service"][name]["host"]: upstream.HostConfig(
                    name=name, config=self.config["service"][name]
                )
                for name in self.config["service"]
            }

    async def main(self, host, port):
        await self.load(self.config_file)

        server = web.Server(self.handler)
        runner = web.ServerRunner(server)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()

        logger.info("=== Serving on http://%s:%s ===", host, port)

        async for changes in awatch(self.config_file):
            for path in changes:
                await self.load(Path(path[1]))
