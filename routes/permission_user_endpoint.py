from sqlalchemy.exc import SQLAlchemyError
from config.db import engine
from sqlalchemy.sql import select
from fastapi import APIRouter, HTTPException
from models.tabel import user_data, permission, personal_leave, user_role
from schema.schemas import UserPermission, UpdatePermissionAgreement
from config.picture_drive import drive
import datetime 
import base64
import secrets
import json
from config.jakarta_timezone import jkt_current_date
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

#! ================== GET PERMISSION DOCS ==================
# fungction untuk mendapatkan dokumen
async def getPermissionDocs(doc_name):
    if str(doc_name) != "None":
        large_file = drive.get(doc_name)
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
        end_date_manipulate = None
        if data.end_date != "" :
            end_date_manipulate = data.end_date
            
        get_user_and_date = conn.execute(permission.select().where(permission.c.user_id == data.user_id, permission.c.start_date == data.start_date)).first()
        get_user_in_personal_leave = conn.execute(personal_leave.select().where(personal_leave.c.user_id == data.user_id, personal_leave.c.end_date >= data.start_date)).first()
        
        #Ini pengecekan untuk menghandle apabila user izin pada hari yang sama maka tolak (Tidak boleh izin pada hari yang sama)
        if get_user_and_date == None : # Usertidak sedang izin hari ini
            # ini kondisi user saat user tidak izin pada tanggal yang sama (diperbolehkan izin pada hari tersebut atau hari ini)
            # maka insert data ke tabel izin 'permission'
            if get_user_in_personal_leave == None : # User tidak sedang cuti
                # jika user tidak sedang cuti maka user boleh izin
                # cek jika user melakukan izin lagi padahal dia sedang dalam masa izin
                user_is_on_permission = conn.execute(permission.select().where(permission.c.user_id == data.user_id, permission.c.end_date >= data.start_date)).first()
                if user_is_on_permission == None :
                    insert_submission = conn.execute(permission.insert().values(user_id = data.user_id, reason = data.reason, start_date = data.start_date, end_date = end_date_manipulate, agreement = 'waiting', created_at = jkt_current_date()))
                    if insert_submission.rowcount > 0 :
                        join_query = permission.join(user_data, permission.c.user_id == user_data.c.id)
                        result_join = select([user_data.c.first_name, user_data.c.last_name, permission.c.reason, permission.c.created_at]).select_from(join_query).where(permission.c.user_id == data.user_id)
                        execute_result = conn.execute(result_join).first()
                        return execute_result
                else:
                    # kondisi jika user sedang dalam masa izin
                    return {"message": "you are on permission"}
                    
            else :
                # Jika user sedang cuti maka tolak izin nya
                return {"message": "user is on paid leave"}
        else :
            # data duplikat atau user telah melakukan izin pada hari yang sama
            return {"message": "user has been permission"}
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
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
        join_query = permission.join(user_data, permission.c.user_id == user_data.c.id).join(user_role, user_data.c.role_id == user_role.c.id)
        result_join = select([user_data.c.id, user_data.c.first_name, user_data.c.last_name, user_data.c.email, user_data.c.no_telepon, user_data.c.profile_picture, permission.c.reason, permission.c.created_at, permission.c.start_date, permission.c.end_date, permission.c.agreement, user_data.c.alamat, user_role.c.role, permission.c.id]).select_from(join_query)
        
        
        execute_result = conn.execute(result_join).fetchall()
        
        for items in execute_result :
            if options == "today" and items.created_at == date_on_today:
                user_permission_datas_for_today.append({
                    "user_id":items.id,
                    "first_name": items.first_name,
                    "last_name": items.last_name,
                    "role": items.role,
                    "email": items.email,
                    "no_telepon": items.no_telepon,
                    "permission_id": items.id_1,
                    "start_date" : items.start_date,
                    "end_date" : items.end_date,
                    "created_at" : items.created_at,
                    "alamat" : items.alamat,
                    "agreement" : items.agreement,
                    "profile_picture": await profilePictures(items.profile_picture),
                    "reason": items.reason
                })
            elif options == "all" :
                user_permission_datas_for_all.append({
                    "user_id":items.id,
                    "first_name": items.first_name,
                    "last_name": items.last_name,
                    "role": items.role,
                    "email": items.email,
                    "no_telepon": items.no_telepon,
                    "permission_id": items.id_1,
                    "start_date" : items.start_date,
                    "end_date" : items.end_date,
                    "created_at" : items.created_at,
                    "alamat" : items.alamat,
                    "agreement" : items.agreement,
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
        conn.close()
        print("\n ==> 'showAllPermissionDatas' berhasil >> Koneksi di tutup <== \n")


@router_user_permission.put('/api/user-permission/agreement/' , tags=['USER PERMISSION'])
async def permissionAgreement (data : UpdatePermissionAgreement) :
    try :
        conn = engine.connect()
        
        if data.agreement == "approved" :
            data_url = data.docs
            pdf_bytes = base64.b64decode(data_url)
            token_name = secrets.token_hex(10)+"."+"pdf"
            generated_name = token_name
            from io import BytesIO
            pdf_stream = BytesIO(pdf_bytes)
            push_the_file = drive.put(generated_name[1:], pdf_stream)
            if push_the_file :
                permission_agreement = conn.execute(permission.update().values(agreement = data.agreement, docs = push_the_file).where(permission.c.user_id == data.user_id, permission.c.id == data.permission_id))
                if permission_agreement.rowcount > 0 :
                    return {"message": "approved"}
        elif data.agreement == "not approved" :
            permission_agreement = conn.execute(permission.update().values(agreement = data.agreement, docs = None).where(permission.c.user_id == data.user_id, permission.c.id == data.permission_id))
            if permission_agreement.rowcount > 0 :
                return {"message": "not approved"}
            
    except SQLAlchemyError as e:
        print("terdapat error permissionAgreement ==> ", e)
    finally:
        conn.close()
        print("\n ==> 'permissionAgreement' berhasil >> Koneksi di tutup <== \n")
        
@router_user_permission.get('/api/user-permission/single/user-permission/{staff_id}/{hv_id}' , tags=['USER PERMISSION'])
async def getSingleUserPermission (staff_id : int, hv_id:int) :
    try :
        conn = engine.connect()
        join_query = user_data.join(permission, user_data.c.id == permission.c.user_id).join(user_role, user_data.c.role_id == user_role.c.id)
        result_join = select([ user_data.c.id, user_data.c.first_name, user_data.c.last_name, user_role.c.role, user_data.c.alamat, permission.c.reason, permission.c.start_date, permission.c.end_date, user_data.c.signature]).select_from(join_query).where(user_data.c.id == staff_id)
        exec_join = conn.execute(result_join).first()
        if exec_join is not None :
            get_head_village_signature = conn.execute(user_data.select().where(user_data.c.id == hv_id)).first()
            return {
                "id": exec_join.id,
                "first_name": exec_join.first_name,
                "last_name": exec_join.last_name,
                "role": exec_join.role,
                "alamat":exec_join .alamat,
                "reason":exec_join .reason,
                "start_date": exec_join.start_date,
                "end_date": exec_join.end_date,
                "staff_signature": await profilePictures(exec_join.signature) if exec_join.signature is not None else None,
                "head_village_signature": await profilePictures(get_head_village_signature.signature) if get_head_village_signature.signature is not None else None
                }
        else :
            raise HTTPException(status_code=404, detail="user not found")
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> 'getSingleUserPermission' berhasil >> Koneksi di tutup <== \n")
        
        
@router_user_permission.get('/api/user-permission/single/user-permission-list/{user_id}' , tags=['USER PERMISSION'])
async def getSingleUserPermissionLis (user_id : int) :
    try :
        conn = engine.connect()
        get_data_permission_list = conn.execute(permission.select().where(permission.c.user_id == user_id)).fetchall()
        return get_data_permission_list
    except SQLAlchemyError as e:
        print("terdapat error ==> getSingleUserPermissionLis", e)
    finally:
        conn.close()
        print("\n ==> 'getSingleUserPermissionLis' berhasil >> Koneksi di tutup <== \n")
        

@router_user_permission.get('/api/user-permission/single/doc/{user_id}/{permission_id}' , tags=['USER PERMISSION'])
async def getDocByOptions (user_id : int, permission_id : int) :
    try :
        conn = engine.connect()
        get_data_permission_list = conn.execute(permission.select().where(permission.c.user_id == user_id, permission.c.id == permission_id)).first()
        if get_data_permission_list :
            return {"docs" : await getPermissionDocs(get_data_permission_list.docs)}
        else :
            return {"message" : "doc not found"}
    except SQLAlchemyError as e:
        print("terdapat error ==> getDocByOptions", e)
    finally:
        conn.close()
        print("\n ==> 'getDocByOptions' berhasil >> Koneksi di tutup <== \n")
        