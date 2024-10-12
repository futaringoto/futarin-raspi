import src.config.config as config
from src.interface.led import led, LedPattern
from io import BytesIO
from src.log.log import log
import threading
import httpx
import asyncio
from typing import Optional
from websockets.sync.client import connect
import websockets
from enum import Enum, auto

PING_INTERVAL = 10
ORIGIN = config.get("api_origin")
VERSION = 2
ID = config.get("id")
RETRIES = 4


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

    async def get(
        self, endpoint: Endpoint, file=None, retries=5
    ) -> Optional[httpx.codes]:
        endpoint = endpoints[Endpoint.Ping]
        url = f"{ORIGIN}{endpoint}"
        if file:
            pass
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
        self, endpoint: Endpoint, audio_file=None, retries=5
    ) -> Optional[httpx.codes]:
        endpoint = endpoints[Endpoint.Normal]
        url = f"{ORIGIN}{endpoint}"
        if audio_file:
            files = {"file": ("record.wav", audio_file, "multipart/form-data")}
            for i in range(retries):
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

    async def ping(self) -> bool:
        status_code = await self.get(Endpoint.Ping)
        return status_code == httpx.codes.OK

    async def normal(self, audio_file) -> bool:
        led.req(LedPattern.AudioThinking)
        response_file = await self.post(Endpoint.Normal, audio_file=audio_file)
        led.req(LedPattern.AudioResSuccess)
        return response_file

    async def messages(self, audio_file) -> bool:
        led.req(LedPattern.AudioUploading)
        response_file = await self.post(Endpoint.Messages, audio_file=audio_file)
        led.req(LedPattern.AudioResSuccess)
        return response_file

    # Wait for ping success
    async def wait_for_connect(self):
        self.logger.info("Try to connect API")
        while True:
            success = await self.ping()
            if success:
                break
            await asyncio.sleep(PING_INTERVAL)

    async def get_message(self, message_id):
        endpoint = f"endpoints[Endpoint.Messages]/{message_id}"
        url = f"{ORIGIN}{endpoint}"
        try:
            with httpx.stream(
                "GET",
                url,
                timeout=120,
            ) as response:
                self.logger.debug(vars(response))
                if response.status_code == httpx.codes.OK:
                    return BytesIO(response.read())
                else:
                    return None
        except httpx.HTTPError:
            return False

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
        message_id = None
        try:
            async with websockets.connect(self.ws_url) as ws:
                self.logger.info("WebSockets connected.")
                await ws.send(f'{{"action": "register", "clientId": {ID}}}')

                print(await ws.recv())

                self.logger(message_id)

        except websockets.exceptions.ConnectionClosedOK:
            self.logger.info("WebSockets connection closed by the server")

    ## not using
    async def start_ws(self):
        self.ws_thread = self.websocket_for_thread(self.ws_url)
        self.ws_thread.start()

    ## not using
    async def get_notification(self):
        return self.ws_thread.get_notification()

    ## not using
    class websocket_for_thread(threading.Thread):
        def __init__(self, ws_url, name="WebsocketThread"):
            super().__init__(name=name)
            self.is_notified = False
            self.ws_url = ws_url
            self.logger = log.get_logger("WebsocketThread")

        def run(self):
            while True:
                try:
                    with connect(self.ws_url) as ws:
                        self.logger.info("Connected.")
                        ws.send(f'{{"action": "register", "clientId": {ID}}}')
                        while True:
                            ws.recv()
                            self.is_notified = True
                except websockets.exceptions.ConnectionClosedOK:
                    self.logger.info("Connection closed by the server")

        def get_notification(self) -> bool:
            if self.is_notified:
                self.is_notified = False
                return True
            else:
                return False


api = Api()
