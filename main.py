from fastapi import FastAPI
from routes.user_endpoint import router_user
from routes.attendance_endpoint import router_attendance
from fastapi.staticfiles import StaticFiles
from config.db import conn, engine
import signal
from fastapi.middleware.cors import CORSMiddleware 

app = FastAPI()


def kill_db_connections ():
    print('\n \033[4;32m==> KONEKSI KE DATABASE DIMATIKAN <== \n')
    conn.close()
    engine.dispose()

@app.on_event("shutdown")
def app_shutdown ():
    kill_db_connections()

def signal_handler(signum, frame):
    kill_db_connections()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# app.mount("/static", StaticFiles(directory="static"),name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins="http://localhost:3000",
    # allow_origins="https://fe-absensi-desa-gandsoli.vercel.app/",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


app.include_router(router_user)
app.include_router(router_attendance)