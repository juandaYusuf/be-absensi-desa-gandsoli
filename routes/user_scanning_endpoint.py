from sqlalchemy.exc import SQLAlchemyError
from config.db import engine
from config.email_sender_message import EmailSender
from sqlalchemy.sql import select
from fastapi import APIRouter, HTTPException
from models.tabel import user_has_scanned_in, user_has_scanned_out, attendance_rules, presence, attendance, user_data, detail_user_scanned
from schema.schemas import userScanning
from config.jakarta_timezone import jkt_current_datetime
# from config.email_sender_message import email_sender
# from config.picture_drive import drive
import datetime
import pytz
# import base64

router_user_scanning = APIRouter()


#! ================== GET PROFILE PICTURE ==================
# # fungction untuk mendapatkan gambar
# async def profilePictures(pp_name):
#     if str(pp_name) != "None":
#         large_file = drive.get(pp_name)
#         output = b""
#         for chunk in large_file.iter_chunks(4096):
#             output += chunk
#         large_file.close()
#         encoded_image = base64.b64encode(output)
#         return encoded_image.decode("utf-8")
#     else :
#         return None
#! ==========================================================

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
    


#! ========================= INSERT detail_user_scanned =================================
async def insertDetailUserScanned(scanned_options, user_id, scan_in_id, scan_out_id, presence_id):
    try :
        conn = engine.connect()
        user_datas = conn.execute(user_data.select().where(user_data.c.id == user_id)).first()
        if scanned_options == "in":
            insert_detail = conn.execute(detail_user_scanned.insert().values(
                user_id = user_id, 
                scan_in_id = scan_in_id, 
                scan_out_id = scan_out_id, 
                presence_id = presence_id,
                created_at=jkt_current_datetime()))
            if insert_detail.rowcount > 0 :
                return {
                    "message" : f"thanks for scanned {scanned_options}",
                    "fullname": f"{user_datas.first_name} {user_datas.last_name}",
                    "date": jkt_current_datetime()}
        else :
            update_detail = conn.execute(detail_user_scanned.update().values(scan_out_id = scan_out_id).where(detail_user_scanned.c.user_id == user_id))
            if update_detail.rowcount > 0 :
                return {
                    "message" : f"thanks for scanned {scanned_options}",
                    "fullname": f"{user_datas.first_name} {user_datas.last_name}",
                    "date": jkt_current_datetime()}
        
        
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        print("\n ==> 'insertDetailUserScanned' berhasil >> Koneksi di tutup <== \n")
        

#! ==========================================================

# !ENDPOINT CLEAR OLD DATA (Membersihkan data terdahulu atau data yang bukan hari ini 'clear data < today') - endpoint ini di hit ketika halaman qr-generator pada frontend di render-
@router_user_scanning.delete('/api/scanning/clearing-old-datas' , tags=['USER SCANNING'])
async def clearingOldDats():
    try :
        conn = engine.connect()
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        current_datetime = datetime.datetime.now(jakarta_tz)
        date_on_today = current_datetime.date()
        date_of_today = date_on_today
        delete_old_record_scan_in = conn.execute(detail_user_scanned.delete().where(detail_user_scanned.c.created_at < date_of_today))
        
        if delete_old_record_scan_in.rowcount > 0:
            return {"message" : "setup done"}
        else :
            return {"message" : "no old data to clean"}
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> 'clearingOldDats' berhasil >> Koneksi di tutup <== \n")

