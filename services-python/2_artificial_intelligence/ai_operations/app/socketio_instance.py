import socketio
from fastapi import FastAPI

app = FastAPI(title="Chatbot Middleware API")
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
sio_app = socketio.ASGIApp(socketio_server=sio, other_asgi_app=app)