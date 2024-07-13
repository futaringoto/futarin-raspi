from logging import getLogger, Logger
from typing import Any, Optional
from websockets import connect, Data


class WebSocket:
    def __init__(self, ws_url: str, logger: Optional[Logger] = None) -> None:
        self.logger = logger or getLogger("dummy")
        self.ws_url = ws_url
        self.logger.debug("Initialized WebSocket")

    async def connect(self) -> None:
        self.connection = await connect(
            self.ws_url, open_timeout=None, ping_interval=1, logger=self.logger
        )
        self.logger.debug("WebSocket Connectied")

    async def send(self, value: Any) -> None:
        await self.connection.send(value)

    async def getReceive(self) -> Optional[Data]:
        recv = await self.connection.recv()
        if recv:
            return recv
        else:
            return None
