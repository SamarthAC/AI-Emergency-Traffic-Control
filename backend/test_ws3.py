import asyncio
import websockets
import json

async def test_ws():
    try:
        async with websockets.connect('ws://127.0.0.1:8000/ws', ping_interval=20, ping_timeout=20) as ws:
            print('Connected')
            msg = await ws.recv()
            data = json.loads(msg)
            print('Initial:', data['type'])
            
            for i in range(3):
                msg = await ws.recv()
                data = json.loads(msg)
                print('Event:', data['type'])
    except Exception as e:
        print('Error:', e)

if __name__ == "__main__":
    asyncio.run(test_ws())