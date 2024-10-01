import httpx
import asyncio
from enum import Enum, auto
import src.config.config as config
from src.log.logger import get_logger

RETRES = 8
ORIGIN = config.get("led_server_origin")
TRANSPORT = httpx.HTTPTransport(retries=RETRES)

logger = get_logger("Led")


class LedPatterns(Enum):
    WifiHigh = auto()
    WifiMiddle = auto()
    WifiLow = auto()
    WifiDisconnect = auto()
    AudioListening = auto()
    AudioThinking = auto()
    AudioResSuccess = auto()
    AudioResFail = auto()


led_endpoints = {
    LedPatterns.WifiHigh: "/wifi/hith",
    LedPatterns.WifiMiddle: "/wifi/middle",
    LedPatterns.WifiLow: "/wifi/low",
    LedPatterns.WifiDisconnect: "/wifi/disconnect",
    LedPatterns.AudioListening: "/audio/listening",
    LedPatterns.AudioThinking: "/audio/thinking",
    LedPatterns.AudioResSuccess: "/audio/res-success",
    LedPatterns.AudioResFail: "/audio/res-fail",
}


async def set(led_pattern: LedPatterns):
    led_endpoint = led_endpoints[led_pattern]
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(f"{ORIGIN}{led_endpoint}")
            logger.info(f"POST: {led_endpoint} {r.status_code}")
        except httpx.HTTPError:
            logger.error(f"POST: {led_endpoint}")


if __name__ == "__main__":
    asyncio.run(set(LedPatterns.WifiHigh))
