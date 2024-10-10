import src.config.config as config
import src.log.log as log
from enum import Enum, auto
import httpx
import asyncio

PING_INTERVAL = 10
ORIGIN = config.get("api_origin")
VERSION = config.get("api_version")
ID = config.get("id")
RETRIES = 4


class Endpoint(Enum):
    WssNegotiate = auto()


endpoints = {Endpoint.WssNegotiate: f"/{VERSION}/raspis/{ID}/negotiate"}


class Api:
    def __init__(self):
        self.logger = log.get_logger("Api")

    async def wait_for_connect(self):
        self.logger.info("Try to connect API")
        while not await self.req_wss_url():
            await asyncio.sleep(PING_INTERVAL)

    async def req_wss_url(self) -> bool:
        url = f"{ORIGIN}{Endpoint.WssNegotiate}"
        async with httpx.AsyncClient() as client:
            try:
                r = await client.post(url)
                if r.status_code == httpx.codes.OK:
                    self.wss_url = r.text
                    return True
                else:
                    return False
            except httpx.HTTPError:
                return False


api = Api()
