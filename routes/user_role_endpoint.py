from sqlalchemy.exc import SQLAlchemyError
from config.db import engine
from fastapi import APIRouter
from models.tabel import user_role




router_user_role = APIRouter()



@router_user_role.get('/api/user-role/show-all-user-role' , tags=['USER ROLE'])
async def getUserRole():
    try:
        conn = engine.connect()
        user_role_datas = conn.execute(user_role.select()).fetchall()
        return user_role_datas
    except SQLAlchemyError as e:
        print("terdapat error pada getUserRole ==> ", e)
    finally:
        conn.close()
        print("\n ==> 'getUserRole' berhasil >> Koneksi di tutup <== \n")


