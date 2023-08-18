from sqlalchemy.exc import SQLAlchemyError
from config.db import engine
from sqlalchemy.sql import select
from fastapi import APIRouter, HTTPException
from models.tabel import personal_leave, user_data, permission, user_role
from schema.schemas import PersonalLeave, UpdatePersonalLeaveAgreement
from config.picture_drive import drive
from config.jakarta_timezone import jkt_current_date
import datetime
import base64
import pytz
import secrets


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


@router_personal_leave.post('/api/personal-leave/submission' , tags=['PERSONAL LEAVE'])
async def personalLeaveSubmission(data : PersonalLeave) :
    try :
        conn = engine.connect()
        get_user_start_date = conn.execute(permission.select().where(permission.c.user_id == data.user_id, permission.c.start_date == data.start_date)).first()
        get_user_end_date = conn.execute(personal_leave.select().where(personal_leave.c.user_id == data.user_id, personal_leave.c.end_date >= data.start_date)).first()
        
        # cek user dan tanggal, apakah user sedang izin atau tidak jika sedang izin input start_date pada tabel cuti setelah tanggal izin berakhir
        if get_user_start_date == None :
            # cek user yang sedang dalam masa cuti, jika masih dalah kurun waktu cuti makan tolak input user agar tidak duplikat
            
            
            # cek lagi jika usernya izin lebih dari satu hari
            is_user_on_permission = conn.execute(permission.select().where(permission.c.user_id == data.user_id, permission.c.end_date >= data.start_date)).first()
            if is_user_on_permission == None :
                if get_user_end_date == None :
                    # Boleh cuti
                    data_url = data.apply_docs
                    pdf_bytes = base64.b64decode(data_url)
                    token_name = secrets.token_hex(10)+"."+"pdf"
                    generated_name = token_name
                    from io import BytesIO
                    pdf_stream = BytesIO(pdf_bytes)
                    push_the_file = drive.put(generated_name[1:], pdf_stream)
                    input_submission = conn.execute(personal_leave.insert().values(user_id = data.user_id, start_date = data.start_date, end_date = data.end_date, apply_docs = push_the_file, descriptions = data.descriptions, agreement = "waiting", created_at = jkt_current_date()))
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
                # Tidak boleh cuti karena masih dalam masa izin
                user_datas = conn.execute(user_data.select().where(user_data.c.id == data.user_id)).first()
                return {
                    "message" : "user is on permission",
                    "start_date" : data.start_date, 
                    "full_name" : f"{user_datas.first_name} {user_datas.last_name}"
                    }
        else :
            # Tidak boleh cuti karena sedang izin pada tanggal tersebut
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



@router_personal_leave.get('/api/personal-leave/single/show-personal-leave/{user_id}' , tags=['PERSONAL LEAVE'])
async def showDatasPersonalLeave(user_id:int) :
    try :
        conn = engine.connect()
        get_data_permission_list = conn.execute(personal_leave.select().where(personal_leave.c.user_id == user_id)).fetchall()
        return get_data_permission_list
    except SQLAlchemyError as e:
        print("terdapat error ==>  showDatasPersonalLeave", e)
    finally:
        print("\n ==> 'showDatasPersonalLeave' berhasil >> Koneksi di tutup <== \n")

@router_personal_leave.get('/api/personal-leave/single/apply-docs/{user_id}/{personal_leave_id}' , tags=['PERSONAL LEAVE'])
async def getPersonalLeaveApplyDocs (user_id : int, personal_leave_id : int) :
    try :
        conn = engine.connect()
        get_data_personal_leave_list = conn.execute(personal_leave.select().where(personal_leave.c.user_id == user_id, personal_leave.c.id == personal_leave_id)).first()
        if get_data_personal_leave_list :
            return {"docs" : await getPermissionDocs(get_data_personal_leave_list.apply_docs)}
        else :
            return {"message" : "doc not found"}
    except SQLAlchemyError as e:
        print("terdapat error ==> getPersonalLeaveApplyDocs", e)
    finally:
        conn.close()
        print("\n ==> 'getPersonalLeaveApplyDocs' berhasil >> Koneksi di tutup <== \n")


