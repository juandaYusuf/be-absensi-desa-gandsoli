from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import select
from config.db import engine
from fastapi import APIRouter
from models.tabel import user_data, attendance, presence, user_has_scanned_in,personal_leave, permission
from schema.schemas import AttendanceInputData
import smtplib
from email.message import EmailMessage
import datetime
import calendar


#! Anggap user yang tidak melakukan scan_in sebagai user yang tidak hadir (Endpoin ini di hit ketika waktu keluar kerja telah berakhir)
async def userNotScannedin():
    try :
        
        conn = engine.connect()
        # cek tanggal sekarang kemudian anggap user yang tidak melakukan scann_in sebagai user yang tidak hadir (ALFA)
        current_date = datetime.date.today()
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
        

userNotScanned = userNotScannedin()