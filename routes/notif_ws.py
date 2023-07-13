# from fastapi import APIRouter, WebSocket
# import threading
# import asyncio


# notif_ws = APIRouter()



# # setInterval
# def setInterval(func, interval):
#     stopped = threading.Event()

#     async def loop():
#         while not stopped.wait(interval):
#             await func()

#     loop_task = asyncio.create_task(loop())

#     def cancel():
#         stopped.set()
#         loop_task.cancel()

#     return cancel




# @notif_ws.websocket("/ws")
# async def websocket(websocket: WebSocket):
#     await websocket.accept()

#     async def send_message():
#         await websocket.send_text("Hello, WebSocket!")

#     # Set interval to send a message every 2 seconds
#     cancel_interval = setInterval(send_message, 1)

#     try:
#         while True:
#             data = await websocket.receive_text()
#             print("Received message:", data)
#     except Exception:
#         pass
#     finally:
#         cancel_interval()  # Cancel the interval when the WebSocket connection is closed