# !ENDPOINT SCANNING-IN (Scan qrcode masuk kerja) -endpoint ini di hit ketika user scan qrcode masuk-
@router_user_scanning.post('/api/scanning/user-scanning-in' , tags=['USER SCANNING'])
async def postUserScanningInData(data : userScanning):
    try:
        conn = engine.connect()
        # cek user yang scan 2x
        cek_user_2x_scanning = conn.execute(user_has_scanned_in.select().where(user_has_scanned_in.c.user_id == data.user_id)).first()
        
        # ========================== Variabel untuk insert detail_user_scanned ==========================
        user_id = 0
        scan_in_id = 0
        presence_id = 0
        # ===================================================================================================
        
        
        # Cek jika user sudah scan
        if cek_user_2x_scanning is not None and cek_user_2x_scanning.user_id == data.user_id:
            # User telah scan
            return {"message" : "you have scanned today"}
        else:
            # User belum scan maka input data scann in
            # get attendance id 
            get_attendance_id = conn.execute(attendance.select().where(attendance.c.user_id == data.user_id)).first().id
            insert_scanned_in = conn.execute(user_has_scanned_in.insert().values(
                user_id = data.user_id, 
                attendance_id = get_attendance_id, 
                status = data.status,
                created_at=jkt_current_datetime()))
            
            # ontime_datas = []
            # alfa_datas = []
            # comelate_datas = []
            
            # cek jika berhasil scanning
            if insert_scanned_in.rowcount > 0 :
                get_data_from_scanned_in = conn.execute(user_has_scanned_in.select().where(user_has_scanned_in.c.user_id == data.user_id)).first()
                            
                date_time_user_scanning = str(get_data_from_scanned_in.created_at)
                time_from_scanning_in = date_time_user_scanning.split(" ")[1]
                # time_from_scanning_in = "07:10:00"
                
                # cek waktu pada aturan absensi
                get_datetime_from_attdnc_rule = conn.execute(attendance_rules.select().where(attendance_rules.c.usage == 1)).first()
                
                string_late_deadline_from_attdnc_rule = str(get_datetime_from_attdnc_rule.late_deadline)
                string_start_time_from_attdnc_rule = str(get_datetime_from_attdnc_rule.work_start_time)
                work_start_time =string_start_time_from_attdnc_rule
                
                # variable hasil manipulasi waktu masuk dengan waktu terlambat kerja disatukan
                late_estimate = string_start_time_from_attdnc_rule[:3] + string_late_deadline_from_attdnc_rule + string_start_time_from_attdnc_rule[5:]
                
                
                #  ubah jam/tanggal yang sebelumnya string menjadi tipe data yang sesungguhnya(time)
                time_format_from_scanning_in = datetime.datetime.strptime(time_from_scanning_in, "%H:%M:%S").time()
                time_format_late_estimate = datetime.datetime.strptime(late_estimate, "%H:%M:%S").time()
                
                if time_format_from_scanning_in > time_format_late_estimate:
                    # ini adalah kondisi dimana user yang melakukan scann melebihi estimasi keterlambatan maka harus "ALFA"
                    insert_to_presence_as_alfa = conn.execute(presence.insert().values(
                        attendance_id = get_attendance_id, 
                        presence_status = "alfa",
                        created_at_in=jkt_current_datetime(),
                        descriptions = "melebihi batas terlambat"))
                    email_data = data_for_email_message(get_attendance_id, jkt_current_datetime())
                    if email_data is not None :
                        EmailSender(reciver_email = email_data.email, reciver_name=f"{email_data.first_name} {email_data.last_name}", reciver_presence_status="alfa", description="Melebihi batas waktu terlambat", date=jkt_current_datetime()).sender()
                    if insert_to_presence_as_alfa.rowcount > 0 :
                        # handle alfa
                        # kirim email pada email user yang terkait dan menyatakan sebagai ALFA
                        #! ========================== JOIN UNTUK ALFA ==============================
                        # join 'tabel user_has_scanned_in' dengan 'tabel attendance'
                        join_qery = user_has_scanned_in.join(attendance, user_has_scanned_in.c.attendance_id == attendance.c.id).join(user_data, user_has_scanned_in.c.user_id == user_data.c.id)
                        result_join_qery = select([user_data.c.id, user_data.c.first_name, user_data.c.last_name, user_data.c.profile_picture, attendance.c.id]).select_from(join_qery)
                        execute_join_qery = conn.execute(result_join_qery).fetchall()
                        #! =========================================================================
                        
                        
                        #! ===================== COMBINE JOIN_QUERY TEPAT WAKTU =====================
                        # mengkombinasikan data hasil "join_qery" dengan data dari tabel "presence_datas"
                        for join_query_data in execute_join_qery:
                            presence_datas = conn.execute(presence.select().where(presence.c.attendance_id == join_query_data.id_1)).fetchall()
                            for presence_data in presence_datas:
                                # picture = await profilePictures(join_query_data.profile_picture)
                                
                                # ========================= isi variabel untuk memasukan data ke detail_user_scanned =========================
                                user_id = join_query_data.id,
                                scan_in_id = get_data_from_scanned_in.id
                                presence_id = presence_data.id,
                                # ============================================================================================================
                                
                                # alfa_datas.append({
                                #         "user_id": join_query_data.id,
                                #         "full_name": f'{join_query_data.first_name} {join_query_data.last_name}',
                                #         "attendance_id": join_query_data.id_1,
                                #         "jam_masuk": presence_data.created_at_in,
                                #         "descriptions" : presence_data.descriptions,
                                #         "profile_picture": picture
                                #     })
                        #! ==========================================================================
                        # melakukan return data untuk user yang ALFA atau MELEBIHI ESTIMASI TERLAMBAT dalam melakukan scan
                        # return alfa_datas
                        # await insertDetailUserScanned("in", user_id, scan_in_id, None, presence_id)
                        # return {"message" : "Tanks for scanned in"}
                        
                else:
                    #! =============================================================
                    # ini kondisi jika user yang scanningIn masih dalam jangka waktu estimasi terlambat (HADIR tapi telat)
                    # nanti kirim email
                    # Handle untuk terlambat berapa menit
                    # dan handle untuk tepat waktu
                    time_format_from_scanning_in = datetime.datetime.strptime(time_from_scanning_in, "%H:%M:%S").time()
                    time_format_late_estimate = datetime.datetime.strptime(late_estimate, "%H:%M:%S").time()
                    #! =============================================================

                    work_start_time_to_time = datetime.datetime.strptime(work_start_time, "%H:%M:%S").time()
                    # Cek jika user terlambat
                    if time_format_from_scanning_in <= time_format_late_estimate and time_format_from_scanning_in > work_start_time_to_time:
                        # handle terlambat dan menampilkan keterlambatanya
                        minutes_from_scanning_in = time_format_from_scanning_in.minute
                        second_from_scanning_in = time_format_from_scanning_in.second
                        come_late_description = f"telat {minutes_from_scanning_in} menit {second_from_scanning_in} detik"
                        insert_to_presence_as_come_late = conn.execute(presence.insert().values(
                            attendance_id = get_attendance_id, 
                            presence_status = "hadir",
                            created_at_in=jkt_current_datetime(),
                            working = True, 
                            descriptions = come_late_description))
                        email_data = data_for_email_message(get_attendance_id, jkt_current_datetime())
                        if email_data is not None :
                            EmailSender(reciver_email = email_data.email, reciver_name=f"{email_data.first_name} {email_data.last_name}", reciver_presence_status="Alfa", description=come_late_description, date=jkt_current_datetime()).sender()
                        #! ========================== JOIN UNTUK TELAT ==============================
                        # join 'tabel user_has_scanned_in' dengan 'tabel attendance'
                        join_qery = user_has_scanned_in.join(attendance, user_has_scanned_in.c.attendance_id == attendance.c.id).join(user_data, user_has_scanned_in.c.user_id == user_data.c.id)
                        result_join_qery = select([user_data.c.id, user_data.c.first_name, user_data.c.last_name, user_data.c.profile_picture, attendance.c.id]).select_from(join_qery)
                        execute_join_qery = conn.execute(result_join_qery).fetchall()
                        #! =========================================================================
                        
                        
                        #! ===================== COMBINE JOIN_QUERY TELAT =====================
                        # mengkombinasikan data hasil "join_qery" dengan data dari tabel "presence_datas"
                        for join_query_data in execute_join_qery:
                            presence_datas = conn.execute(presence.select().where(presence.c.attendance_id == join_query_data.id_1)).fetchall()
                            for presence_data in presence_datas:
                                # picture = await profilePictures(join_query_data.profile_picture)
                                
                                # ========================= Masukan data ke detail_user_scanned =========================
                                user_id = join_query_data.id,
                                scan_in_id = get_data_from_scanned_in.id
                                presence_id = presence_data.id,
                                # =======================================================================================
                                
                                # comelate_datas.append({
                                #         "user_id": join_query_data.id,
                                #         "full_name": f'{join_query_data.first_name} {join_query_data.last_name}',
                                #         "attendance_id": join_query_data.id_1,
                                #         "jam_masuk": presence_data.created_at_in,
                                #         "descriptions" : presence_data.descriptions,
                                #         "profile_picture": picture
                                #     })
                        #! ====================================================================
                        # melakukan return data untuk user yang TERLAMBAT dalam melakukan scan
                        # await insertDetailUserScanned("in", user_id, scan_in_id, None, presence_id)
                        # return {"message" : "Tanks for scanned in"}
                        
                        
                    elif time_format_from_scanning_in <= work_start_time_to_time :
                        # handle ketika user masuk kerja
                        insert_to_presence_as_come_late = conn.execute(presence.insert().values(
                            attendance_id = get_attendance_id, 
                            presence_status = "hadir", 
                            created_at_in=jkt_current_datetime(),
                            working = True, 
                            descriptions = "tepat waktu"))
                        email_data = data_for_email_message(get_attendance_id, jkt_current_datetime())
                        if email_data is not None :
                            EmailSender(reciver_email = email_data.email, reciver_name=f"{email_data.first_name} {email_data.last_name}", reciver_presence_status="hadir", description="tepat waktu", date=jkt_current_datetime()).sender()
                        # jika berhasil inser data ke "presence"
                        if insert_to_presence_as_come_late.rowcount > 0 :
                            
                            #! ========================== JOIN TEPAT WAKTU ==============================
                            # join 'tabel user_has_scanned_in' dengan 'tabel attendance'
                            join_qery = user_has_scanned_in.join(attendance, user_has_scanned_in.c.attendance_id == attendance.c.id).join(user_data, user_has_scanned_in.c.user_id == user_data.c.id)
                            result_join_qery = select([user_data.c.id, user_data.c.first_name, user_data.c.last_name, user_data.c.profile_picture, attendance.c.id]).select_from(join_qery)
                            execute_join_qery = conn.execute(result_join_qery).fetchall()
                            #! ==========================================================================
                            
                            
                            #! ===================== COMBINE JOIN_QUERY TEPAT WAKTU =====================
                            # mengkombinasikan data hasil "join_qery" dengan data dari tabel "presence_datas"
                            for join_query_data in execute_join_qery:
                                presence_datas = conn.execute(presence.select().where(presence.c.attendance_id == join_query_data.id_1)).fetchall()
                                for presence_data in presence_datas:
                                    # picture = await profilePictures(join_query_data.profile_picture)
                                    
                                    # ========================= Masukan data ke detail_user_scanned =========================
                                    user_id = join_query_data.id,
                                    scan_in_id = get_data_from_scanned_in.id
                                    presence_id = presence_data.id,
                                    # =======================================================================================
                                    
                                    
                                    # ontime_datas.append({
                                    #         "user_id": join_query_data.id,
                                    #         "full_name": f'{join_query_data.first_name} {join_query_data.last_name}',
                                    #         "attendance_id": join_query_data.id_1,
                                    #         "jam_masuk": presence_data.created_at_in,
                                    #         "descriptions" : presence_data.descriptions,
                                    #         "profile_picture": picture
                                    #     })
                            #! ==========================================================================
                            # melakukan return data untuk user yang tepat waktu melakukan scan
                            # await insertDetailUserScanned("in", user_id, scan_in_id, None, presence_id)
                            # return {"message" : "Tanks for scanned in"}
                    
                    #! =========================================================================================
                    #! ==============KONDISI WAKTU SCAN benar-benar SAMA DENGAN ESTIMASI TERLAMBAT==============
                    #! =========================================================================================
            
            else :
                print("Error validasi")
            return await insertDetailUserScanned("in", user_id, scan_in_id, None, presence_id)
                
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> 'postUserScanningData' berhasil >> Koneksi di tutup <== \n")


