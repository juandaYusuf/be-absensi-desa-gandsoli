from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import select
from sqlalchemy.orm import selectinload
from config.db import engine
from fastapi import APIRouter
from models.tabel import (user_data, attendance, presence)
from schema.schemas import (AttendanceInputData)
import smtplib
from email.message import EmailMessage


router_attendance = APIRouter()

@router_attendance.post('/api/attendance/input-attendance', tags=['ATTENDANCE'])
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
            "presenting": response.presenting,
            "created_at": response.created_at
        }
    except SQLAlchemyError as e:
        print("terdapat error --> ", e)
    finally:
        conn.close()
        print("\n --> attendance berhasil | Koneksi di tutup <-- \n")

@router_attendance.get('/api/attendance/multi/user-presence-data', tags=['ATTENDANCE'])
async def attendancesMultiUser():
    try:
        conn = engine.connect()
        join_attendance_to_user_query = user_data.join(attendance, user_data.c.id == attendance.c.user_id)
        join_attendance_to_user_result = select([attendance, user_data.c.first_name, user_data.c.last_name]).select_from(join_attendance_to_user_query)
        response_attendance_to_user = conn.execute(join_attendance_to_user_result).fetchall()
        attendance_data = []
        
        for data_of_attendance in response_attendance_to_user :
            presence_datas = []
            response_presence = conn.execute(presence.select()).fetchall()
            for data_of_presence in response_presence :
                if data_of_presence.attendance_id == data_of_attendance.id :
                    presence_datas.append({
                            "id" : data_of_presence.id,
                            "attendance_id" : data_of_presence.attendance_id,
                            "presence_status" : data_of_presence.presence_status,
                            "created_at_in": data_of_presence.created_at_in,
                            "created_at_out": data_of_presence.created_at_out,
                        })
            attendance_data.append({
                "id":data_of_attendance.id ,
                "user_id": data_of_attendance.user_id,
                "first_name": data_of_attendance.first_name,
                "last_name": data_of_attendance. last_name,
                "presence": presence_datas
            })
        return attendance_data
    except SQLAlchemyError as e:
        print("terdapat error --> ", e)
    finally:
        conn.close()
        print("\n --> attendancesMultiUser berhasil >> Koneksi di tutup <-- \n")
        

@router_attendance.get('/api/attendance/single/user-presence-data/{id}', tags=['ATTENDANCE'])
async def attendancesSingleUser(id: int):
    try:
        conn = engine.connect()
        join_attendance_to_user_query = user_data.join(attendance, user_data.c.id == attendance.c.user_id)
        join_attendance_to_user_result = select([attendance, user_data.c.first_name, user_data.c.last_name]).select_from(join_attendance_to_user_query).where(attendance.c.id == id)
        response_attendance_to_user = conn.execute(join_attendance_to_user_result).fetchall()
        attendance_data = {}
        
        for data_of_attendance in response_attendance_to_user :
            presence_datas = []
            response_presence = conn.execute(presence.select()).fetchall()
            for data_of_presence in response_presence :
                if data_of_presence.attendance_id == data_of_attendance.id :
                    presence_datas.append({
                            "id" : data_of_presence.id,
                            "attendance_id" : data_of_presence.attendance_id,
                            "presence_status" : data_of_presence.presence_status,
                            "created_at_in": data_of_presence.created_at_in,
                            "created_at_out": data_of_presence.created_at_out
                        })
            attendance_data = {
                "id":data_of_attendance.id ,
                "user_id": data_of_attendance.user_id,
                "first_name": data_of_attendance.first_name,
                "last_name": data_of_attendance. last_name,
                "presence": presence_datas
            }
        return attendance_data
    except SQLAlchemyError as e:
        print("terdapat error --> ", e)
    finally:
        conn.close()
        print("\n --> attendancesSingleUser berhasil >> Koneksi di tutup <-- \n")