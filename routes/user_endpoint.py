from sqlalchemy.exc import SQLAlchemyError
from PIL import Image
from sqlalchemy.orm import Session
from config.db import engine
from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from models.tabel import user_data, attendance, presence, user_role, user_device_auth, account_verification, detail_user_scanned, user_has_scanned_in, user_has_scanned_out, personal_leave, permission, sick
from schema.schemas import (LoginData, RegisterData, EditDataProfile, changePassword, UpdateRole, Verifications, UpdateSignature)
import secrets
from config.email_sender_message import ConfirmEmailSender
from config.upload_image_to_detadrive import uploadImageToDeta
import base64
from config.picture_drive import drive
import random




router_user = APIRouter()

#! ================== GET PROFILE PICTURE ==================
# fungction untuk mendapatkan gambar
async def profilePictures(img_name):
    if str(img_name) != "None":
        large_file = drive.get(img_name)
        output = b""
        for chunk in large_file.iter_chunks(4096):
            output += chunk
        large_file.close()
        encoded_image = base64.b64encode(output)
        return encoded_image.decode("utf-8")
    else :
        return None
#! ==========================================================



#! USER  ==============================================================================
@router_user.get('/')
async def fetchAllUserData():
    try:
        conn = engine.connect()
        return {"Hallo": "Koneksi ke DataBase Berhasil...!"}
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> fetchAllUserData berhasil >> Koneksi di tutup <== \n")

@router_user.post('/api/user/login', tags=["USERS"])
async def login(data: LoginData):
    try:
        conn = engine.connect()
        new_value = 0
        response = conn.execute(user_data.select().where(user_data.c.email == data.email)).first()
        
        if response :
            is_user_verified = conn.execute(account_verification.select().where(account_verification.c.user_id == response.id)).first()
            if is_user_verified.is_verified == True :
                get_role = conn.execute(user_role.select().where(user_role.c.id == response.role_id)).first()
                check_login_counter = conn.execute(user_data.select().where(user_data.c.id == response.id)).first()
                if check_login_counter.login_counter == None or check_login_counter.login_counter == 0:
                    # Ini kondisi ketika user baru di registrasikan atau belum pernah login
                    first_login = conn.execute(user_data.update().values(login_counter = 1).where(user_data.c.id == response.id)) # jika user login pertama kali maka hitung atau inisialisasi dengan angka 1
                    if first_login.rowcount > 0 :
                        # ini kondisi jika proses query 'first_login' berhasil
                        # karena user barusaja login maka insert fpBrowser  -> 'user_device_auth'
                        insert_fpBrowser = conn.execute(user_device_auth.insert().values(user_id = response.id, user_device = data.user_device))
                        if insert_fpBrowser.rowcount > 0:
                            return {
                                "id" : response.id, 
                                "role": get_role.role,
                                "encpass": response.password,
                                "log": "first login"
                                }
                else :
                    validate_user_device = conn.execute(user_device_auth.select().where(user_device_auth.c.user_id == response.id, user_device_auth.c.user_device == data.user_device)).first()
                    if validate_user_device is not None :
                        new_value = check_login_counter.login_counter + 1
                        insert_counter = conn.execute(user_data.update().values(login_counter = new_value).where(user_data.c.id == response.id))
                        if insert_counter.rowcount > 0 :
                            return {
                                "id" : response.id, 
                                "role": get_role.role,
                                "encpass": response.password,
                                "log": f"{new_value} times login"
                                }
                    else :
                        return {"message" : "device not vaidated"}
            else :
                get_role = conn.execute(user_role.select().where(user_role.c.id == response.role_id)).first()
                return {
                    "id" : response.id, 
                    "role": get_role.role,
                    "encpass": response.password,
                    "log": "unverified"
                    }
        elif not response :
            raise HTTPException(status_code=404, detail="User Tidak Dapat ditemukan, Harap periksa kembali Email dan Password")
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        if response :
            print(f"\n \033[4;32m ==> OK[200]: {response.first_name} --> 'login' | CONNECTION KILLED <== \n")


