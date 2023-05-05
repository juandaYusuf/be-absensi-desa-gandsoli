from sqlalchemy.exc import SQLAlchemyError
from config.db import conn, engine
from fastapi import APIRouter
from models.tabel import (user_data, attendance)
from schema.schemas import (AttendanceInputData)
import smtplib
from email.message import EmailMessage


router_attendance = APIRouter()

@router_attendance.post('/attendance/input', tags=['ATTENDANCE'])
async def attendancesInput(data: AttendanceInputData):
    try:
        conn = engine.connect()
        conn.execute(attendance.insert().values(user_id = data.user_id, presenting = data.presenting))
        response = conn.execute(attendance.select().where(attendance.c.user_id == data.user_id)).first()
        user_id = response.user_id
        presenting_status = response.presenting

        # MEMBUAT SISTEMATIS MENGIRIM NOTIFIKASI KE EMAIL 
        user_data_by_attendance_user_id = conn.execute(user_data.select().where(user_data.c.id == user_id)).first()
        # user_email_reciver = user_data_by_attendance_user_id.email
        user_email_reciver = "juandmark123@gmail.com"
        user_fullname = f"{user_data_by_attendance_user_id.first_name} {user_data_by_attendance_user_id.last_name}"
        email_address_sender = "panjoelalfath@gmail.com" 
        email_password_sender = "huqhxkztjwmsbvlx" 

        msg = EmailMessage()
        msg['Subject'] = "PEMBERITAHUAN STATUS KEHADIRAN"
        msg['From'] = email_address_sender
        msg['To'] = user_email_reciver
        msg.set_content(
        f"""\
        Nama : {user_fullname}
        Status : anda dinyatakan {presenting_status}
        Message : anda dinyatakan {response.presenting}, jika anda mengalami ketidak selarasan informasi harap hubungi admin 0878765654321    
        """,
        )
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(email_address_sender, email_password_sender)
            smtp.send_message(msg)

        return {
            "id": response.id,
            "name": f"{user_data_by_attendance_user_id.first_name} {user_data_by_attendance_user_id.last_name}",
            "presenting": response.presenting
        }
    except SQLAlchemyError as e:
        print("terdapat error ==>> ", e)
    finally:
        conn.close()
        print("\n ==>> attendance berhasil >> Koneksi di tutup <<== \n")

@router_attendance.get('/attendance/users', tags=['ATTENDANCE'])
async def attendancesUser():
    try:
        conn = engine.connect()
        response = conn.execute(attendance.select()).fetchall()
        return response
    except SQLAlchemyError as e:
        print("terdapat error ==>> ", e)
    finally:
        conn.close()
        print("\n ==>> attendance berhasil >> Koneksi di tutup <<== \n")