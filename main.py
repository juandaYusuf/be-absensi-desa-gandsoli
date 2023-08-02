# ===================================================
# aplikasi backend rusak ketika zona waktu dalam operating sistem di ubah
# maka perlu pnedekatan seperti baris kode dibawah ini sebelum core dari aplikasi ini dijalankan
import os
os.environ['TZ'] = 'Asia/Jakarta'
# ===================================================


from fastapi import FastAPI
from endpoint.endpoints import (
    user, 
    attendance, 
    attendance_rules, 
    qrcode_data, user_scanning,
    detail_scanned, personal_leave,
    user_permission,
    user_role
    # notifs_ws
    )
from config.db import conn, engine
import signal
from fastapi.middleware.cors import CORSMiddleware 
# from fastapi.staticfiles import StaticFiles

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
    # allow_origins="http//127.0.0.1/",
    # allow_origins="https://fe-absensi-desa-gandsoli.vercel.app/",
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


app.include_router(user)
app.include_router(attendance)
app.include_router(attendance_rules)
app.include_router(qrcode_data)
app.include_router(user_scanning)
app.include_router(detail_scanned)
app.include_router(personal_leave)
app.include_router(user_permission)
app.include_router(user_role)
# app.include_router(notifs_ws)
