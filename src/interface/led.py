import httpx
import asyncio
from enum import Enum, auto
import src.config.config as config
from src.log.logger import get_logger

RETRES = 8
STATUS_CODE = 202
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
    LedPatterns.WifiHigh: "/wifi/high",
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
    url = f"{ORIGIN}{led_endpoint}"
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(url)
            if r.status_code == STATUS_CODE:
                logger.info(f"Change LED lighting pattern. ({led_pattern})")
            else:
                logger.error(
                    f'Failed to change LED lighting pattern ("POST {url}" r.status_code)'
                )
        except httpx.HTTPError:
            logger.error(f"Failed to change LED lighting pattern (POST {url})")


if __name__ == "__main__":
    asyncio.run(set(LedPatterns.WifiHigh))
