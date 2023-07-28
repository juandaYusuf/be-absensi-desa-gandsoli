from sqlalchemy.exc import SQLAlchemyError
from config.db import engine
from sqlalchemy.sql import select
from fastapi import APIRouter, HTTPException
from models.tabel import personal_leave, user_data, permission
from schema.schemas import PersonalLeave
from config.picture_drive import drive
import datetime
import base64
import pytz



router_personal_leave = APIRouter()

#! ================== GET PROFILE PICTURE ==================
# fungction untuk mendapatkan gambar
async def profilePictures(pp_name):
    if str(pp_name) != "None":
        large_file = drive.get(pp_name)
        output = b""
        for chunk in large_file.iter_chunks(4096):
            output += chunk
        large_file.close()
        encoded_image = base64.b64encode(output)
        return encoded_image.decode("utf-8")
    else :
        return None
#! ==========================================================

@router_personal_leave.post('/api/personal-leave/submission' , tags=['PERSONAL LEAVE'])
async def personalLeaveSubmission(data : PersonalLeave) :
    try :
        conn = engine.connect()
        get_user_start_date = conn.execute(permission.select().where(permission.c.user_id == data.user_id, permission.c.created_at >= data.start_date)).first()
        get_user_end_date = conn.execute(personal_leave.select().where(personal_leave.c.user_id == data.user_id, personal_leave.c.end_date >= data.start_date)).first()
        
        # cek user dan tanggal, apakah user sedang izin atau tidak jika sedang izin input start_date pada tabel cuti setelah tanggal izin berakhir
        if get_user_start_date == None :
            # cek user yang sedang dalam masa cuti, jika masih dalah kurun waktu cuti makan tolak input user agar tidak duplikat
            if get_user_end_date == None :
                # Boleh cuti
                input_submission = conn.execute(personal_leave.insert().values(user_id = data.user_id, start_date = data.start_date, end_date = data.end_date, descriptions = data.descriptions))
                if input_submission.rowcount > 0 :
                    join_query = personal_leave.join(user_data, personal_leave.c.user_id == user_data.c.id)
                    result_join = select([user_data.c.first_name, user_data.c.last_name, personal_leave.c.start_date, personal_leave.c.end_date]).select_from(join_query).where(personal_leave.c.user_id == data.user_id)
                    execute_query = conn.execute(result_join).first()
                return execute_query
            else :
                # Tidak boleh cuti karena masih dalam masa cuti
                user_datas = conn.execute(user_data.select().where(user_data.c.id == data.user_id)).first()
                return {
                    "message" : "user is on paid leave",
                    "end_date" : get_user_end_date.end_date,
                    "full_name" : f"{user_datas.first_name} {user_datas.last_name}"
                    }
        else :
            # Tidak boleh cuti karena sedang izin
            user_datas = conn.execute(user_data.select().where(user_data.c.id == data.user_id)).first()
            return {
                "message" : "user is on permission",
                "start_date" : data.start_date, 
                "full_name" : f"{user_datas.first_name} {user_datas.last_name}"
                }
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        print("\n ==> 'personalLeaveSubmission' berhasil >> Koneksi di tutup <== \n")



@router_personal_leave.get('/api/personal-leave/show-all-personal-leave' , tags=['PERSONAL LEAVE'])
async def showAllDatasPersonalLeave() :
    try :
        conn = engine.connect()
        datas = []
        join_query = personal_leave.join(user_data, personal_leave.c.user_id == user_data.c.id)
        result_join = select([user_data.c.profile_picture, user_data.c.first_name, user_data.c.email, user_data.c.no_telepon, user_data.c.last_name, personal_leave.c.start_date, personal_leave.c.end_date, personal_leave.c.descriptions]).select_from(join_query)
        execute_query = conn.execute(result_join).fetchall()
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        current_datetime = datetime.datetime.now(jakarta_tz)
        date_on_today = current_datetime.date()
        
        
        for items in execute_query :
            if items.end_date >= date_on_today :
                datas.append({
                    "profile_picture": await profilePictures(items.profile_picture),
                    "first_name": items.first_name,
                    "last_name": items.last_name,
                    "email": items.email,
                    "no_telepon": items.no_telepon,
                    "start_date": items.start_date,
                    "end_date": items.end_date,
                    "descriptions": items.descriptions
                })
            
        return datas
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        print("\n ==> 'showAllDatasPersonalLeave' berhasil >> Koneksi di tutup <== \n")

