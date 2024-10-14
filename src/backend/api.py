import src.config.config as config
from src.interface.led import led, LedPattern
from io import BytesIO
from src.log.log import log
import httpx
import asyncio
from websockets.asyncio.client import connect
import websockets
from typing import Optional
from enum import Enum, auto

PING_INTERVAL = 10
ORIGIN = config.get("api_origin")
VERSION = 2
ID = config.get("id")
RETRIES = 4
SENSOR_INTERVAL = 0.1


class Endpoint(Enum):
    WsNegotiate = auto()
    Ping = auto()
    Normal = auto()
    Messages = auto()


endpoints = {
    Endpoint.WsNegotiate: f"/v{VERSION}/raspis/{ID}/negotiate",
    Endpoint.Ping: "/ping",
    Endpoint.Normal: f"/v{VERSION}/raspis/{ID}",
    Endpoint.Messages: f"/v{VERSION}/raspis/{ID}/messages",
}


class Api:
    def __init__(self):
        self.logger = log.get_logger("Api")
        self.logger.info("Initialized.")

    async def get(self, endpoint: str, file=None, retries=5) -> Optional[int]:
        url = f"{ORIGIN}{endpoint}"
        if file:
            self.logger.error("Not implemented.")
        else:
            for i in range(retries):
                async with httpx.AsyncClient() as client:
                    try:
                        r = await client.get(url)
                        return r.status_code
                    except httpx.HTTPError:
                        continue
            return None

    async def post(
        self, endpoint_enum: Endpoint, audio_file=None, retries=5
    ) -> Optional[BytesIO] | Optional[httpx.codes]:
        endpoint = endpoints[endpoint_enum]
        url = f"{ORIGIN}{endpoint}"
        if audio_file:
            files = {"file": ("record.wav", audio_file, "multipart/form-data")}
            for _ in range(retries):
                try:
                    with httpx.stream(
                        "POST",
                        url,
                        files=files,
                        timeout=120,
                    ) as response:
                        if response.status_code == httpx.codes.OK:
                            return BytesIO(response.read())
                        else:
                            continue
                except httpx.HTTPError:
                    continue
            return None
        else:
            self.logger.error("Not implemented.")

    async def wait_for_connect(self):
        self.logger.info("Try to connect API")
        while True:
            success = await self.ping()
            if success:
                break
            await asyncio.sleep(PING_INTERVAL)

    async def ping(self) -> bool:
        status_code = await self.get(endpoints[Endpoint.Ping])
        return status_code == httpx.codes.OK

    async def normal(self, audio_file) -> Optional[BytesIO]:
        led.req(LedPattern.AudioThinking)
        response_file = await self.post(Endpoint.Normal, audio_file=audio_file)
        led.req(LedPattern.AudioResSuccess)
        return response_file

    async def messages(self, audio_file) -> Optional[BytesIO]:
        led.req(LedPattern.AudioUploading)
        response_file = await self.post(Endpoint.Messages, audio_file=audio_file)
        led.req(LedPattern.AudioResSuccess)
        return response_file

    async def get_message(self):
        endpoint = f"endpoints[Endpoint.Messages]/{self.message_id}"
        url = f"{ORIGIN}{endpoint}"
        received_file = await self.get(endpoint)
        return received_file

    ### Notification
    async def req_ws_url(self) -> bool:
        endpoint = endpoints[Endpoint.WsNegotiate]
        url = f"{ORIGIN}{endpoint}"
        async with httpx.AsyncClient() as client:
            try:
                r = await client.post(url)
                if r.status_code == httpx.codes.OK:
                    self.ws_url = r.json()["url"]
                    return True
                else:
                    return False
            except httpx.HTTPError as e:
                self.logger.error(e)
                return False

    async def wait_for_notification(self):
        self.logger.debug("Wait for notification.")
        while not self.notified:
            await asyncio.sleep(SENSOR_INTERVAL)

    async def start_listening_notification(self):
        self.ws_task = asyncio.create_task(self.run_websockets())

    async def run_websockets(self):
        while True:
            async with connect(self.ws_url) as websocket:
                try:
                    async with connect(self.ws_url) as ws:
                        self.logger.info("WebSockets connected.")
                        await ws.send(f'{{"action": "register", "clientId": {ID}}}')

                        while True:
                            self.logger.info("Listening notification.")
                            self.message_id = await ws.recv()
                            self.notified = True
                            self.logger.info("Notified.")

                except websockets.exceptions:
                    self.logger.info("WebSockets connection closed by the server.")

    api = Api()
