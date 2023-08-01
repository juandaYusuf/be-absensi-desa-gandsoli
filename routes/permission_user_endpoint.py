from sqlalchemy.exc import SQLAlchemyError
from config.db import engine
from sqlalchemy.sql import select
from fastapi import APIRouter, HTTPException
from models.tabel import user_data, permission, personal_leave
from schema.schemas import UserPermission
from config.picture_drive import drive
import datetime 
import base64
import json
import pytz



router_user_permission = APIRouter()

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


@router_user_permission.post('/api/user-permission/submission' , tags=['USER PERMISSION'])
async def permissionSubmission(data: UserPermission) :
    try :
        conn = engine.connect()
        get_user_and_date = conn.execute(permission.select().where(permission.c.user_id == data.user_id, permission.c.created_at >= data.created_at)).first()
        get_user_in_personal_leave = conn.execute(personal_leave.select().where(personal_leave.c.user_id == data.user_id, personal_leave.c.end_date >= data.created_at)).first()
        
        #Ini pengecekan untuk menghandle apabila user izin pada hari yang sama maka tolak (Tidak boleh izin pada hari yang sama)
        if get_user_and_date == None : # Usertidak sedang izin hari ini
            # ini kondisi user saat user tidak izin pada tanggal yang sama (diperbolehkan izin pada hari tersebut atau hari ini)
            # maka insert data ke tabel izin 'permission'
            if get_user_in_personal_leave == None : # User tidak sedang cuti
                # jika user tidak sedang cuti maka user boleh izin
                insert_submission = conn.execute(permission.insert().values(user_id = data.user_id, reason = data.reason, created_at = data.created_at))
                if insert_submission.rowcount > 0 :
                    join_query = permission.join(user_data, permission.c.user_id == user_data.c.id)
                    result_join = select([user_data.c.first_name, user_data.c.last_name, permission.c.reason, permission.c.created_at]).select_from(join_query).where(permission.c.user_id == data.user_id)
                    execute_result = conn.execute(result_join).first()
                    return execute_result
            else :
                # Jika user sedang cuti maka tolak izin nya
                user_datas = conn.execute(user_data.select().where(user_data.c.id == data.user_id)).first()
                raise HTTPException(
                status_code=409, 
                detail={
                    "message": "user is on paid leave", 
                    "full_name" : f"{user_datas['first_name']} {user_datas['last_name']}", 
                    "end_date": json.dumps(get_user_in_personal_leave.end_date.isoformat())
                    })
        else :
            # data duplikat atau user telah melakukan izin pada hari yang sama
            user_datas = conn.execute(user_data.select().where(user_data.c.id == data.user_id)).first()
            raise HTTPException(
                status_code=409, 
                detail={
                    "message": "user has been permission", 
                    "full_name" : f"{user_datas['first_name']} {user_datas['last_name']}", 
                    "created_at": json.dumps(data.created_at.isoformat())
                    })
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        print("\n ==> 'permissionSubmission' berhasil >> Koneksi di tutup <== \n")


@router_user_permission.get('/api/user-permission/show-all-user-permission/{options}' , tags=['USER PERMISSION'])
async def showAllPermissionDatas(options : str) :
    try :
        conn = engine.connect()
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        current_datetime = datetime.datetime.now(jakarta_tz)
        date_on_today = current_datetime.date()
        
        user_permission_datas_for_today = []
        user_permission_datas_for_all = []
        join_query = permission.join(user_data, permission.c.user_id == user_data.c.id)
        result_join = select([user_data.c.first_name, user_data.c.last_name, user_data.c.email, user_data.c.no_telepon, user_data.c.profile_picture, permission.c.reason, permission.c.created_at]).select_from(join_query)
        
        
        execute_result = conn.execute(result_join).fetchall()
        
        for items in execute_result :
            if options == "today" and items.created_at == date_on_today:
                print(options, items.created_at == date_on_today)
                user_permission_datas_for_today.append({
                    "first_name": items.first_name,
                    "last_name": items.last_name,
                    "email": items.email,
                    "no_telepon": items.no_telepon,
                    "created_at" : items.created_at,
                    "profile_picture": await profilePictures(items.profile_picture),
                    "reason": items.reason
                })
            else :
                user_permission_datas_for_all.append({
                    "first_name": items.first_name,
                    "last_name": items.last_name,
                    "email": items.email,
                    "no_telepon": items.no_telepon,
                    "created_at" : items.created_at,
                    "profile_picture": await profilePictures(items.profile_picture),
                    "reason": items.reason
                })
        
        if options == "today":
            return user_permission_datas_for_today
        else :
            return user_permission_datas_for_all
            
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        print("\n ==> 'personalLeaveSubmission' berhasil >> Koneksi di tutup <== \n")
