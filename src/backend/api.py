import src.config.config as config
import json
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
        self.notified = False
        self.message_id = None

    # for ping, get message
    async def get(
        self, endpoint: str, file=None, except_file=False
    ) -> Optional[httpx.Response]:
        url = f"{ORIGIN}{endpoint}"
        if except_file:
            if file:
                self.logger.error("Not implemented.")
            for _ in range(RETRIES):
                try:
                    with httpx.stream(
                        "GET",
                        url,
                        timeout=120,
                    ) as response:
                        self.logger.debug(f"{response.status_code=}")
                        if response.status_code == httpx.codes.OK:
                            self.logger.info(
                                f"Connection successful. ({url=}, {response.status_code=})"
                            )
                            return response
                        else:
                            self.logger.warn(
                                f"Response has error code. Will be retry. ({url=}, {response.status_code=})"
                            )
                            continue
                except httpx.HTTPError:
                    self.logger.warn("HTTP error. Will be retry.")
                    continue
            self.logger.error(f"HTTP error {RETRIES} times. Finish trying to connect.")
        else:
            if file:
                self.logger.error("Not implemented.")
            for _ in range(RETRIES):
                self.logger.info(f"Send GET HTTP Req. ({url=})")
                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.get(url)
                        if response.status_code == httpx.codes.OK:
                            self.logger.info(
                                f"Connection successful. ({url=}, {response.status_code=})"
                            )
                            return response
                        else:
                            self.logger.warn(
                                f"Response has error code. Will be retry. ({url=}, {response.status_code=})"
                            )
                            continue
                    except httpx.HTTPError:
                        self.logger.warn("HTTP error. Will be retry.")
                        continue
            self.logger.error(f"HTTP error {RETRIES} times. Finish trying to connect.")
            return None

    async def post(
        self, endpoint: str, audio_file=None, except_file=False
    ) -> Optional[httpx.Response]:
        url = f"{ORIGIN}{endpoint}"
        if except_file:
            if audio_file:
                files = {"file": ("record.wav", audio_file, "multipart/form-data")}
            else:
                files = None
            for _ in range(RETRIES):
                self.logger.info(f"Send POST HTTP Req. ({url=})")
                try:
                    with httpx.stream(
                        "POST",
                        url,
                        files=files,
                        timeout=120,
                    ) as response:
                        if response.status_code == httpx.codes.OK:
                            self.logger.info(
                                f"Connection successful. ({url=}, {response.status_code=})"
                            )
                            return response
                        else:
                            self.logger.warn(
                                f"Response has error code. ({url=}, {response.status_code=})"
                            )
                            continue
                except httpx.HTTPError:
                    self.logger.warn("HTTP error. Will be Retry.")
                    continue
            self.logger.error(f"HTTP error {RETRIES} times. Finish trying to connect.")
            return None
        else:
            self.logger.error("Not implemented.")

    async def wait_for_connect(self):
        self.logger.info("Try to connect API")
        led.req(LedPattern.SystemSetup)
        while True:
            is_success = await self.ping()
            if is_success:
                self.logger.info("Connected to API server.")
                led.req(LedPattern.WifiHigh)
                return
            else:
                self.logger.info("Failed to connect API server.")
                await asyncio.sleep(PING_INTERVAL)

    async def ping(self) -> bool:
        response = await self.get(endpoints[Endpoint.Ping])
        if response:
            self.logger.info("Ping success.")
            return True
        else:
            self.logger.info("Ping fail.")
            return False

    async def normal(self, audio_file) -> Optional[BytesIO]:
        led.req(LedPattern.AudioThinking)
        endpoint = endpoints[Endpoint.Normal]
        response = await self.post(endpoint, audio_file=audio_file, except_file=True)
        if response:
            response_file = BytesIO(response.read())
            led.req(LedPattern.AudioResSuccess)
            return response_file
        else:
            led.req(LedPattern.AudioResFail)
            return None

    async def messages(self, audio_file) -> bool:
        self.logger.info("Start Api.messages()")
        led.req(LedPattern.AudioUploading)
        endpoint = endpoints[Endpoint.Messages]
        response = await self.post(endpoint, audio_file=audio_file)
        if response:
            self.logger.info("Post message asuccess.")
            led.req(LedPattern.AudioResSuccess)
            return True
        else:
            self.logger.info("Post message fail.")
            led.req(LedPattern.AudioResFail)
            return False

    async def req_get_message(self) -> bool:
        endpoint = f"{endpoints[Endpoint.Messages]}/{self.message_id}"
        response = await self.get(endpoint, except_file=True)
        if response:
            self.message_file = BytesIO(response.read())
            self.logger.error("Success to get message.")
            return True
        else:
            self.logger.error("Fail to get message.")
            return False

    async def get_message(self) -> Optional[BytesIO]:
        if not self.message_file:
            response = await self.req_get_message()
            if not response:
                return None
        message_file = self.message_file
        self.notified = False
        self.message_file = None
        return message_file

    ### Notification
    async def req_ws_url(self):
        endpoint = endpoints[Endpoint.WsNegotiate]
        response = await self.get(endpoint)
        while True:
            if response:
                self.ws_url = response.json()["url"]
                return
            else:
                continue

    async def wait_for_notification(self):
        self.logger.debug("Wait for notification.")
        while not self.notified:
            await asyncio.sleep(SENSOR_INTERVAL)
        await self.req_get_message()

    async def start_listening_notification(self):
        if not self.ws_url:
            await self.req_ws_url()
        self.ws_task = asyncio.create_task(self.run_websockets())

    async def run_websockets(self):
        while True:
            try:
                async with connect(self.ws_url) as ws:
                    self.logger.info("WebSockets connected.")

                    while True:
                        self.logger.info("Listening notification.")
                        json_str = await ws.recv()
                        try:
                            json_obj = json.loads(json_str)
                            if json_obj["type"] == "message":
                                self.message_id = int(json_obj["id"])
                                self.notified = True
                                self.logger.info("Message notified.")
                            else:
                                self.logger.info(f"Other data notified.{json_str}")
                        except (json.JSONDecodeError, KeyError):
                            self.logger.error("Failed decoding received notification")

            except websockets.exceptions:
                self.logger.info("WebSockets connection closed by the server.")


api = Api()
