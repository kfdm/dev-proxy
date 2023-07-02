import asyncio
import logging
from pathlib import Path
from subprocess import STDOUT, check_call

from aiohttp import client, web

logger = logging.getLogger(__name__)


class HostConfig:
    def __init__(self, *, name, config):
        self.name = name
        self.config = config
        self.lock = asyncio.Lock()

    async def proxy(self, request: web.Request):
        data = await request.read() if request.can_read_body else None

        async with client.request(
            method=request.method,
            url=f"http://localhost:{self.config['port']}{request.path}",
            headers=request.headers,
            params=request.query,
            data=data,
            cookies=request.cookies,
            allow_redirects=False,
        ) as result:
            return web.Response(
                body=await result.read(),
                status=result.status,
                headers=result.headers,
            )

    async def launch(self):
        kwargs = {
            "stderr": STDOUT,
        }
        args = [
            "tmux",
            "new-session",
            "-s",
            self.name,
            "-d",
        ]
        if "command" in self.config:
            args.append(
                self.config["command"].replace("{port}", str(self.config["port"]))
            )
        if "cwd" in self.config:
            kwargs["cwd"] = Path(self.config["cwd"]).expanduser().resolve()

        logger.debug("Launching: %s %s", args, kwargs)
        check_call(args, **kwargs)
        await asyncio.sleep(5)
