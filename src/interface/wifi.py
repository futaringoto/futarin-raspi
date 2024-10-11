import asyncio
from typing import Optional


PING_INTERVAL = 10


class Wifi:
    async def wait_for_enable(self):
        while not await self.strength():
            await asyncio.sleep(PING_INTERVAL)

    # TODO
    async def strength(self) -> Optional[int]:
        return None
        # proc = await asyncio.create_subprocess_shell(
        #     ["sudo", "iw", "dev"],
        #     stdout=asyncio.subprocess.PIPE,
        #     stderr=asyncio.subprocess.PIPE,
        # )
        # stdout, stderr = await proc.communicate()
        # # TODO: stdoutからtxpowerを正規表現で取り出す


wifi = Wifi()
