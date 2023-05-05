from sqlalchemy.exc import SQLAlchemyError
from config.db import engine
from fastapi import APIRouter, HTTPException
from models.tabel import (user_data)
from schema.schemas import (LoginData, RegisterData)


router_user = APIRouter()

#! USER  ==============================================================================
@router_user.get('/')
async def fetchAllUserData():
    try:
        conn = engine.connect()
        return {"Hallo": "Koneksi ke DataBase Berhasil...!"}
    except SQLAlchemyError as e:
        print("terdapat error ==>> ", e)
    finally:
        conn.close()
        print("\n ==>> fetchAllUserData berhasil >> Koneksi di tutup <<== \n")

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
        print("terdapat error ==>> ", e)
    finally:
        conn.close()
        if response :
            print(f"\n \033[4;32m ==>> OK[200]: {response.first_name} --> 'login' | CONNECTION KILLED <<== \n")

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
        print("terdapat error ==>> ", e)
    finally:
        conn.close()
        if response :
            print(f"\n \033[4;32m ==>> OK[200]: {response.first_name} --> 'register' | CONNECTION KILLED <<== \n")