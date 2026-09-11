# AI Smart Ambulance Backend - Step 1

Run:

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000

Check:
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs

WebSocket:
ws://127.0.0.1:8000/ws

Planned message types:
VEHICLE_UPDATE
SIGNAL_UPDATE
AMBULANCE_STATUS
AI_ROUTE
TRAFFIC_OVERVIEW
LOG
