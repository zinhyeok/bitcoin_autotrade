import websockets
import asyncio
import json


async def upbit_websocket():
    wb = await websockets.connect(
        "wss://api.upbit.com/websocket/v1", ping_interval=None
    )
    await wb.send(
        json.dumps(
            [
                {"ticket": "test"},
                {"type": "trade", "codes": ["KRW-BTC", "BTC-BCH", "KRW-AQT"]},
                {"format": "SIMPLE"},
            ]
        )
    )

    while True:
        if wb.open:
            result = await wb.recv()
            result = json.loads(result)
            print(result)
        else:
            print("연결 안됨! 또는 연결 끊김")


loop = asyncio.get_event_loop()
asyncio.ensure_future(upbit_websocket())
loop.run_forever()
