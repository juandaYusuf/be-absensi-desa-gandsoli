from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import select
from config.db import engine
# from config.automated_input_presence import userNotScannedin
from fastapi import APIRouter, HTTPException, BackgroundTasks
from models.tabel import attendance_rules, attendance, user_has_scanned_in, personal_leave ,permission ,presence, user_data
from schema.schemas import (AttendanceRules, AttendanceRulesActivation, )
import pytz
from config.email_sender_message import EmailSender, ConfirmEmailSender
from config.jakarta_timezone import jkt_current_datetime, jkt_current_date, jkt_current_time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import datetime
import time
import threading
import schedule
import requests



router_attendance_rules = APIRouter()
# scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Jakarta'))

# @router_attendance_rules.get("/data_for_email_message")
def data_for_email_message (attendance_id, created_at_in):
    try :
        conn = engine.connect()
        join_query = attendance.join(user_data, attendance.c.user_id == user_data.c.id ).join(presence, attendance.c.id == presence.c.attendance_id)
        exe_join_query = select(join_query).where(attendance.c.id == attendance_id, presence.c.created_at_in == created_at_in)
        resuult_exe = conn.execute(exe_join_query).first()
        if resuult_exe :
            return resuult_exe
        else :
            return None
            
    except SQLAlchemyError as e :
        print("Terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n --> 'data_for_email_message' berhasil >> Koneksi di tutup <-- \n")
    
    
    
