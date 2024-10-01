import httpx
import asyncio
from enum import Enum
import src.config.config as config
from src.log.logger import get_logger

RETRES = 8
ORIGIN = config.get("led_server_origin")
TRANSPORT = httpx.HTTPTransport(retries=RETRES)

logger = get_logger("Led")


class LedEndpoints(Enum):
    WifiHigh = "/wifi/high"
    WifiMiddle = "/wifi/middle"
    WifiLow = "/wifi/low"
    WifiDisconnect = "/wifi/disconnect"


### MAIN ###
async def set(led_endpoint: LedEndpoints):
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(f"{ORIGIN}{led_endpoint}")
            logger.info(f"POST: {led_endpoint} {r.status_code}")
        except httpx.HTTPError:
            logger.error(f"POST: {led_endpoint}")


if __name__ == "__main__":
    asyncio.run(set(LedEndpoints.WifiHigh))