#!  ENDPOINT SCANNING-OUT (endpoint untuk scan keluar) -endpoint ini di hit ketika user scan qrcode keluar-
@router_user_scanning.post('/api/scanning/user-scanning-out' , tags=['USER SCANNING'])
async def postUserScanningOutData(data: userScanning):
    try :

        
        conn = engine.connect()
        
        # ========================== Variabel untuk insert detail_user_scanned ==========================
        user_id = 0
        scan_out_id = 0
        presence_id = 0
        # ===================================================================================================
        
        cek_user_2x_scanning = conn.execute(user_has_scanned_out.select().where(user_has_scanned_out.c.user_id == data.user_id)).first()
        
        # Cek jika user sudah scan
        if cek_user_2x_scanning is not None and cek_user_2x_scanning.user_id == data.user_id:
            # User telah scan
            return {"message" : "you have scanned today"}
        else:
            get_user_scanned_in = conn.execute(user_has_scanned_in.select().where(user_has_scanned_in.c.user_id == data.user_id)).first()
            get_attendance_id = conn.execute(attendance.select().where(attendance.c.user_id == data.user_id)).first().id
            
            #! ============================= JOIN QUERY UNTUK CEK PRESENSI ================================
            join_query = user_has_scanned_in.join(attendance, user_has_scanned_in.c.attendance_id == attendance.c.id ).join(presence, presence.c.attendance_id == attendance.c.id).join(user_data, user_data.c.id == attendance.c.user_id)
            result_join_query = select([attendance.c.user_id, user_data.c.first_name, user_data.c.last_name, user_data.c.profile_picture, presence.c.id, presence.c.presence_status, presence.c.descriptions]).select_from(join_query)
            execute_join_query = conn.execute(result_join_query).fetchall()
            #! ============================================================================================
            
            if get_user_scanned_in :
                # ini kondisi ketika user melakukan scanning_in
                # Note: Jika scanning_in tepat waktu maka input data ke presence sebagai hadir (ambil data untuk cek hadir tepat waktu pada variable 'execute_join_query')
                
                # insert data ke tabel user_has_scanned_out
                insert_scanned_out = conn.execute(user_has_scanned_out.insert().values(
                    user_id = data.user_id, 
                    attendance_id = get_attendance_id, 
                    status = data.status,
                    created_at=jkt_current_datetime()))
                if insert_scanned_out.rowcount > 0 :
                    # ini kondisi ketika insert_scanned_out berhasil kemudian return data
                    # ambil data dari 'execute_join_query' menggunakan 'for loop' untuk validasi yang telah melakukan scan
                    for join_query_datas in execute_join_query :
                        #! ============================= JIKA SCANNING_IN TEPAT WAKTU =================================
                        # cek user yang tepat waktu
                        if join_query_datas.user_id == data.user_id and join_query_datas.presence_status == "hadir" :
                            # picture = await profilePictures(join_query_datas.profile_picture)
                            
                            # =================================== Update data presence ===================================
                            # get nilai created_at pada tabel 'user_has_scanned_out'
                            date_of_scanned_in = conn.execute(user_has_scanned_in.select().where(user_has_scanned_in.c.user_id == data.user_id)).first()
                            date_of_scanned_out = conn.execute(user_has_scanned_out.select().where(user_has_scanned_out.c.user_id == data.user_id)).first()
                            
                            # hitung total jam kerja
                            time_difference = date_of_scanned_out.created_at - get_user_scanned_in.created_at  #selisih waktu
                            hours_worked = time_difference.seconds // 3600
                            minutes_worked = (time_difference.seconds // 60) % 60
                            second_worked = time_difference.seconds % 60
                            result_total_hours_worked = f"{hours_worked} jam, {minutes_worked} menit, {second_worked} detik"
                            
                            # Update table presence kolom created_at_out yang di isi dengan data created_at yang terdapat pada tabel scan_out
                            update_presence = conn.execute(presence.update().values(created_at_out = date_of_scanned_out.created_at, total_hours_worked = result_total_hours_worked, working = False).where(presence.c.attendance_id == date_of_scanned_out.attendance_id))
                            # ============================================================================================
                            if update_presence.rowcount > 0 :
                                # ========================= isi variabel untuk memasukan data ke detail_user_scanned =========================
                                user_id = join_query_datas.user_id
                                scan_in_id = date_of_scanned_in.id
                                scan_out_id = date_of_scanned_out.id
                                presence_id = join_query_datas.id #presence id hasil join
                                # ============================================================================================================
                                # return {
                                #     "user_id": join_query_datas.user_id,
                                #     "full_name": f"{join_query_datas.first_name} {join_query_datas.last_name}",
                                #     "presence_status": join_query_datas.presence_status,
                                #     "descriptions": join_query_datas.descriptions,
                                #     "profile_picture": picture
                                #     }
                        #! ============================================================================================
                        
                        
                        #! ================================== SCANNING_IN TERLAMBAT ===================================
                        # cek melakukan scanning_in yang masih dalam estimasi terlambat (Hadir tapi terlambat)
                        if join_query_datas.user_id == data.user_id and join_query_datas.presence_status == "hadir" :
                            # picture = await profilePictures(join_query_datas.profile_picture)
                            # =================================== Update data presence ===================================
                            # get nilai created_at pada tabel 'user_has_scanned_out'
                            date_of_scanned_in = conn.execute(user_has_scanned_in.select().where(user_has_scanned_in.c.user_id == data.user_id)).first()
                            date_of_scanned_out = conn.execute(user_has_scanned_out.select().where(user_has_scanned_out.c.user_id == data.user_id)).first()
                            
                            # hitung total jam kerja
                            time_difference = date_of_scanned_out.created_at - get_user_scanned_in.created_at  #selisih waktu
                            hours_worked = time_difference.seconds // 3600
                            minutes_worked = (time_difference.seconds // 60) % 60
                            second_worked = time_difference.seconds % 60
                            result_total_hours_worked = f"{hours_worked} jam, {minutes_worked} menit, {second_worked} detik"
                            
                            # Update table presence kolom created_at_out yang di isi dengan data created_at yang terdapat pada tabel scan_out
                            update_presence = conn.execute(presence.update().values(created_at_out = date_of_scanned_out.created_at, total_hours_worked = result_total_hours_worked, working = False).where(presence.c.attendance_id == date_of_scanned_out.attendance_id))
                            # ============================================================================================
                            if update_presence.rowcount > 0 :
                                # ========================= isi variabel untuk memasukan data ke detail_user_scanned =========================
                                user_id = join_query_datas.user_id
                                scan_in_id = date_of_scanned_in.id
                                scan_out_id = date_of_scanned_out.id
                                presence_id = join_query_datas.id #presence id hasil join
                                # ============================================================================================================
                                # return {
                                #     "user_id": join_query_datas.user_id,
                                #     "full_name": f"{join_query_datas.first_name} {join_query_datas.last_name}",
                                #     "presence_status": join_query_datas.presence_status,
                                #     "descriptions": join_query_datas.descriptions,
                                #     "profile_picture": picture
                                #     }
                        #! ============================================================================================
                        
                        
                        #! ======================== SCANNING_IN LEWAT ESTIMASI TERLAMBAT =========================
                        # cek melakukan scanning_in tapi melebihi batas waktu estimasi terlambat (alfa)
                        if join_query_datas.user_id == data.user_id and join_query_datas.presence_status == "alfa" :
                            # picture = await profilePictures(join_query_datas.profile_picture)
                            date_of_scanned_in = conn.execute(user_has_scanned_in.select().where(user_has_scanned_in.c.user_id == data.user_id)).first()
                            date_of_scanned_out = conn.execute(user_has_scanned_out.select().where(user_has_scanned_out.c.user_id == data.user_id)).first()
                            # ========================= isi variabel untuk memasukan data ke detail_user_scanned =========================
                            user_id = join_query_datas.user_id
                            scan_in_id = date_of_scanned_in.id
                            scan_out_id = date_of_scanned_out.id
                            presence_id = join_query_datas.id #presence id hasil join
                            # ============================================================================================================
                            
                            # return {
                            #     "user_id": join_query_datas.user_id,
                            #     "full_name": f"{join_query_datas.first_name} {join_query_datas.last_name}",
                            #     "presence_status": join_query_datas.presence_status,
                            #     "descriptions": join_query_datas.descriptions,
                            #     "profile_picture": picture
                            #     }
                        #! =======================================================================================
                    return await insertDetailUserScanned("out", user_id, scan_in_id, scan_out_id, presence_id)
            else :
                # Ini kondisi dimana user tidak scanning_in
                
                # Cek jika user tidak melakukan scan_in maka user akan dianggap tidak hadir
                # tapi pada 25 juni 2023 pada saat code ini ditulis saya melakukan return seperti dibawah yang tidak mengembalikan data user hanya message saja
                # mungkin suatu saat kode ini akan dikembangkan lagi
                return {"message" : "You do not scan_in"}
            
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> 'postUserScanningOutData' berhasil >> Koneksi di tutup <== \n")