@router_user.post('/api/user/register', tags=["USERS"])
async def register(data: RegisterData):
    try:
        conn = engine.connect()
        verify_code = random.randint(000000, 999999)
        
        
        is_email_duplicate = conn.execute(user_data.select().where(user_data.c.email == data.email)).fetchall()
        get_role = conn.execute(user_role.select().where(user_role.c.role == data.role)).first()
        if is_email_duplicate :
            raise HTTPException(status_code=409, detail="Email telah digunakan")
        else :
            conn.execute(user_data.insert().values(first_name = data.first_name, last_name = data.last_name, alamat=data.alamat, no_telepon = data.no_telepon, email = data.email, password = data.password, j_kelamin = data.j_kelamin, role_id = get_role.id))
            response = conn.execute(user_data.select().where(user_data.c.first_name == data.first_name, user_data.c.last_name == data.last_name)).first()
            if response :
                fullname = f"{response.first_name} {response.last_name}"
                conn.execute(attendance.insert().values(user_id = response.id))
                attendance_table_response = conn.execute(attendance.select().where(attendance.c.user_id == response.id)).first()
                if attendance_table_response :
                    # Insert verified code 
                    conn.execute(account_verification.insert().values(user_id = response.id, code = verify_code))
                    ConfirmEmailSender(reciver_email=data.email, reciver_name= f'{data.first_name} {data.last_name}', verify_code=verify_code).sender()
                    return {
                        "message" : "register success",
                        "name": fullname,
                        "role": get_role.role
                        }
                    
            elif not response :
                raise HTTPException(status_code=404, detail="gagal menyimpan data")
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print(f"\n \033[4;32m ==> OK[200]:'register' | CONNECTION KILLED <== \n")


@router_user.put('/api/user/edit-profile', tags=["USERS"])
async def edifProfileData( data: EditDataProfile):
    try:
        conn = engine.connect()
        conn.execute(user_data.update().values(first_name = data.first_name, last_name = data.last_name, alamat = data.alamat, no_telepon = data.no_telepon, email = data.email).where(user_data.c.id == data.user_id))
        response = conn.execute(user_data.select().where(user_data.c.id == data.user_id)).first()
        print("response ==> \n", response)
        if response :
            return {"message" : "Data berhasil di update"}
        else :
            raise HTTPException(status_code=409, detail="Gagal edit data silahkan periksa kembali data")
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print(f"\n \033[4;32m ==> OK[200]: --> 'edit-profile-data' | CONNECTION KILLED <== \n")

@router_user.put('/api/user/check-password', tags=["USERS"])
async def checkPassword(data: changePassword) :
    try:
        conn = engine.connect()
        checking_current_pass = conn.execute(user_data.select().where(user_data.c.id == data.user_id)).first()
        return {"enc_pass":checking_current_pass.password}
    except SQLAlchemyError as e :
        print("terdapat error ==> ", e)
    finally :
        conn.close()
        print(f"\n \033[4;32m ==> OK[200]: --> 'check-password' | CONNECTION KILLED <== \n")

@router_user.put('/api/user/change-password', tags=["USERS"])
async def editPassword(data: changePassword) :
    try:
        conn = engine.connect()
        checking_current_pass = conn.execute(user_data.select().where(user_data.c.id == data.user_id)).first()
        if(checking_current_pass) :
            change_pass = conn.execute(user_data.update().where(user_data.c.id == data.user_id).values(password = data.encpass))
            print(change_pass.rowcount)
            if change_pass.rowcount > 0 :
                return {"message" : "password changed"}
        else :
            raise HTTPException(status_code=404, detail="gagal menyimpan perubahan")
    except SQLAlchemyError as e :
        print("terdapat error ==> ", e)
    finally :
        conn.close()
    print(f"\n \033[4;32m ==> OK[200]: --> 'check-password' | CONNECTION KILLED <== \n")

#! upload foto profile
@router_user.post('/api/user/upload-profile-picture/{id}', tags=["USERS"])
async def uploadprofileimage(id:int, image: UploadFile =File(...)):
    try:
        conn = engine.connect()
        is_user_exist = conn.execute(user_data.select().where(user_data.c.id == id)).first()
        upload_img = await uploadImageToDeta(image)
        if is_user_exist :
            insert_filename = conn.execute(user_data.update().values(profile_picture = upload_img).where(user_data.c.id == id))
            if insert_filename.rowcount > 0 :
                return {"message":"file succesfully uploaded"}
        else :
            raise HTTPException(
                status_code=404,
                detail="Pengguna tidak terdafatar"
                )
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print(f"\n \033[4;32m ==> OK[200]: --> 'register' | CONNECTION KILLED <== \n")

