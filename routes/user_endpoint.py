from sqlalchemy.exc import SQLAlchemyError
from config.db import engine
from fastapi import APIRouter, HTTPException, UploadFile, File
from models.tabel import user_data, attendance, presence
from schema.schemas import (LoginData, RegisterData, EditDataProfile, changePassword, UpdateRole)
import secrets
import base64
from deta import Deta

router_user = APIRouter()

deta = Deta("c0nRwAq5JJSf_ti5F9A5g6Evx5jESXGe8aviyDRaTVQPE")
drive = deta.Drive("profile_photo")


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
        response = conn.execute(user_data.select().where(user_data.c.email == data.email)).first()
        if response :
            return {
                "id" : response.id, 
                "role": response.role,
                "encpass": response.password
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
        is_email_duplicate = conn.execute(user_data.select().where(user_data.c.email == data.email)).fetchall()
        # response = {}
        if is_email_duplicate :
            raise HTTPException(status_code=409, detail="Email telah digunakan")
        else :
            conn.execute(user_data.insert().values(first_name = data.first_name, last_name = data.last_name, alamat=data.alamat, no_telepon = data.no_telepon, email = data.email, password = data.password, j_kelamin = data.j_kelamin, role = data.role))
            response = conn.execute(user_data.select().where(user_data.c.first_name == data.first_name, user_data.c.last_name == data.last_name)).first()
            if response :
                fullname = f"{response.first_name} {response.last_name}"
                conn.execute(attendance.insert().values(user_id = response.id))
                attendance_table_response = conn.execute(attendance.select().where(attendance.c.user_id == response.id)).first()
                if attendance_table_response :
                    return {
                        "message" : "register success",
                        "name": fullname,
                        "role": response.role
                        }
            elif not response :
                raise HTTPException(status_code=404, detail="gagal menyimpan data")
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        if response :
            print(f"\n \033[4;32m ==> OK[200]: {response.first_name} --> 'register' | CONNECTION KILLED <== \n")


@router_user.put('/api/user/edit-profile', tags=["USERS"])
async def edifProfileData( data: EditDataProfile):
    try:
        conn = engine.connect()
        conn.execute(user_data.update().values(first_name = data.first_name, last_name = data.last_name, alamat = data.alamat, no_telepon = data.no_telepon).where(user_data.c.id == data.user_id))
        response = conn.execute(user_data.select().where(user_data.c.id == data.user_id)).first()
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
        if is_user_exist :
            with image.file as f:
                fileName = image.filename
                extensions = fileName.split(".")[1]
                if extensions not in ['png', 'jpg', 'jpeg']:
                    return {
                        "status": "error",
                        "detail": "file extension is not allowed"
                        }
                token_name = secrets.token_hex(10)+"."+extensions
                generated_name = token_name
                push_the_file = drive.put(generated_name[1:], f)
                conn.execute(user_data.update().values(profile_picture = push_the_file).where(user_data.c.id == id))
                result = conn.execute(user_data.select().where(user_data.c.id == id, user_data.c.profile_picture == push_the_file)).first().profile_picture
                if result :
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
        return {
            "id": response.id,
            "first_name": response.first_name,
            "last_name": response.last_name,
            "alamat":response.alamat,
            "no_telepon": response.no_telepon,
            "email": response.email,
            "j_kelamin": response.j_kelamin,
            "role": response.role,
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
        if get_presence_data or not get_presence_data:
            if get_presence_data :
                delete_presence_data = conn.execute(presence.delete().where(presence.c.attendance_id == get_presence_data.attendance_id))
            # ?Delete Attendance_data
            if delete_presence_data.rowcount > 0 :
                delete_attendance_data = conn.execute(attendance.delete().where(attendance.c.id == get_attendance_data.id))
                # ?Delete user data and delete profile picture
                if delete_attendance_data.rowcount > 0 :
                    delete_user_data = conn.execute(user_data.delete().where(user_data.c.id == id))
                    if delete_user_data.rowcount > 0 :
                        if get_profile_picture_name:
                            drive.delete(get_profile_picture_name)
                        return {"message":"user data has been deleted"}

    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> 'deletUserData' berhasil >> Koneksi di tutup <== \n")


@router_user.put('/api/user/single/update-user-role' , tags=['USERS'])
async def updateUserRole(data : UpdateRole):
    try:
        conn = engine.connect()
        update_user_role = conn.execute(user_data.update().values(role = data.role).where(user_data.c.id == data.id))
        if update_user_role.rowcount > 0 :
            return {"message": "user role has been updated"}
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> 'updateUserRole' berhasil >> Koneksi di tutup <== \n")
