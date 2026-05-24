import asyncio

import uvicorn

from lib.app import create_app
from lib.settings import Settings


async def run() -> None:
    cfg = Settings()
    app = create_app(cfg)
    config = uvicorn.Config(app, host=cfg.api_host, port=cfg.api_port)
    await uvicorn.Server(config).serve()


if __name__ == "__main__":
    asyncio.run(run())