# !Get profile picture by user id
@router_user.get('/api/user/single/profile-picture/{id}', tags=["USERS"])
async def showprofileimage(id: int):
    try :
        conn = engine.connect()
        response = conn.execute(user_data.select().where(user_data.c.id == id)).first()
        if response :
            if response.profile_picture :
                large_file = drive.get(response.profile_picture)
                output = b""
                for chunk in large_file.iter_chunks(4096):
                    output += chunk
                large_file.close()
                encoded_image = base64.b64encode(output)
                return {"id": response.id,"picture": encoded_image.decode("utf-8")}
            else :
                return {"id": response.id ,"picture": "no picture"}
        else :
            raise HTTPException(status_code=404, detail="data tidak tersedia")
    except SQLAlchemyError as e :
        print("terdapat error ==> ", e)
    finally :
        conn.close()
        print(f"\n \033[4;32m ==> OK[200]: --> 'profile picture 0f {id}' | CONNECTION KILLED <== \n")

# !Get multi profile picture 
@router_user.get('/api/user/multi/profile-picture/', tags=["USERS"])
async def showmultiprofileimage():
    try :
        conn = engine.connect()
        get_profile_picture_from_db = conn.execute(user_data.select().where(user_data.c.profile_picture != None).with_only_columns([user_data.c.id, user_data.c.profile_picture])).fetchall()
        result = drive.list()
        all_files = result.get("names")
        profile_picture_multi_user = []
        for list_0f_files in all_files :
            print("==> ",list_0f_files)
            for list_of_preofile_picture_db in get_profile_picture_from_db :
                if list_0f_files == list_of_preofile_picture_db.profile_picture :
                    each_persons_picture = drive.get(list_of_preofile_picture_db.profile_picture)
                    output = b""
                    for chunk in each_persons_picture.iter_chunks(4096):
                        output += chunk
                    each_persons_picture.close()
                    encoded_image = base64.b64encode(output)
                    profile_picture_multi_user.append({
                        "id" : list_of_preofile_picture_db.id,
                        "picture": encoded_image
                    })
        return profile_picture_multi_user
    except SQLAlchemyError as e :
        print("terdapat error ==> ", e)
    finally :
        conn.close()
        print(f"\n \033[4;32m ==> OK[200]: --> 'profile picture 0f {id}' | CONNECTION KILLED <== \n")


#! Delete profile picture
@router_user.delete('/api/user/delete-profile-picture/{id}', tags=['USERS'])
async def deleteProfilePicture(id: int) :
    try :
        conn = engine.connect()
        user_profile_picture_data = conn.execute(user_data.select().where(user_data.c.id == id)).first().profile_picture
        if user_profile_picture_data :
            deleted_file = drive.delete(user_profile_picture_data)
            if deleted_file :
                conn.execute(user_data.update().values(profile_picture = None).where(user_data.c.id == id))
                return {"message" : "Foto profile berhasil dihapus"}
    except SQLAlchemyError as e :
        print("terdapat error ==> ", e)
    finally :
        conn.close()
        print(f"\n \033[4;32m ==> OK[200]: 'delete-profile-picture'| CONNECTION KILLED <== \n")


@router_user.get('/api/user/single/user/{id}', tags=['USERS'])
async def userDetail(id:int):
    try :
        conn = engine.connect()
        response = conn.execute(user_data.select().where(user_data.c.id == id)).first()
        get_role = conn.execute(user_role.select().where(user_role.c.id == response.role_id)).first()
        return {
            "id": response.id,
            "first_name": response.first_name,
            "last_name": response.last_name,
            "alamat":response.alamat,
            "no_telepon": response.no_telepon,
            "email": response.email,
            "j_kelamin": response.j_kelamin,
            "role": get_role.role,
            "signature": response.signature,
            "signature_data": await profilePictures(response.signature),
            "profile_picture": response.profile_picture
            }
    except SQLAlchemyError as e :
        print("terdapat error ==> ", e)
    finally :
        conn.close()
        print(f"\n \033[4;32m ==> OK[200]: 'user-detail'| CONNECTION KILLED <== \n")

