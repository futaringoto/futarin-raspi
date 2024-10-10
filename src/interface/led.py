import httpx
import time
from enum import Enum, auto
import src.config.config as config
import src.log.log as log
import threading

RETRIES = 2
CODE_SUCCESS = 202
ORIGIN = config.get("led_server_origin")
CHECK_INTERVAL = 0.2
TRANSPORT = httpx.HTTPTransport(retries=RETRIES)


class LedPattern(Enum):
    SystemOn = auto()
    SystemSetup = auto()
    SystemOff = auto()
    SystemTurnOff = auto()
    WifiHigh = auto()
    WifiMiddle = auto()
    WifiLow = auto()
    WifiDisconnect = auto()
    AudioListening = auto()
    AudioThinking = auto()
    AudioResSuccess = auto()
    AudioResFail = auto()
    AudioUploading = auto()
    AudioReceive = auto()


led_endpoints = {
    LedPattern.SystemOn: "/system/on",
    LedPattern.SystemSetup: "/system/setup",
    LedPattern.SystemOff: "/system/off",
    LedPattern.SystemTurnOff: "/system/turn_off",
    LedPattern.WifiHigh: "/wifi/high",
    LedPattern.WifiMiddle: "/wifi/middle",
    LedPattern.WifiLow: "/wifi/low",
    LedPattern.WifiDisconnect: "/wifi/disconnect",
    LedPattern.AudioListening: "/audio/listening",
    LedPattern.AudioThinking: "/audio/thinking",
    LedPattern.AudioResSuccess: "/audio/res-success",
    LedPattern.AudioResFail: "/audio/res-fail",
    LedPattern.AudioUploading: "/audio/uploading",
    LedPattern.AudioReceive: "/audio/receive",
}


class Led(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True, name="Led")
        self.logger = log.get_logger("Led")
        self.pattern = None
        self.pattern_req = None

    def run(self):
        while True:
            if self.pattern != self.pattern_req:
                led_endpoint = led_endpoints[self.pattern_req]
                url = f"{ORIGIN}{led_endpoint}"
                with httpx.Client(transport=TRANSPORT) as client:
                    try:
                        r = client.post(url)
                        if r.status_code == CODE_SUCCESS:
                            self.pattern = self.pattern_req
                            self.logger.info(
                                f"Change LED lighting pattern. ({self.pattern})"
                            )
                        else:
                            self.logger.error(
                                f'Failed to change LED lighting pattern ("POST {url}" r.status_code)'
                            )
                    except httpx.HTTPError:
                        self.logger.error(
                            f"Failed to change LED lighting pattern (POST {url})"
                        )
            else:
                time.sleep(CHECK_INTERVAL)

    ### Send request to futarin-led server
    def req(self, led_pattern: LedPattern):
        self.pattern_req = led_pattern


led = Led()
led.start()
