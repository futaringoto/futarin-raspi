import src.interface.wifi as wifi
import asyncio
import src.interface.led as led

### Alias
ct = asyncio.create_task


async def main():
    wait_for_wifi_task = ct(wifi.wait_for_connect())
    led.set(led.LedPatterns.Wifi)


if __name__ == "__main__":
    asyncio.run(main())
