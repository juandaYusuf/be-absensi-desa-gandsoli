from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import select
from config.db import engine
from fastapi import APIRouter
from models.tabel import user_data, attendance, presence, user_has_scanned_in,personal_leave, permission
from schema.schemas import AttendanceInputData, userSick
import smtplib
from email.message import EmailMessage
import datetime
import pytz
import calendar
import time

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
        # return response_attendance_to_user
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
                            "working": data_of_presence.working,
                            "descriptions": data_of_presence.descriptions,
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


@router_attendance.get('/api/attendance/single/detail-presence/{id}/{set_year}', tags=['ATTENDANCE'])
async def attendancesDetailPresence(id: int, set_year: int):
    def efective_works(year):
        month_names = ["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"]
        total_efective_works = []
        result = []
        for month in range(1, 13):
            _, days = calendar.monthrange(year, month)
            total_efective_works.append(sum(1 for day in range(1, days + 1) if calendar.weekday(year, month, day) < 5))
        
        for i, works in enumerate(total_efective_works) :
            result.append({
                "month": month_names[i],
                "efective_works": works
            })
            
        return result

    try:
        conn = engine.connect()
        get_efective_works = efective_works(set_year)
        month_names = ["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"]
        join_query = user_data.join(attendance, user_data.c.id == attendance.c.user_id).join(presence, presence.c.attendance_id == attendance.c.id)
        join_query_result = select([attendance, user_data.c.first_name, user_data.c.last_name, presence.c.presence_status, presence.c.created_at_in, presence.c.created_at_out, presence.c.descriptions]).select_from(join_query).where(attendance.c.user_id == id)
        response_join = conn.execute(join_query_result).fetchall()
        efective_works_from_user = []
        
        hadir = 0
        result_hadir = [{   
                    "month": "Januari",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Februari",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Maret",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "April",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Mei",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Juni",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Juli",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Agustus",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "September",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Oktober",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "November",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Desember",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                }]
        
        alfa = 0
        result_alfa = [{   
                    "month": "Januari",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Februari",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Maret",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "April",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Mei",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Juni",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Juli",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Agustus",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "September",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Oktober",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "November",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Desember",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                }]
        
        izin = 0
        result_izin =  [{   
                    "month": "Januari",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Februari",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Maret",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "April",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Mei",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Juni",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Juli",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Agustus",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "September",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Oktober",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "November",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Desember",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                }]
        
        cuti = 0
        result_cuti =  [{   
                    "month": "Januari",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Februari",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Maret",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "April",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Mei",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Juni",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Juli",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Agustus",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "September",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Oktober",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "November",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Desember",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                }]
        
        sakit = 0
        result_sakit = [{   
                    "month": "Januari",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Februari",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Maret",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "April",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Mei",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Juni",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Juli",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Agustus",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "September",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Oktober",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "November",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                },
                {   
                    "month": "Desember",
                    "efective_work": 0,
                    "total": 0,
                    "percentage": 0,
                }]
        
        for i, month in enumerate(month_names) :
            for datas in response_join :
                # !JANUARI
                if month == "Januari":
                    for efct_wrk in get_efective_works:
                        if efct_wrk['month'] == month:
                            result_hadir[i]['efective_work'] = efct_wrk['efective_works']
                            # !Hadir ===============================================
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "hadir" and set_year == datas.created_at_in.year:
                                hadir += 1
                                result_hadir[i]['total'] = hadir
                                result_hadir[i]['percentage'] = hadir / efct_wrk['efective_works'] * 100
                        
                            # *Izin ===============================================
                            result_izin[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "izin" and set_year == datas.created_at_in.year:
                                izin += 1
                                result_izin[i]['total'] = izin
                                result_izin[i]['percentage'] = izin / efct_wrk['efective_works'] * 100
                        
                            # ?Alfa ===============================================
                            result_alfa[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "alfa" and set_year == datas.created_at_in.year:
                                alfa += 1
                                result_alfa[i]['total'] = alfa
                                result_alfa[i]['percentage'] = alfa / efct_wrk['efective_works'] * 100
                        
                            # Curi ===============================================
                            result_cuti[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "cuti" and set_year == datas.created_at_in.year:
                                cuti += 1
                                result_cuti[i]['total'] = cuti
                                result_cuti[i]['percentage'] = cuti / efct_wrk['efective_works'] * 100
                            
                            # Sakit ===============================================
                            result_sakit[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "sakit" and set_year == datas.created_at_in.year:
                                sakit += 1
                                result_sakit[i]['total'] = sakit
                                result_sakit[i]['percentage'] = sakit / efct_wrk['efective_works'] * 100
                            
                # !FEBRUARI
                if month == "Februari":
                    for efct_wrk in get_efective_works:
                        if efct_wrk['month'] == month:
                            result_hadir[i]['efective_work'] = efct_wrk['efective_works']
                            # !Hadir ===============================================
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "hadir" and set_year == datas.created_at_in.year:
                                hadir += 1
                                result_hadir[i]['total'] = hadir
                                result_hadir[i]['percentage'] = hadir / efct_wrk['efective_works'] * 100
                        
                            # *Izin ===============================================
                            result_izin[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "izin" and set_year == datas.created_at_in.year:
                                izin += 1
                                result_izin[i]['total'] = izin
                                result_izin[i]['percentage'] = izin / efct_wrk['efective_works'] * 100
                        
                            # ?Alfa ===============================================
                            result_alfa[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "alfa" and set_year == datas.created_at_in.year:
                                alfa += 1
                                result_alfa[i]['total'] = alfa
                                result_alfa[i]['percentage'] = alfa / efct_wrk['efective_works'] * 100
                        
                            # Curi ===============================================
                            result_cuti[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "cuti" and set_year == datas.created_at_in.year:
                                cuti += 1
                                result_cuti[i]['total'] = cuti
                                result_cuti[i]['percentage'] = cuti / efct_wrk['efective_works'] * 100
                                
                            # Sakit ===============================================
                            result_sakit[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "sakit" and set_year == datas.created_at_in.year:
                                sakit += 1
                                result_sakit[i]['total'] = sakit
                                result_sakit[i]['percentage'] = sakit / efct_wrk['efective_works'] * 100
                
                # !MARET
                if month == "Maret":
                    for efct_wrk in get_efective_works:
                        if efct_wrk['month'] == month:
                            result_hadir[i]['efective_work'] = efct_wrk['efective_works']
                            # !Hadir ===============================================
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "hadir" and set_year == datas.created_at_in.year:
                                hadir += 1
                                result_hadir[i]['total'] = hadir
                                result_hadir[i]['percentage'] = hadir / efct_wrk['efective_works'] * 100
                        
                            # *Izin ===============================================
                            result_izin[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "izin" and set_year == datas.created_at_in.year:
                                izin += 1
                                result_izin[i]['total'] = izin
                                result_izin[i]['percentage'] = izin / efct_wrk['efective_works'] * 100
                        
                            # ?Alfa ===============================================
                            result_alfa[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "alfa" and set_year == datas.created_at_in.year:
                                alfa += 1
                                result_alfa[i]['total'] = alfa
                                result_alfa[i]['percentage'] = alfa / efct_wrk['efective_works'] * 100
                        
                            # Curi ===============================================
                            result_cuti[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "cuti" and set_year == datas.created_at_in.year:
                                cuti += 1
                                result_cuti[i]['total'] = cuti
                                result_cuti[i]['percentage'] = cuti / efct_wrk['efective_works'] * 100
                            
                            # Sakit ===============================================
                            result_sakit[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "sakit" and set_year == datas.created_at_in.year:
                                sakit += 1
                                result_sakit[i]['total'] = sakit
                                result_sakit[i]['percentage'] = sakit / efct_wrk['efective_works'] * 100
                
                # !APRIL
                if month == "April":
                    for efct_wrk in get_efective_works:
                        if efct_wrk['month'] == month:
                            result_hadir[i]['efective_work'] = efct_wrk['efective_works']
                            # !Hadir ===============================================
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "hadir" and set_year == datas.created_at_in.year:
                                hadir += 1
                                result_hadir[i]['total'] = hadir
                                result_hadir[i]['percentage'] = hadir / efct_wrk['efective_works'] * 100
                        
                            # *Izin ===============================================
                            result_izin[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "izin" and set_year == datas.created_at_in.year:
                                izin += 1
                                result_izin[i]['total'] = izin
                                result_izin[i]['percentage'] = izin / efct_wrk['efective_works'] * 100
                        
                            # ?Alfa ===============================================
                            result_alfa[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "alfa" and set_year == datas.created_at_in.year:
                                alfa += 1
                                result_alfa[i]['total'] = alfa
                                result_alfa[i]['percentage'] = alfa / efct_wrk['efective_works'] * 100
                        
                            # Curi ===============================================
                            result_cuti[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "cuti" and set_year == datas.created_at_in.year:
                                cuti += 1
                                result_cuti[i]['total'] = cuti
                                result_cuti[i]['percentage'] = cuti / efct_wrk['efective_works'] * 100
                            
                            # Sakit ===============================================
                            result_sakit[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "sakit" and set_year == datas.created_at_in.year:
                                sakit += 1
                                result_sakit[i]['total'] = sakit
                                result_sakit[i]['percentage'] = sakit / efct_wrk['efective_works'] * 100
                
                
                # !MEI
                if month == "Mei":
                    for efct_wrk in get_efective_works:
                        if efct_wrk['month'] == month:
                            result_hadir[i]['efective_work'] = efct_wrk['efective_works']
                            # !Hadir ===============================================
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "hadir" and set_year == datas.created_at_in.year:
                                hadir += 1
                                result_hadir[i]['total'] = hadir
                                result_hadir[i]['percentage'] = hadir / efct_wrk['efective_works'] * 100
                        
                            # *Izin ===============================================
                            result_izin[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "izin" and set_year == datas.created_at_in.year:
                                izin += 1
                                result_izin[i]['total'] = izin
                                result_izin[i]['percentage'] = izin / efct_wrk['efective_works'] * 100
                        
                            # ?Alfa ===============================================
                            result_alfa[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "alfa" and set_year == datas.created_at_in.year:
                                alfa += 1
                                result_alfa[i]['total'] = alfa
                                result_alfa[i]['percentage'] = alfa / efct_wrk['efective_works'] * 100
                        
                            # Curi ===============================================
                            result_cuti[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "cuti" and set_year == datas.created_at_in.year:
                                cuti += 1
                                result_cuti[i]['total'] = cuti
                                result_cuti[i]['percentage'] = cuti / efct_wrk['efective_works'] * 100
                            
                            # Sakit ===============================================
                            result_sakit[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "sakit" and set_year == datas.created_at_in.year:
                                sakit += 1
                                result_sakit[i]['total'] = sakit
                                result_sakit[i]['percentage'] = sakit / efct_wrk['efective_works'] * 100
                
                
                # !JUNI
                if month == "Juni":
                    for efct_wrk in get_efective_works:
                        if efct_wrk['month'] == month:
                            result_hadir[i]['efective_work'] = efct_wrk['efective_works']
                            # !Hadir ===============================================
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "hadir" and set_year == datas.created_at_in.year:
                                hadir += 1
                                result_hadir[i]['total'] = hadir
                                result_hadir[i]['percentage'] = hadir / efct_wrk['efective_works'] * 100
                        
                            # *Izin ===============================================
                            result_izin[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "izin" and set_year == datas.created_at_in.year:
                                izin += 1
                                result_izin[i]['total'] = izin
                                result_izin[i]['percentage'] = izin / efct_wrk['efective_works'] * 100
                        
                            # ?Alfa ===============================================
                            result_alfa[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "alfa" and set_year == datas.created_at_in.year:
                                alfa += 1
                                result_alfa[i]['total'] = alfa
                                result_alfa[i]['percentage'] = alfa / efct_wrk['efective_works'] * 100
                        
                            # Curi ===============================================
                            result_cuti[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "cuti" and set_year == datas.created_at_in.year:
                                cuti += 1
                                result_cuti[i]['total'] = cuti
                                result_cuti[i]['percentage'] = cuti / efct_wrk['efective_works'] * 100
                            
                            # Sakit ===============================================
                            result_sakit[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "sakit" and set_year == datas.created_at_in.year:
                                sakit += 1
                                result_sakit[i]['total'] = sakit
                                result_sakit[i]['percentage'] = sakit / efct_wrk['efective_works'] * 100
                
                
                # !JULI
                if month == "Juli":
                    for efct_wrk in get_efective_works:
                        if efct_wrk['month'] == month:
                            result_hadir[i]['efective_work'] = efct_wrk['efective_works']
                            # !Hadir ===============================================
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "hadir" and set_year == datas.created_at_in.year:
                                hadir += 1
                                result_hadir[i]['total'] = hadir
                                result_hadir[i]['percentage'] = hadir / efct_wrk['efective_works'] * 100
                        
                            # *Izin ===============================================
                            result_izin[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "izin" and set_year == datas.created_at_in.year:
                                izin += 1
                                result_izin[i]['total'] = izin
                                result_izin[i]['percentage'] = izin / efct_wrk['efective_works'] * 100
                        
                            # ?Alfa ===============================================
                            result_alfa[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "alfa" and set_year == datas.created_at_in.year:
                                alfa += 1
                                result_alfa[i]['total'] = alfa
                                result_alfa[i]['percentage'] = alfa / efct_wrk['efective_works'] * 100
                        
                            # Curi ===============================================
                            result_cuti[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "cuti" and set_year == datas.created_at_in.year:
                                cuti += 1
                                result_cuti[i]['total'] = cuti
                                result_cuti[i]['percentage'] = cuti / efct_wrk['efective_works'] * 100
                                
                            # Sakit ===============================================
                            result_sakit[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "sakit" and set_year == datas.created_at_in.year:
                                sakit += 1
                                result_sakit[i]['total'] = sakit
                                result_sakit[i]['percentage'] = sakit / efct_wrk['efective_works'] * 100
                
                
                # !AGUSTUS
                if month == "Agustus":
                    for efct_wrk in get_efective_works:
                        if efct_wrk['month'] == month:
                            result_hadir[i]['efective_work'] = efct_wrk['efective_works']
                            # !Hadir ===============================================
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "hadir" and set_year == datas.created_at_in.year:
                                hadir += 1
                                result_hadir[i]['total'] = hadir
                                result_hadir[i]['percentage'] = hadir / efct_wrk['efective_works'] * 100
                        
                            # *Izin ===============================================
                            result_izin[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "izin" and set_year == datas.created_at_in.year:
                                izin += 1
                                result_izin[i]['total'] = izin
                                result_izin[i]['percentage'] = izin / efct_wrk['efective_works'] * 100
                        
                            # ?Alfa ===============================================
                            result_alfa[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "alfa" and set_year == datas.created_at_in.year:
                                alfa += 1
                                result_alfa[i]['total'] = alfa
                                result_alfa[i]['percentage'] = alfa / efct_wrk['efective_works'] * 100
                        
                            # Curi ===============================================
                            result_cuti[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "cuti" and set_year == datas.created_at_in.year:
                                cuti += 1
                                result_cuti[i]['total'] = cuti
                                result_cuti[i]['percentage'] = cuti / efct_wrk['efective_works'] * 100
                                
                            # Sakit ===============================================
                            result_sakit[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "sakit" and set_year == datas.created_at_in.year:
                                sakit += 1
                                result_sakit[i]['total'] = sakit
                                result_sakit[i]['percentage'] = sakit / efct_wrk['efective_works'] * 100
                        
                
                
                
                # !SEPTEMBER
                if month == "September":
                    for efct_wrk in get_efective_works:
                        if efct_wrk['month'] == month:
                            result_hadir[i]['efective_work'] = efct_wrk['efective_works']
                            # !Hadir ===============================================
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "hadir" and set_year == datas.created_at_in.year:
                                hadir += 1
                                result_hadir[i]['total'] = hadir
                                result_hadir[i]['percentage'] = hadir / efct_wrk['efective_works'] * 100
                        
                            # *Izin ===============================================
                            result_izin[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "izin" and set_year == datas.created_at_in.year:
                                izin += 1
                                result_izin[i]['total'] = izin
                                result_izin[i]['percentage'] = izin / efct_wrk['efective_works'] * 100
                        
                            # ?Alfa ===============================================
                            result_alfa[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "alfa" and set_year == datas.created_at_in.year:
                                alfa += 1
                                result_alfa[i]['total'] = alfa
                                result_alfa[i]['percentage'] = alfa / efct_wrk['efective_works'] * 100
                        
                            # Curi ===============================================
                            result_cuti[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "cuti" and set_year == datas.created_at_in.year:
                                cuti += 1
                                result_cuti[i]['total'] = cuti
                                result_cuti[i]['percentage'] = cuti / efct_wrk['efective_works'] * 100
                                
                            # Sakit ===============================================
                            result_sakit[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "sakit" and set_year == datas.created_at_in.year:
                                sakit += 1
                                result_sakit[i]['total'] = sakit
                                result_sakit[i]['percentage'] = sakit / efct_wrk['efective_works'] * 100
                
                
                # !OKTOBER
                if month == "Oktober":
                    for efct_wrk in get_efective_works:
                        if efct_wrk['month'] == month:
                            result_hadir[i]['efective_work'] = efct_wrk['efective_works']
                            # !Hadir ===============================================
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "hadir" and set_year == datas.created_at_in.year:
                                hadir += 1
                                result_hadir[i]['total'] = hadir
                                result_hadir[i]['percentage'] = hadir / efct_wrk['efective_works'] * 100
                        
                            # *Izin ===============================================
                            result_izin[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "izin" and set_year == datas.created_at_in.year:
                                izin += 1
                                result_izin[i]['total'] = izin
                                result_izin[i]['percentage'] = izin / efct_wrk['efective_works'] * 100
                        
                            # ?Alfa ===============================================
                            result_alfa[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "alfa" and set_year == datas.created_at_in.year:
                                alfa += 1
                                result_alfa[i]['total'] = alfa
                                result_alfa[i]['percentage'] = alfa / efct_wrk['efective_works'] * 100
                        
                            # Curi ===============================================
                            result_cuti[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "cuti" and set_year == datas.created_at_in.year:
                                cuti += 1
                                result_cuti[i]['total'] = cuti
                                result_cuti[i]['percentage'] = cuti / efct_wrk['efective_works'] * 100
                                
                            # Sakit ===============================================
                            result_sakit[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "sakit" and set_year == datas.created_at_in.year:
                                sakit += 1
                                result_sakit[i]['total'] = sakit
                                result_sakit[i]['percentage'] = sakit / efct_wrk['efective_works'] * 100
                
                
                # !NOVEMBER
                if month == "November":
                    for efct_wrk in get_efective_works:
                        if efct_wrk['month'] == month:
                            result_hadir[i]['efective_work'] = efct_wrk['efective_works']
                            # !Hadir ===============================================
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "hadir" and set_year == datas.created_at_in.year:
                                hadir += 1
                                result_hadir[i]['total'] = hadir
                                result_hadir[i]['percentage'] = hadir / efct_wrk['efective_works'] * 100
                        
                            # *Izin ===============================================
                            result_izin[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "izin" and set_year == datas.created_at_in.year:
                                izin += 1
                                result_izin[i]['total'] = izin
                                result_izin[i]['percentage'] = izin / efct_wrk['efective_works'] * 100
                        
                            # ?Alfa ===============================================
                            result_alfa[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "alfa" and set_year == datas.created_at_in.year:
                                alfa += 1
                                result_alfa[i]['total'] = alfa
                                result_alfa[i]['percentage'] = alfa / efct_wrk['efective_works'] * 100
                        
                            # Curi ===============================================
                            result_cuti[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "cuti" and set_year == datas.created_at_in.year:
                                cuti += 1
                                result_cuti[i]['total'] = cuti
                                result_cuti[i]['percentage'] = cuti / efct_wrk['efective_works'] * 100
                                
                            # Sakit ===============================================
                            result_sakit[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "sakit" and set_year == datas.created_at_in.year:
                                sakit += 1
                                result_sakit[i]['total'] = sakit
                                result_sakit[i]['percentage'] = sakit / efct_wrk['efective_works'] * 100
                
                
                # !DESEMBER
                if month == "Desember":
                    for efct_wrk in get_efective_works:
                        if efct_wrk['month'] == month:
                            result_hadir[i]['efective_work'] = efct_wrk['efective_works']
                            # !Hadir ===============================================
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "hadir" and set_year == datas.created_at_in.year:
                                hadir += 1
                                result_hadir[i]['total'] = hadir
                                result_hadir[i]['percentage'] = hadir / efct_wrk['efective_works'] * 100

                            # *Izin ===============================================
                            result_izin[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "izin" and set_year == datas.created_at_in.year:
                                izin += 1
                                result_izin[i]['total'] = izin
                                result_izin[i]['percentage'] = izin / efct_wrk['efective_works'] * 100

                            # ?Alfa ===============================================
                            result_alfa[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "alfa" and set_year == datas.created_at_in.year:
                                alfa += 1
                                result_alfa[i]['total'] = alfa
                                result_alfa[i]['percentage'] = alfa / efct_wrk['efective_works'] * 100

                            # Curi ===============================================
                            result_cuti[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "cuti" and set_year == datas.created_at_in.year:
                                cuti += 1
                                result_cuti[i]['total'] = cuti
                                result_cuti[i]['percentage'] = cuti / efct_wrk['efective_works'] * 100
                                
                            # Sakit ===============================================
                            result_sakit[i]['efective_work'] = efct_wrk['efective_works']
                            if month == month_names[datas.created_at_in.month -1] and datas.presence_status == "sakit" and set_year == datas.created_at_in.year:
                                sakit += 1
                                result_sakit[i]['total'] = sakit
                                result_sakit[i]['percentage'] = sakit / efct_wrk['efective_works'] * 100
                        
        return {
            "hadir":result_hadir,
            "izin": result_izin,
            "alfa": result_alfa,
            "cuti": result_cuti,
            "sakit": result_sakit,
            }
    except SQLAlchemyError as e:
        print("terdapat error --> ", e)
    finally:
        conn.close()
        print("\n --> attendancesSingleUser berhasil >> Koneksi di tutup <-- \n")



@router_attendance.get('/api/attendance/multi/detail-presence/{set_year}/{set_month}', tags=['ATTENDANCE'])
async def multiAttendanceDetailPresent(set_year: int, set_month: int):
    
    def dayAndDate(month, year):
        # Mendapatkan jumlah hari dalam bulan
        total_day = calendar.monthrange(year, month)[1]

        # Mendapatkan nama-nama hari dan bulan dalam bahasa Indonesia
        days_names = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
        month_names = ["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"]
        
        
        # Menggunakan calendar untuk mendapatkan indeks hari pertama dalam bulan
        first_day_index = calendar.weekday(year, month, 1)

        # Membuat list untuk menyimpan nama hari dan tanggal
        result = []

    # Mengisi list dengan nama hari dan tanggal dalam bulan
        for date in range(1, total_day+1):
            day_index = (first_day_index + date - 1) % 7
            day = days_names[day_index]
            name_of_month = month_names[month - 1]
            months = month
            years = year
            result.append((day, date, months, years, name_of_month))
            
            
        return result
    
    try:
        conn = engine.connect()
        days_and_dates = dayAndDate(set_month, set_year)
        
        # get user data ========================================
        Join_query = attendance.join(user_data, attendance.c.user_id == user_data.c.id)
        result_join = select([user_data.c.first_name, user_data.c.last_name, attendance.c.user_id, attendance.c.id]).select_from(Join_query)
        execute_result = conn.execute(result_join).fetchall()
        # return execute_result
        # ======================================================
        
        # get presence data ========================================
        presence_datas = conn.execute(presence.select()).fetchall()
        # ==========================================================
        total_hadir = []
        total_izin = []
        total_alfa = []
        total_cuti = []
        result_presence_datas = []
        result_user_datas = []
        # return execute_result
        
        
        
        for prsnc in presence_datas :
            for date_day in days_and_dates :
                if date_day[1] == prsnc.created_at_in.day and prsnc.created_at_in.month == date_day[2] and  prsnc.created_at_in.year == date_day[3]:
                    result_presence_datas.append({
                        'attendance_id': prsnc.attendance_id,
                        'day': date_day[0],
                        'date': date_day[1],
                        'month': date_day[2],
                        'year': date_day[3],
                        'status': prsnc.presence_status
                        })
                    
            
        for attndcs in execute_result :
            total_hadir = [result_presence_datas['status'] for result_presence_datas in result_presence_datas if result_presence_datas['attendance_id'] == attndcs.id and result_presence_datas['status'] == "hadir"]
            total_izin = [result_presence_datas['status'] for result_presence_datas in result_presence_datas if result_presence_datas['attendance_id'] == attndcs.id and result_presence_datas['status'] == "izin"]
            total_alfa = [result_presence_datas['status'] for result_presence_datas in result_presence_datas if result_presence_datas['attendance_id'] == attndcs.id and result_presence_datas['status'] == "alfa"]
            total_cuti = [result_presence_datas['status'] for result_presence_datas in result_presence_datas if result_presence_datas['attendance_id'] == attndcs.id and result_presence_datas['status'] == "cuti"]
            
            result_user_datas.append({
                'full_name': f'{attndcs.first_name} {attndcs.last_name}',
                'total_hadir': len(total_hadir),
                'total_izin': len(total_izin),
                'total_alfa': len(total_alfa),
                'total_cuti': len(total_cuti),
                'presence' : [result_presence_datas for result_presence_datas in result_presence_datas if result_presence_datas['attendance_id'] == attndcs.id]
            })
        
        return result_user_datas
        
    except SQLAlchemyError as e :
        print("terdapat error --> ", e)
    finally :
        conn.close()
        print("\n --> 'multiAttendanceDetailPresent' berhasil >> Koneksi di tutup <-- \n")
    



#! Anggap user yang tidak melakukan scan_in sebagai user yang tidak hadir (Endpoin ini di hit ketika waktu keluar kerja telah berakhir)
# @router_attendance.post('/api/attendance/multi/auto-set-user-as-alfa/', tags=['ATTENDANCE'])
# async def userNotScannedin():
#     try :
        
#         conn = engine.connect()
#         # cek tanggal sekarang kemudian anggap user yang tidak melakukan scann_in sebagai user yang tidak hadir (ALFA)
#         current_date = datetime.date.today()
#         #? ================================ ALGORITHM =======================================
#         # Dapatkan data user yang sudah melakukan scan hari ini
#         # Dapatkan seluruh user
#         # kemudian cek user mana yang tidak melakukan scann_in
#         # cek apakah ada user yang cuti jika ada insert cuti ke tabel presence
#         # insert yang tidak hadir ke tabel presence
#         #? ==================================================================================
        
#         get_data_from_attendance = conn.execute(attendance.select()).fetchall()
#         get_user_scanned_in = conn.execute(user_has_scanned_in.select().where(user_has_scanned_in.c.created_at > current_date)).fetchall()
        
        
        
#         # variabel untuk menyimpan user_id
#         # karena 'get_data_from_attendance' dan 'get_user_scanned_in' mengembalikan object dalam array
#         # jadi harus ditampung dulu pada variable agar value dari array tidak bertipe data object
#         only_user_id_of_attendance = []
#         only_user_id_of_scanned_in = []
#         only_attendance_id = []
#         user_id_has_scanned_in_today = []
#         user_id_do_not_scan_in_today = []
#         attendance_id_do_not_scan_in_today = []
        
        
        
#         #* ===========================================================================
#         # Loop seluruh isi data dari tabel user_data (var 'get_data_from_attendance') 
#         # dan ambil 'user_id' nya saja
#         for user_id_of_attendance in get_data_from_attendance :
#             only_user_id_of_attendance.append(user_id_of_attendance.user_id)
#         #* ===========================================================================
        
        
        
#         #* ===========================================================================
#         # Loop seleuruh isi data dari tabel attendance (var 'get_data_from_attendance') 
#         # dan ambil 'user_id' nya saja
#         for id_of_attendance in get_data_from_attendance :
#             only_attendance_id.append(id_of_attendance.id)
#         #* ===========================================================================
        
        
        
#         #* ===========================================================================
#         # Loop seleuruh isi data dari tabel user_has_scanned_in (var 'get_user_scanned_in') 
#         # dan ambil 'user_id' nya saja
#         for user_id_of_scanned_in in get_user_scanned_in :
#             only_user_id_of_scanned_in.append(user_id_of_scanned_in.user_id)
#         #* ===========================================================================
        
        
#         #* ===========================================================================
#         # Loop seluruh user_id dan cek user dengan id berapa yang tidak melakukan scan_in 
#         for user_id in only_user_id_of_attendance :
#             if user_id not in only_user_id_of_scanned_in :
#                 # kondisi dimana user yang tidak melakukan scan_in dan yang akan di anggap ALFA
#                 attendance_id = conn.execute(attendance.select().where(attendance.c.user_id == user_id, )).first()
#                 user_id_do_not_scan_in_today.append({
#                     "attendance_id": attendance_id.id,
#                     "user_id" : attendance_id.user_id
#                     })
#             else :
#                 # kondisi dimana user yang melakukan scan_in (HADIR)
#                 # tidak akan melakukan apapunm pada kondisi ini
#                 # ini diimplementasikan karena untuk mempermudah jika sistem ini akan dikembangkan lagi
#                 attendance_id = conn.execute(attendance.select().where(attendance.c.user_id == user_id)).first()
#                 user_id_has_scanned_in_today.append({
#                     "attendance_id": attendance_id.id,
#                     "user_id" : attendance_id.user_id
#                     })
#         #* ===========================================================================
        
        
        
#         #! ================================ Nyatakan tidak hadir ================================
#         # Loop lagi user yang tidak melakukan scan_in pada (var 'user_id_do_not_scan_in_today')
#         # kemudian insert ke tabel 'presence' untuk dinyatakan tidak hadir
#         for absent_users in user_id_do_not_scan_in_today :
#             attendance_id = absent_users["attendance_id"] # variabel ini untuk mengambil value dari objek yang terdapat dalam array
#             user_id = absent_users["user_id"] # variabel ini untuk mengambil value dari objek yang terdapat dalam array
#             # Sebelum menyatakan alfa cek dulu jika ada user yang izin atau cuti maka jangan di anggap alfa
#             check_user_is_cuti = conn.execute(personal_leave.select().where(personal_leave.c.user_id == user_id)).first()
#             check_user_is_izin = conn.execute(permission.select().where(permission.c.user_id == user_id)).first()
            
#             #* ❗🪲============================== prediksi akan terjadinya bug pada logic ini ============================== belum diketahui BUG-nya apa
            
#             if check_user_is_cuti :
#                 if user_id != check_user_is_cuti.user_id :
#                     # Kondisi jika user tidak cuti dan  tidak scanning_in maka langsung nyatakan tidak hadir (ALFA)
#                     conn.execute(presence.insert().values(attendance_id = attendance_id, presence_status = "alfa", descriptions = "tanpa keterangan", ))
#                 else :
#                     # cek tanggal terkahir cuti (jika tanggal terakhir cuti lebih dari tanggal sekarang dan tidak masuk kerja 'scanning-in' maka di anggap ALFA)
#                     if current_date > check_user_is_cuti.end_date :
#                         # Kondisi jika user ada pada tabel cuti tapi sudah melebihi tanggal terkahir cuti
#                         conn.execute(presence.insert().values(attendance_id = attendance_id, presence_status = "alfa", descriptions = "tanpa keterangan", ))
#                     else :
#                         # Kondisi jika user ada pada tabel cuti dan masih dalam kurun waktu cuti
#                         conn.execute(presence.insert().values(attendance_id = attendance_id, presence_status = "cuti", descriptions = check_user_is_cuti.descriptions, ))
#             elif check_user_is_izin :
#                 if user_id != check_user_is_izin.user_id :
#                     # Kondisi jika user tidak izin dan  tidak scanning_in maka langsung nyatakan tidak hadir (ALFA)
#                     conn.execute(presence.insert().values(attendance_id = attendance_id, presence_status = "alfa", descriptions = "tanpa keterangan", ))
#                 else :
#                     if current_date == check_user_is_izin.created_at :
#                         # Kondisi jika user sedang izin atau user izin pada tanggal saat ini
#                         conn.execute(presence.insert().values(attendance_id = attendance_id, presence_status = "izin", descriptions = check_user_is_izin.reason, ))
#                     else :
#                         # Kondisi jika user tidak izin atau tanggal izin lewat dari tanggal ini
#                         conn.execute(presence.insert().values(attendance_id = attendance_id, presence_status = "alfa", descriptions = "tanpa keterangan", ))
#             else :
#                 # Kondisi jika user tidak izin dan tidak cuti
#                 conn.execute(presence.insert().values(attendance_id = attendance_id, presence_status = "alfa", descriptions = "tanpa keterangan", ))
        
#         return {"message" : "setup done"}
#     except SQLAlchemyError as e :
#         print("terdapat error --> ", e)
#     finally :
#         conn.close()
#         print("\n --> 'userNotScannedin' berhasil >> Koneksi di tutup <-- \n")