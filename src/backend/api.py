import src.config.config as config
from io import BytesIO
import threading
import src.log.log as log
from enum import Enum, auto
import httpx
import asyncio
from websockets.sync.client import connect
import websockets

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

    async def ping(self) -> bool:
        endpoint = endpoints[Endpoint.Ping]
        url = f"{ORIGIN}{endpoint}"
        async with httpx.AsyncClient() as client:
            try:
                r = await client.get(url)
                return r.status_code == httpx.codes.OK
            except httpx.HTTPError:
                return False

    async def normal(self, audio_file) -> bool:
        endpoint = endpoints[Endpoint.Normal]
        url = f"{ORIGIN}{endpoint}"
        files = {"file": ("record.wav", audio_file, "multipart/form-data")}
        try:
            with httpx.stream(
                "POST",
                url,
                files=files,
                timeout=120,
            ) as response:
                self.logger.debug(vars(response))
                if response.status_code == httpx.codes.OK:
                    return BytesIO(response.read())
                else:
                    return None
        except httpx.HTTPError:
            return False

    async def messages(self, audio_file) -> bool:
        endpoint = endpoints[Endpoint.Messages]
        url = f"{ORIGIN}{endpoint}"
        files = {"file": ("record.wav", audio_file, "multipart/form-data")}
        with httpx.stream(
            "POST",
            url,
            files=files,
            timeout=120,
        ) as response:
            self.logger.debug(vars(response))
            return response.status_code == httpx.codes.OK

    async def wait_for_connect(self):
        self.logger.info("Try to connect API")
        while True:
            success = await self.ping()
            if success:
                break
            await asyncio.sleep(PING_INTERVAL)

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

    async def start_ws(self):
        self.ws_thread = self.websocket_for_thread(self.ws_url)
        self.ws_thread.start()

    async def get_notification(self):
        return self.ws_thread.get_notification()

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