@router_personal_leave.get('/api/personal-leave/multi/personal-leave' , tags=['PERSONAL LEAVE'])
async def getAllPersonalLeave () :
    try :
        conn = engine.connect()
        join_query = personal_leave.join(user_data, personal_leave.c.user_id == user_data.c.id).join(user_role, user_data.c.role_id == user_role.c.id )
        result_join = select([user_data.c.id, user_data.c.alamat, user_data.c.no_telepon, user_data.c.first_name, user_data.c.email, user_role.c.role, user_data.c.last_name, user_data.c.profile_picture, personal_leave.c.id, personal_leave.c.agreement, personal_leave.c.apply_docs, personal_leave.c.agreement_docs, personal_leave.c.descriptions,personal_leave.c.start_date, personal_leave.c.end_date, personal_leave.c.created_at]).select_from(join_query)
        exec_join = conn.execute(result_join).fetchall()
        
        personal_leave_datas = []
        
        for item in exec_join :
            personal_leave_datas.append({
                "staf_id": item.id,
                "personal_leave_id": item.id_1,
                "first_name": item.first_name,
                "last_name": item.last_name,
                "email": item.email,
                "alamat": item.alamat,
                "no_telepon": item.no_telepon,
                "role": item.role,
                "agreement": item.agreement,
                "apply_docs":  item.apply_docs,
                "agreement_docs" : item.agreement_docs,
                "descriptions": item.descriptions,
                "start_date": item.start_date,
                "end_date": item.end_date,
                "created_at": item.created_at,
                "profile_picture": await profilePictures(item.profile_picture)
                })
            
        return personal_leave_datas
    
    except SQLAlchemyError as e:
        print("terdapat error ==> getAllPersonalLeave", e)
    finally:
        conn.close()
        print("\n ==> 'getAllPersonalLeave' berhasil >> Koneksi di tutup <== \n")


@router_personal_leave.put('/api/personal-leave/agreement/personal-leave' , tags=['PERSONAL LEAVE'])
async def agreementPersonalLeave (data : UpdatePersonalLeaveAgreement) :
    try :
        conn = engine.connect()
        if data.agreement == "approved" :
            data_url = data.agreement_docs
            pdf_bytes = base64.b64decode(data_url)
            token_name = secrets.token_hex(10)+"."+"pdf"
            generated_name = token_name
            from io import BytesIO
            pdf_stream = BytesIO(pdf_bytes)
            push_the_file = drive.put(generated_name[1:], pdf_stream)
            if push_the_file :
                personal_leave_approving = conn.execute(personal_leave.update().values(agreement = data.agreement, agreement_docs = push_the_file).where(personal_leave.c.user_id == data.user_id, personal_leave.c.id == data.personal_leave_id))
                if personal_leave_approving.rowcount > 0 :
                    return {"message": "approved"}
        elif data.agreement == "not approved" :
            personal_leave_not_approving = conn.execute(personal_leave.update().values(agreement = data.agreement, agreement_docs = None).where(personal_leave.c.user_id == data.user_id, personal_leave.c.id == data.personal_leave_id))
            if personal_leave_not_approving.rowcount > 0 :
                return {"message": "not approved"}
    except SQLAlchemyError as e:
        print("terdapat error ==> agreementPersonalLeave", e)
    finally:
        conn.close()
        print("\n ==> 'agreementPersonalLeave' berhasil >> Koneksi di tutup <== \n")

@router_personal_leave.get('/api/user-permission/single/approvment-loading/{user_id}/{personal_leave_id}' , tags=['PERSONAL LEAVE'])
async def getDocByOptions (user_id : int, personal_leave_id : int) :
    try :
        conn = engine.connect()
        get_data_personal_leave_list = conn.execute(personal_leave.select().where(personal_leave.c.user_id == user_id, personal_leave.c.id == personal_leave_id)).first()
        if get_data_personal_leave_list :
            return {"agreement_docs" : await getPermissionDocs(get_data_personal_leave_list.agreement_docs)}
        else :
            return {"message" : "doc not found"}
    except SQLAlchemyError as e:
        print("terdapat error ==> getDocByOptions", e)
    finally:
        conn.close()
        print("\n ==> 'getDocByOptions' berhasil >> Koneksi di tutup <== \n")
        