@router_user.get('/api/user/multi/user', tags=['USERS'])
async def listOfUser():
    try:
        conn = engine.connect()
        response = conn.execute(user_data.select()).fetchall()
        filtered_response = []

        for row in response:
            filtered_row = {key: value for key, value in row.items() if key != 'password' }

            if row.profile_picture != None :
                each_persons_picture = drive.get(row.profile_picture)
                output = b""
                for chunk in each_persons_picture.iter_chunks(4096):
                    output += chunk
                each_persons_picture.close()
                encoded_image = base64.b64encode(output)
                filtered_row['profile_picture'] = encoded_image
                

            get_role = conn.execute(user_role.select().where(user_role.c.id == row.role_id)).first()
            filtered_row['role_id'] = get_role.role
            filtered_response.append(filtered_row)

        return filtered_response
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print(f"\n \033[4;32m ==> OK[200]: 'list-of-user'| CONNECTION KILLED <== \n")
        
# !DELETE USER
@router_user.delete('/api/user/single/delete-user/{id}' , tags=['USERS'])
async def deletUserData(id: int):
    try:
        conn = engine.connect()
        
        
        get_attendance_data = conn.execute(attendance.select().where(attendance.c.user_id == id)).first()
        get_presence_data = conn.execute(presence.select().where(presence.c.attendance_id == get_attendance_data.id)).first()
        get_profile_picture_name = conn.execute(user_data.select().where(user_data.c.id == id)).first().profile_picture
        
        
        # ?delete presence data
        if get_presence_data :
            conn.execute(detail_user_scanned.delete().where(detail_user_scanned.c.user_id == id))
            conn.execute(user_has_scanned_in.delete().where(user_has_scanned_in.c.user_id == id))
            conn.execute(user_has_scanned_out.delete().where(user_has_scanned_out.c.user_id == id))
            conn.execute(account_verification.delete().where(account_verification.c.user_id == id))
            conn.execute(user_device_auth.delete().where(user_device_auth.c.user_id == id))
            conn.execute(personal_leave.delete().where(personal_leave.c.user_id == id))
            conn.execute(permission.delete().where(permission.c.user_id == id))
            conn.execute(presence.delete().where(presence.c.attendance_id == get_presence_data.attendance_id))
            conn.execute(sick.delete().where(sick.c.user_id == id))
            conn.execute(attendance.delete().where(attendance.c.id == get_attendance_data.id))
            conn.execute(user_data.delete().where(user_data.c.id == id))
            if get_profile_picture_name:
                drive.delete(get_profile_picture_name)
            return {"message":"user data has been deleted"}
            # if delete_user_device_auth.rowcount > 0 :
            # if get_presence_data :
            #     delete_presence_data = conn.execute(presence.delete().where(presence.c.attendance_id == get_presence_data.attendance_id))
            # # ?Delete Attendance_data
            # if delete_presence_data.rowcount > 0 :
            #     delete_attendance_data = conn.execute(attendance.delete().where(attendance.c.id == get_attendance_data.id))
            #     # ?Delete user data and delete profile picture
            #     if delete_attendance_data.rowcount > 0 :
            #         delete_user_data = conn.execute(user_data.delete().where(user_data.c.id == id))
            #         if delete_user_data.rowcount > 0 :
            #             if get_profile_picture_name:
            #                 drive.delete(get_profile_picture_name)
        # ?delete jika presence data kosong
        else :
            conn.execute(detail_user_scanned.delete().where(detail_user_scanned.c.user_id == id))
            conn.execute(user_has_scanned_in.delete().where(user_has_scanned_in.c.user_id == id))
            conn.execute(user_has_scanned_out.delete().where(user_has_scanned_out.c.user_id == id))
            conn.execute(account_verification.delete().where(account_verification.c.user_id == id))
            conn.execute(personal_leave.delete().where(personal_leave.c.user_id == id))
            conn.execute(permission.delete().where(permission.c.user_id == id))
            conn.execute(user_device_auth.delete().where(user_device_auth.c.user_id == id))
            conn.execute(attendance.delete().where(attendance.c.id == get_attendance_data.id))
            conn.execute(user_data.delete().where(user_data.c.id == id))
            if get_profile_picture_name:
                drive.delete(get_profile_picture_name)
            return {"message":"user data has been deleted"}
            # if delete_user_device_auth.rowcount > 0 :
            # if delete_attendance_data.rowcount > 0 :
            #     delete_user_data = conn.execute(user_data.delete().where(user_data.c.id == id))
            #     if delete_user_data.rowcount > 0 :
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> 'deletUserData' berhasil >> Koneksi di tutup <== \n")


