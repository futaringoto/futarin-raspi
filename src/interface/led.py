import httpx
from enum import Enum, auto
import threading
import src.config.config as config
import src.log.log as log


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


class Led:
    def __init__(self):
        self.logger = log.get_logger("Led")

    def req(self, led_pattern: LedPattern):
        thread = threading.Thread(target=self.req_for_thread, args=(led_pattern,))
        thread.run()

    def req_for_thread(self, led_pattern: LedPattern):
        led_endpoint = led_endpoints[led_pattern]
        url = f"{ORIGIN}{led_endpoint}"
        with httpx.Client(transport=TRANSPORT) as client:
            try:
                r = client.post(url)
                if r.status_code == CODE_SUCCESS:
                    self.logger.info(f"Change LED pattern. ({led_pattern})")
                else:
                    self.logger.error(
                        f'Failed to change LED pattern ("POST {url}" r.status_code)'
                    )
            except httpx.HTTPError:
                self.logger.error(f"Failed to change LED pattern (POST {url})")


led = Led()
