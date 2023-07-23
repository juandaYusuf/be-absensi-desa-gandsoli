from sqlalchemy.exc import SQLAlchemyError
from config.db import engine
from config.automated_input_presence import userNotScanned
from fastapi import APIRouter, HTTPException
from models.tabel import attendance_rules, attendance, user_has_scanned_in, personal_leave ,permission ,presence
from schema.schemas import (AttendanceRules, AttendanceRulesActivation, )
import datetime
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler


router_attendance_rules = APIRouter()
scheduler = AsyncIOScheduler()


async def automatedInsertquery():
    try :
        conn = engine.connect()
        # cek tanggal sekarang kemudian anggap user yang tidak melakukan scann_in sebagai user yang tidak hadir (ALFA)
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        current_datetime = datetime.datetime.now(jakarta_tz)
        date_on_today = current_datetime.date()
        current_date = date_on_today
        #? ================================ ALGORITHM =======================================
        # Dapatkan data user yang sudah melakukan scan hari ini
        # Dapatkan seluruh user
        # kemudian cek user mana yang tidak melakukan scann_in
        # cek apakah ada user yang cuti jika ada insert cuti ke tabel presence
        # insert yang tidak hadir ke tabel presence
        #? ==================================================================================
        
        get_data_from_attendance = conn.execute(attendance.select()).fetchall()
        get_user_scanned_in = conn.execute(user_has_scanned_in.select().where(user_has_scanned_in.c.created_at > current_date)).fetchall()
        
        
        
        # variabel untuk menyimpan user_id
        # karena 'get_data_from_attendance' dan 'get_user_scanned_in' mengembalikan object dalam array
        # jadi harus ditampung dulu pada variable agar value dari array tidak bertipe data object
        only_user_id_of_attendance = []
        only_user_id_of_scanned_in = []
        only_attendance_id = []
        user_id_has_scanned_in_today = []
        user_id_do_not_scan_in_today = []
        attendance_id_do_not_scan_in_today = []
        
        
        
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
                    conn.execute(presence.insert().values(attendance_id = attendance_id, presence_status = "alfa", descriptions = "tanpa keterangan", ))
                else :
                    # cek tanggal terkahir cuti (jika tanggal terakhir cuti lebih dari tanggal sekarang dan tidak masuk kerja 'scanning-in' maka di anggap ALFA)
                    if current_date > check_user_is_cuti.end_date :
                        # Kondisi jika user ada pada tabel cuti tapi sudah melebihi tanggal terkahir cuti
                        conn.execute(presence.insert().values(attendance_id = attendance_id, presence_status = "alfa", descriptions = "tanpa keterangan", ))
                    else :
                        # Kondisi jika user ada pada tabel cuti dan masih dalam kurun waktu cuti
                        conn.execute(presence.insert().values(attendance_id = attendance_id, presence_status = "cuti", descriptions = check_user_is_cuti.descriptions, ))
            elif check_user_is_izin :
                if user_id != check_user_is_izin.user_id :
                    # Kondisi jika user tidak izin dan  tidak scanning_in maka langsung nyatakan tidak hadir (ALFA)
                    conn.execute(presence.insert().values(attendance_id = attendance_id, presence_status = "alfa", descriptions = "tanpa keterangan", ))
                else :
                    if current_date == check_user_is_izin.created_at :
                        # Kondisi jika user sedang izin atau user izin pada tanggal saat ini
                        conn.execute(presence.insert().values(attendance_id = attendance_id, presence_status = "izin", descriptions = check_user_is_izin.reason, ))
                    else :
                        # Kondisi jika user tidak izin atau tanggal izin lewat dari tanggal ini
                        conn.execute(presence.insert().values(attendance_id = attendance_id, presence_status = "alfa", descriptions = "tanpa keterangan", ))
            else :
                # Kondisi jika user tidak izin dan tidak cuti
                conn.execute(presence.insert().values(attendance_id = attendance_id, presence_status = "alfa", descriptions = "tanpa keterangan", ))
        
        return {"message" : "setup done"}
    except SQLAlchemyError as e :
        print("terdapat error --> ", e)
    finally :
        conn.close()
        print("\n --> 'userNotScannedin' berhasil >> Koneksi di tutup <-- \n")


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
                description=data.description))
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
async def usageAttendancerule(data : AttendanceRulesActivation):
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
                hour = get_attendance_time.work_start_time.hour
                minutes = get_attendance_time.late_deadline
                
                
                # !======================= Menjalankan schedul task =======================
                
                is_task_is_running = scheduler.get_jobs() #cek apakah ada task yang sedang berjalan
                for job in is_task_is_running: 
                    if job.name == "userNotScanned": # jika da maka update jadwal nya setiap kali user melakuka perubahan pada aturan absensi di frontend
                        job.reschedule(trigger='cron', hour=hour, minute=minutes)
                        return {
                            "messages" : "attendance_rules has been updated",
                            "work_start_time":get_attendance_time.work_start_time,
                            "work_times_up":get_attendance_time.work_times_up,
                            "late_deadline": get_attendance_time.late_deadline,
                            "sechedule": f"{hour}:{minutes}",
                            "sechedule_status":"rescheduled"
                            } 
                
                if len(is_task_is_running) <= 0: # jika tidak ada schedule maka buat schedule
                    scheduler.add_job(userNotScanned, 'cron', hour=hour, minute=minutes)
                    scheduler.start()
                    return {
                        "messages" : "attendance_rules has been updated",
                        "work_start_time":get_attendance_time.work_start_time,
                        "work_times_up":get_attendance_time.work_times_up,
                        "late_deadline": get_attendance_time.late_deadline,
                        "sechedule": f"{hour}:{minutes}",
                        "sechedule_status":"rescheduled"
                        } 
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> usageAttendancerule berhasil >> Koneksi di tutup <== \n")

