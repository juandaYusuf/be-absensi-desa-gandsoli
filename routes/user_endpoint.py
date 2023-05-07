from sqlalchemy.exc import SQLAlchemyError
from config.db import engine
from fastapi import APIRouter, HTTPException, UploadFile, File
from models.tabel import (user_data)
from schema.schemas import (LoginData, RegisterData)
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

@router_user.post('/login', tags=["USERS"])
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


@router_user.post('/register', tags=["USERS"])
async def register(data: RegisterData):
    try:
        conn = engine.connect()
        is_email_duplicate = conn.execute(user_data.select().where(user_data.c.email == data.email)).fetchall()
        response = {}
        if is_email_duplicate :
            raise HTTPException(status_code=409, detail="Email telah digunakan")
        else :
            conn.execute(user_data.insert().values(first_name = data.first_name, last_name = data.last_name, alamat=data.alamat, no_telepon = data.no_telepon, email = data.email, password = data.password, j_kelamin = data.j_kelamin, role = data.role))
            response = conn.execute(user_data.select().where(user_data.c.first_name == data.first_name, user_data.c.last_name == data.last_name)).first()
            if response :
                fullname = f"{response.first_name} {response.last_name}"
                return {
                    "message" : "register success",
                    "name": fullname
                    }
            elif not response :
                raise HTTPException(status_code=404, detail="gagal menyimpan data")
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        if response :
            print(f"\n \033[4;32m ==> OK[200]: {response.first_name} --> 'register' | CONNECTION KILLED <== \n")


#! upload foto profile
@router_user.post('/upload-profile-picture/', tags=["USERS"])
async def uploadprofileimage(id:int, image: UploadFile =File(...)):
    try:
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
            conn = engine.connect()
            conn.execute(user_data.update().values(profile_picture = push_the_file).where(user_data.c.id == id))
            result = conn.execute(user_data.select().where(user_data.c.id == id, user_data.c.profile_picture == push_the_file)).first().profile_picture
            if result :
                return {"message":"file succesfully uploaded"}
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print(f"\n \033[4;32m ==> OK[200]: --> 'register' | CONNECTION KILLED <== \n")

# !Get profile picture by user id
@router_user.get('/profile-picture/{id}', tags=["USERS"])
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


@router_user.get('/user-detail/{id}', tags=['USERS'])
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
