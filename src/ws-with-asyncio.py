

import asyncio
import websockets

async def hello():
    uri = "ws://localhost:8000/ws/hi"
    async with websockets.connect(uri) as websocket:
        await websocket.send("Hello world!")
        print(await websocket.recv())

asyncio.run(hello())