@router_user.put('/api/user/single/update-user-role' , tags=['USERS'])
async def updateUserRole(data : UpdateRole):
    try:
        conn = engine.connect()
        update_user_role = conn.execute(user_data.update().values(role_id = data.role).where(user_data.c.id == data.id))
        if update_user_role.rowcount > 0 :
            return {"message": "user role has been updated"}
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> 'updateUserRole' berhasil >> Koneksi di tutup <== \n")


@router_user.get('/api/user-role/multi/role' , tags=['USERS'])
async def userRoles():
    try:
        conn = engine.connect()
        return conn.execute(user_role.select()).fetchall()
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> 'userRoles' berhasil >> Koneksi di tutup <== \n")


@router_user.post('/api/verifications/single/user-verification-code/' , tags=['USERS'])
async def verifivations(data: Verifications):
    try:
        conn = engine.connect()
        get_verify_code = conn.execute(account_verification.select().where(account_verification.c.user_id == data.user_id, account_verification.c.code == data.code)).first()
        if get_verify_code :
            set_as_verified = conn.execute(account_verification.update().values(is_verified = True).where(account_verification.c.user_id == data.user_id))
            if set_as_verified.rowcount > 0 :
                return {"message" : "verified"}
        else :
            return {"message" : "invalid"}
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> 'verifivations' berhasil >> Koneksi di tutup <== \n")


@router_user.put('/api/user/single/update-signature' , tags=['USERS'])
async def updateUserSignature(data : UpdateSignature):
    
    def saveSignature () :
        data_url = data.signature
        image_data = data_url.split(",")[1]
        image_bytes = base64.b64decode(image_data)
        token_name = secrets.token_hex(10)+"."+"png"
        generated_name = token_name
        from io import BytesIO
        image_stream = BytesIO(image_bytes)
        push_the_file = drive.put(generated_name[1:], image_stream)
        return push_the_file
    
    try:
        conn = engine.connect()
        # print(data.signature)
        save_signature_to_cloud = saveSignature()
        # Delete signature jika sudah ada
        chek_signature_exist = conn.execute(user_data.select().where(user_data.c.id == data.id)).first()
        if chek_signature_exist.signature is not None :
            delete_signature = conn.execute(user_data.update().values(signature = None).where(user_data.c.id == data.id))
            deleted_file = drive.delete(chek_signature_exist.signature)
            if delete_signature.rowcount > 0 and deleted_file:
                update_user_signature = conn.execute(user_data.update().values(signature = save_signature_to_cloud).where(user_data.c.id == data.id))
                if update_user_signature.rowcount > 0 :
                    return {"message": "user signature has been updated"}
        else :
            update_signature_if_not_exist = conn.execute(user_data.update().values(signature = save_signature_to_cloud).where(user_data.c.id == data.id))
            if update_signature_if_not_exist.rowcount > 0 :
                return {"message": "user signature has been added"}
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> 'updateUserSignature' berhasil >> Koneksi di tutup <== \n")



# @router_user.put('/api/user/single/show-signature/{user_id}' , tags=['USERS'])
# async def showUserSignature(user_id:int):
#     try:
#         conn = engine.connect()
#         get_signature = conn.execute(user_data.select().where(user_data.c.id == user_id))
#         if get_signature is not None :
#             return {
#                 "user_id" : "",
#                 "signature" : ""
#             }
#     except SQLAlchemyError as e:
#         print("terdapat error di showUserSignature ==> ", e)
#     finally:
#         conn.close()
#         print("\n ==> 'showUserSignature' berhasil >> Koneksi di tutup <== \n")





@router_user.get('/api/user/ip', tags=['IP'])
async def clienIP(req: Request):
    clien_ip = req.client.host
    
    return {"IP" : clien_ip}