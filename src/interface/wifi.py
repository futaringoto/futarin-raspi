import asyncio

PING_INTERVAL = 10


async def wait_for_connect():
    await asyncio.sleep(PING_INTERVAL)
    pass

async def ping():
