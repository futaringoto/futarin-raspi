import src.config.config as config
import json
from src.interface.led import led, LedPattern
from io import BytesIO
from src.log.log import log
import httpx
import asyncio
from websockets.asyncio.client import connect
import websockets
from typing import Literal, Optional
from enum import Enum, auto

PING_INTERVAL = 10
ORIGIN = config.get("api_origin")
VERSION = 2
ID = config.get("id")
RETRIES = 4
SENSOR_INTERVAL = 0.1
TIMEOUT = 120


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


class Response:
    def __init__(self, response):
        self.logger = log.get_logger("Response")
        try:
            self.json = response.json()
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.json = None
            self.logger.warn("Failed to get json from response.")

        try:
            self.file = BytesIO(response.content)
        except httpx.ResponseNotRead:
            self.file = None
            self.logger.warn("Failed to file json from response.")


class Api:
    def __init__(self):
        self.logger = log.get_logger("Api")
        self.logger.info("Initialized.")
        self.notified = False
        self.message_id = None
        self.ws_rul = None

    # for ping, get message
    async def get(self, endpoint: str) -> Optional[Response]:
        url = f"{ORIGIN}{endpoint}"
        for _ in range(RETRIES):
            self.logger.info(f"Send GET HTTP Req. ({url=})")
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, timeout=TIMEOUT)
                    if response.status_code == httpx.codes.OK:
                        self.logger.info(
                            f"Connection successful. ({url=}, {response.status_code=})"
                        )
                        return Response(response)
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

    async def post(self, endpoint: str, audio_file=None) -> Optional[Response]:
        url = f"{ORIGIN}{endpoint}"
        if audio_file:
            files = {"file": ("record.wav", audio_file, "multipart/form-data")}
        else:
            files = None

        for _ in range(RETRIES):
            self.logger.info(f"Send GET HTTP Req. ({url=})")
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, files=files, timeout=TIMEOUT)
                    if response.status_code == httpx.codes.OK:
                        self.logger.info(
                            f"Connection successful. ({url=}, {response.status_code=})"
                        )
                        return Response(response)
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

    async def wait_for_connect(self) -> Literal[True]:
        self.logger.info("Try to connect API")
        led.req(LedPattern.SystemSetup)
        while True:
            is_success = await self.ping()
            if is_success:
                self.logger.info("Connected to API server.")
                led.req(LedPattern.WifiHigh)
                return True
            else:
                self.logger.info("Failed to connect API server. Retry.")
                await asyncio.sleep(PING_INTERVAL)

    async def ping(self) -> bool:
        response = await self.get(endpoints[Endpoint.Ping])
        if response is not None:
            self.logger.info("Ping success.")
            return True
        else:
            self.logger.info("Ping fail.")
            return False

    async def normal(self, audio_file) -> Optional[BytesIO]:
        led.req(LedPattern.ApiProcessing)
        endpoint = endpoints[Endpoint.Normal]
        response = await self.post(endpoint, audio_file=audio_file)
        if response is not None:
            response_file = response.file
            led.req(LedPattern.ApiSuccess)
            return response_file
        else:
            led.req(LedPattern.ApiFail)
            return None

    async def messages(self, audio_file) -> bool:
        self.logger.info("Start Api.messages()")
        led.req(LedPattern.ApiPostingMessage)
        endpoint = endpoints[Endpoint.Messages]
        response = await self.post(endpoint, audio_file=audio_file)
        if response is None:
            self.logger.info("Post message fail.")
            led.req(LedPattern.ApiFail)
            return False
        else:
            self.logger.info("Post message success.")
            led.req(LedPattern.ApiSuccess)
            return True

    async def req_get_message(self) -> bool:
        endpoint = f"{endpoints[Endpoint.Messages]}/{self.message_id}"
        response = await self.get(endpoint)
        if response is not None:
            self.message_file = response.file
            self.logger.error("Success to get message.")
            return True
        else:
            self.logger.error("Fail to get message.")
            return False

    async def get_message(self) -> Optional[BytesIO]:
        if not self.message_file:
            response = await self.req_get_message()
            if response is None:
                return None
        message_file = self.message_file
        self.notified = False
        self.message_file = None
        return message_file

    ### Notification
    async def init_notification_connection(self) -> Literal[True]:
        self.logger.info("Get WebSocket url.")
        endpoint = endpoints[Endpoint.WsNegotiate]
        response = await self.post(endpoint)
        while True:
            try:
                if response is None or response.json is None:
                    continue
                else:
                    self.ws_url = response.json["url"]
                    return True
            except KeyError:
                self.logger.error("Key('url') not found")
                continue

    async def wait_for_notification(self):
        self.logger.debug("Wait for notification.")
        while not self.notified:
            await asyncio.sleep(SENSOR_INTERVAL)
        await self.req_get_message()

    async def start_listening_notifications(self):
        await self.init_notification_connection()
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

            except websockets.exceptions.ConnectionClosed:
                self.logger.info("WebSockets connection closed by the server.")


api = Api()