@router_attendance_rules.get("/api/automation/automate-insert-query", tags=["CRON JOB API"])
async def automatedInsertquery():
    try :
        day_name_of_ind = ['senin', 'selasa', 'rabu', 'kamis', 'jumat', 'sabtu', 'minggu']
        conn = engine.connect()
        # cek tanggal sekarang kemudian anggap user yang tidak melakukan scann_in sebagai user yang tidak hadir (ALFA)
        current_date = jkt_current_time()
        # return current_date
        #? ================================ ALGORITHM =======================================
        # Dapatkan data user yang sudah melakukan scan hari ini
        # Dapatkan seluruh user
        # kemudian cek user mana yang tidak melakukan scann_in
        # cek apakah ada user yang cuti jika ada insert cuti ke tabel presence
        # insert yang tidak hadir ke tabel presence
        #? ==================================================================================
        
        # dapatkan tanggal sekarang
        curren_date = datetime.date.today()
        
        # dapatkan index hari dari hari ini 
        index_of_today = curren_date.weekday()
        
        # dapatkan nama hari dalam bahasa indonesia
        result_day_name_of_ind = day_name_of_ind[index_of_today]
        
        get_data_from_attendance = conn.execute(attendance.select()).fetchall()
        get_user_scanned_in = conn.execute(user_has_scanned_in.select().where(user_has_scanned_in.c.created_at > jkt_current_datetime())).fetchall()
        
        
        
        # variabel untuk menyimpan user_id
        # karena 'get_data_from_attendance' dan 'get_user_scanned_in' mengembalikan object dalam array
        # jadi harus ditampung dulu pada variable agar value dari array tidak bertipe data object
        only_user_id_of_attendance = []
        only_user_id_of_scanned_in = []
        only_attendance_id = []
        user_id_has_scanned_in_today = []
        user_id_do_not_scan_in_today = []
        attendance_id_do_not_scan_in_today = []
        
        #* Cek apakah hari minggu/sabtu. Maka jangan ngapangapain
        
        # if result_day_name_of_ind == 'sabtu' or result_day_name_of_ind == 'minggu':
        #     print("weekEnd")
        # else :
        #     print("weekDay")
        # return result_day_name_of_ind
        
        if result_day_name_of_ind == 'sabtu' or result_day_name_of_ind == 'minggu':
            return {"message" : "weekend"}
        else :
            
            #* ===========================================================================
            # Loop seluruh isi data dari tabel user_data (var 'get_data_from_attendance') 
            # dan ambil 'user_id' nya saja
            for user_id_of_attendance in get_data_from_attendance :
                only_user_id_of_attendance.append(user_id_of_attendance.user_id)
            #* ===========================================================================
            
            
            
            #* ===========================================================================
            # Loop seleuruh isi data dari tabel attendance (var 'get_data_from_attendance') 
            # dan ambil 'user_id' nya saja
            for id_of_attendance in get_data_from_attendance :
                only_attendance_id.append(id_of_attendance.id)
            #* ===========================================================================
            
            
            
            #* ===========================================================================
            # Loop seleuruh isi data dari tabel user_has_scanned_in (var 'get_user_scanned_in') 
            # dan ambil 'user_id' nya saja
            for user_id_of_scanned_in in get_user_scanned_in :
                only_user_id_of_scanned_in.append(user_id_of_scanned_in.user_id)
            #* ===========================================================================
            
            
            #* ===========================================================================
            # Loop seluruh user_id dan cek user dengan id berapa yang tidak melakukan scan_in 
            for user_id in only_user_id_of_attendance :
                if user_id not in only_user_id_of_scanned_in :
                    # kondisi dimana user yang tidak melakukan scan_in dan yang akan di anggap ALFA
                    attendance_id = conn.execute(attendance.select().where(attendance.c.user_id == user_id, )).first()
                    user_id_do_not_scan_in_today.append({
                        "attendance_id": attendance_id.id,
                        "user_id" : attendance_id.user_id
                        })
                else :
                    # kondisi dimana user yang melakukan scan_in (HADIR)
                    # tidak akan melakukan apapunm pada kondisi ini
                    # ini diimplementasikan karena untuk mempermudah jika sistem ini akan dikembangkan lagi
                    attendance_id = conn.execute(attendance.select().where(attendance.c.user_id == user_id)).first()
                    user_id_has_scanned_in_today.append({
                        "attendance_id": attendance_id.id,
                        "user_id" : attendance_id.user_id
                        })
            #* ===========================================================================
            
            
            
            #! ================================ Nyatakan tidak hadir ================================
            # Loop lagi user yang tidak melakukan scan_in pada (var 'user_id_do_not_scan_in_today')
            # kemudian insert ke tabel 'presence' untuk dinyatakan tidak hadir
            for absent_users in user_id_do_not_scan_in_today :
                attendance_id = absent_users["attendance_id"] # variabel ini untuk mengambil value dari objek yang terdapat dalam array
                user_id = absent_users["user_id"] # variabel ini untuk mengambil value dari objek yang terdapat dalam array
                # Sebelum menyatakan alfa cek dulu jika ada user yang izin atau cuti maka jangan di anggap alfa
                check_user_is_cuti = conn.execute(personal_leave.select().where(personal_leave.c.user_id == user_id)).first()
                check_user_is_izin = conn.execute(permission.select().where(permission.c.user_id == user_id)).first()
                
                #* ❗🪲============================== prediksi akan terjadinya bug pada logic ini ============================== belum diketahui BUG-nya apa
                
                if check_user_is_cuti :
                    if user_id != check_user_is_cuti.user_id :
                        # Kondisi jika user tidak cuti dan  tidak scanning_in maka langsung nyatakan tidak hadir (ALFA)
                        conn.execute(presence.insert().values(
                            attendance_id = attendance_id, 
                            presence_status = "alfa", 
                            created_at_in=jkt_current_datetime(),
                            descriptions = "tanpa keterangan", 
                            ))
                        # ?Kirim emal pemberitahuan
                        # data_for_email_message(attendance_id)
                        email_data = data_for_email_message(attendance_id, jkt_current_datetime())
                        if email_data is not None :
                            EmailSender(reciver_email = email_data.email, reciver_name=f"{email_data.first_name} {email_data.last_name}", reciver_presence_status="alfa", description="tanpa keterangan", date=jkt_current_datetime()).sender()
                    else :
                        # cek tanggal terkahir cuti (jika tanggal terakhir cuti lebih dari tanggal sekarang dan tidak masuk kerja 'scanning-in' maka di anggap ALFA)
                        if current_date > check_user_is_cuti.end_date :
                            # Kondisi jika user ada pada tabel cuti tapi sudah melebihi tanggal terkahir cuti
                            conn.execute(presence.insert().values(
                                attendance_id = attendance_id, 
                                presence_status = "alfa", 
                                created_at_in=jkt_current_datetime(),
                                descriptions = "tanpa keterangan", ))
                            # ?Kirim emal pemberitahuan
                            email_data = data_for_email_message(attendance_id, jkt_current_datetime())
                            if email_data is not None :
                                EmailSender(reciver_email = email_data.email, reciver_name=f"{email_data.first_name} {email_data.last_name}", reciver_presence_status="alfa", description="tanpa keterangan", date=jkt_current_datetime()).sender()
                        else :
                            # Kondisi jika user ada pada tabel cuti dan masih dalam kurun waktu cuti
                            conn.execute(presence.insert().values(
                                attendance_id = attendance_id, 
                                presence_status = "cuti", 
                                created_at_in=jkt_current_datetime(),
                                descriptions = check_user_is_cuti.descriptions, ))
                elif check_user_is_izin :
                    if user_id != check_user_is_izin.user_id :
                        # Kondisi jika user tidak izin dan  tidak scanning_in maka langsung nyatakan tidak hadir (ALFA)
                        conn.execute(presence.insert().values(
                            attendance_id = attendance_id, 
                            presence_status = "alfa", 
                            created_at_in=jkt_current_datetime(),
                            descriptions = "tanpa keterangan", ))
                        # ?Kirim emal pemberitahuan
                        email_data = data_for_email_message(attendance_id, jkt_current_datetime())
                        if email_data is not None :
                            EmailSender(reciver_email = email_data.email, reciver_name=f"{email_data.first_name} {email_data.last_name}", reciver_presence_status="alfa", description="tanpa keterangan", date=jkt_current_datetime()).sender()
                    else :
                        if current_date == check_user_is_izin.created_at :
                            # Kondisi jika user sedang izin atau user izin pada tanggal saat ini
                            conn.execute(presence.insert().values(
                                attendance_id = attendance_id, 
                                presence_status = "izin", 
                                created_at_in=jkt_current_datetime(),
                                descriptions = check_user_is_izin.reason, ))
                        else :
                            # Kondisi jika user tidak izin atau tanggal izin lewat dari tanggal ini
                            conn.execute(presence.insert().values(
                                attendance_id = attendance_id, 
                                presence_status = "alfa", 
                                created_at_in=jkt_current_datetime(),
                                descriptions = "tanpa keterangan", ))
                            # ?Kirim emal pemberitahuan
                            email_data = data_for_email_message(attendance_id, jkt_current_datetime())
                            if email_data is not None :
                                EmailSender(reciver_email = email_data.email, reciver_name=f"{email_data.first_name} {email_data.last_name}", reciver_presence_status="alfa", description="tanpa keterangan", date=jkt_current_datetime()).sender()
                else :
                    # Kondisi jika user tidak izin dan tidak cuti
                    conn.execute(presence.insert().values(
                        attendance_id = attendance_id, 
                        presence_status = "alfa", 
                        created_at_in=jkt_current_datetime(),
                        descriptions = "tanpa keterangan", ))
                    # ?Kirim emal pemberitahuan
                    email_data = data_for_email_message(attendance_id, jkt_current_datetime())
                    if email_data is not None :
                        EmailSender(reciver_email = email_data.email, reciver_name=f"{email_data.first_name} {email_data.last_name}", reciver_presence_status="alfa", description="tanpa keterangan", date=jkt_current_datetime()).sender()
            return {"message" : "setup done"}
    except SQLAlchemyError as e :
        print("terdapat error --> ", e)
    finally :
        conn.close()
        print("\n --> 'automatedInsertquery' berhasil >> Koneksi di tutup <-- \n")


