import asyncio
import websockets
import json

async def test_ws():
    try:
        async with websockets.connect('ws://127.0.0.1:8000/ws') as ws:
            print('Connected!')
            msg = await ws.recv()
            data = json.loads(msg)
            print('Connected! Type:', data['type'])
            
            for i in range(3):
                msg = await ws.recv()
                data = json.loads(msg)
                print('Event:', data['type'])
    except Exception as e:
        print('Error:', e)

if __name__ == "__main__":
    import asyncio
    import websockets
    import json
    asyncio.run(test_ws())