import asyncio
import logging
from asyncio import Lock
from subprocess import STDOUT, check_call

from aiohttp import ClientSession, web

logger = logging.getLogger(__name__)


class HostConfig:
    def __init__(self, config):
        self.config = config
        self.lock = Lock()

    async def proxy(self, request):
        async with ClientSession() as session:
            async with session.get(
                url=f"http://localhost:{self.config['port']}{request.path}",
                headers=request.headers,
            ) as result:
                return web.Response(
                    text=await result.text(),
                    status=result.status,
                    headers=result.headers,
                )

    async def launch(self):
        logger.info("Launching .... %s", self.config["command"])
        check_call(
            [
                "tmux",
                "new-session",
                "-s",
                self.config["name"],
                "-d",
                self.config["command"],
            ],
            cwd=self.config["cwd"],
            stderr=STDOUT,
        )
        await asyncio.sleep(5)