def run_automated_insert():
    # asyncio.run(automatedInsertquery())
    requests.get('https://bedesagandasoli-1-j0924938.deta.app/api/automation/automate-insert-query')
    # while True:
    #     jkt_tz = pytz.timezone('Asia/Jakarta')
    #     curr_datetime = datetime.datetime.now(jkt_tz)
    #     h = int(curr_datetime.strftime('%H'))
    #     m = int(curr_datetime.strftime('%M'))
    #     s = int(curr_datetime.strftime('%S'))
    #     print(curr_datetime.strftime('%H:%M:%S'))
    #     if h == 21 and m == 13 and s == 00:
    #         print("Menjalankan tugas")
    #         asyncio.run(automatedInsertquery())
    #         print("Tugas telah dijalankan")
    #         time.sleep(30)
    #     time.sleep(1)



@router_attendance_rules.get("/api/attendance_rule/show-all-attendance-rules", tags=["ATTENDANCE RULES"])
async def showAttendancerule():
    try:
        conn = engine.connect()
        response = conn.execute(attendance_rules.select()).fetchall()
        return response
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> addAttendancerule berhasil >> Koneksi di tutup <== \n")


@router_attendance_rules.post("/api/attendance_rule/add-attendance-rule", tags=["ATTENDANCE RULES"])
async def addAttendanceRule(data: AttendanceRules):
    try:
        conn = engine.connect()
        response = conn.execute(
            attendance_rules.insert().values(
                title = data.title,
                work_start_time = data.work_start_time,
                work_times_up = data.work_times_up,
                late_deadline = data.late_deadline,
                description=data.description,
                created_at=jkt_current_datetime()))
        if response.rowcount > 0:
            return {"message": "data has been posted"}
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> addAttendanceRule berhasil >> Koneksi di tutup <== \n")

@router_attendance_rules.delete("/api/attendance_rule/delete-attendance-rules/{id}", tags=["ATTENDANCE RULES"])
async def deleteAttendancerule(id: int):
    try:
        conn = engine.connect()
        response = conn.execute(attendance_rules.delete().where(attendance_rules.c.id == id))
        if response.rowcount > 0 :
            cek_usage = conn.execute(attendance_rules.select().where(attendance_rules.c.usage == True)).first()
            if cek_usage == None :
                conn.execute(attendance_rules.update().values(usage = True).where(attendance_rules.c.id == 1))
            
            return {"message": "data has been deleted"}
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> addAttendancerule berhasil >> Koneksi di tutup <== \n")

@router_attendance_rules.put("/api/attendance_rule/usage-attendance-rules", tags=["ATTENDANCE RULES"])
async def usageAttendancerule(data : AttendanceRulesActivation, bg_task : BackgroundTasks):
    try:
        conn = engine.connect()
        reset_usages = conn.execute(attendance_rules.update().values(usage = 0))
        if reset_usages.rowcount > 0:
            response = conn.execute(attendance_rules.update().values(usage = data.usage).where(attendance_rules.c.id == data.id))
            if response.rowcount > 0 :
                cek_usage = conn.execute(attendance_rules.select().where(attendance_rules.c.usage == True)).first()
                if cek_usage == None :
                    conn.execute(attendance_rules.update().values(usage = True).where(attendance_rules.c.id == 1))
                    
                get_attendance_time = conn.execute(attendance_rules.select().where(attendance_rules.c.usage == True)).first()
                hour = int( get_attendance_time.work_start_time.hour)
                minutes = int(get_attendance_time.late_deadline)
                
                # !======================= Menjalankan schedul task =======================
                # is_task_is_running = scheduler.get_jobs() #cek apakah ada task yang sedang berjalan
                # for job in is_task_is_running: 
                #     if job.name == "run_automated_insert": # jika da maka update jadwal nya setiap kali user melakuka perubahan pada aturan absensi di frontend
                #         job.reschedule(trigger='cron', hour=20, minute=5)
                #         return {
                #             "messages" : "attendance_rules has been updated",
                #             "work_start_time":get_attendance_time.work_start_time,
                #             "work_times_up":get_attendance_time.work_times_up,
                #             "late_deadline": get_attendance_time.late_deadline,
                #             "sechedule": f"{hour}:{minutes}",
                #             "sechedule_status":"rescheduled"
                #             } 
                
                # if len(is_task_is_running) <= 0: # jika tidak ada schedule maka buat schedule
                #     scheduler.add_job(run_automated_insert, 'cron', hour=20, minute=5)
                #     scheduler.start()
                #     return {
                #         "messages" : "attendance_rules has been updated",
                #         "work_start_time":get_attendance_time.work_start_time,
                #         "work_times_up":get_attendance_time.work_times_up,
                #         "late_deadline": get_attendance_time.late_deadline,
                #         "sechedule": f"{hour}:{minutes}",
                #         "sechedule_status":"add scheduled"
                #         } 
                
                # threads = threading.Thread(target=run_automated_insert)
                # threads.start()
                # def run_bg_task():
                #     schedule.every().day.at("22:49").do(run_automated_insert)
                #     print('Shceduling.....')
                
                # bg_task.add_task(run_bg_task)
                
                return {
                    "messages" : "attendance_rules has been updated",
                    "work_start_time":get_attendance_time.work_start_time,
                    "work_times_up":get_attendance_time.work_times_up,
                    "late_deadline": get_attendance_time.late_deadline,
                    "sechedule": f"{hour}:{minutes}",
                    "sechedule_status":"add scheduled"
                    } 
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> usageAttendancerule berhasil >> Koneksi di tutup <== \n")

@router_attendance_rules.get('/date')
async def getdateFromServer():
    current_date = datetime.datetime.now()
    jkt_tz = pytz.timezone('Asia/Jakarta')
    jkt_date = datetime.datetime.now(jkt_tz)
    print('test datetime')
    return {"jkt_tz": jkt_date, "server_tz": current_date}



# def scheduled_task():
#     response = requests.post("http://127.0.0.1:8000/api/attendance_rule/usage-attendance-rules")
#     print(response.json())

# def run_scheduler():
#     # Ganti jam dan menit sesuai dengan waktu yang Anda inginkan (contoh: 08:00)
#     schedule.every().day.at("22:10").do(scheduled_task)

#     while True:
#         schedule.run_pending()
#         jkt_tz = pytz.timezone('Asia/Jakarta')
#         curr_datetime = datetime.datetime.now(jkt_tz)
#         print(curr_datetime.strftime('%H:%M:%S'))
#         time.sleep(1)

# scheduler_thread = threading.Thread(target=run_scheduler)
# scheduler_thread.start()

