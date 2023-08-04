from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import select
from config.db import engine
from fastapi import APIRouter, HTTPException, UploadFile, File
from models.tabel import user_data, presence, detail_user_scanned, user_has_scanned_in, user_has_scanned_out
import base64
from config.picture_drive import drive


detail_scanned = APIRouter()



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





@detail_scanned.get('/api/user-detail-scanned/scaned-in', tags=["DETAIL SCANNED"])
async def detailScannedIn():
    try:
        conn = engine.connect()
        datas = []
        
        join_query = detail_user_scanned.join(
            user_data, detail_user_scanned.c.user_id == user_data.c.id
            ).join(
                user_has_scanned_in, detail_user_scanned.c.scan_in_id == user_has_scanned_in.c.id
                ).join(
                    presence, detail_user_scanned.c.presence_id == presence.c.id
                    )
        result_join_query = select([
            user_data.c.first_name,
            user_data.c.last_name,
            user_data.c.profile_picture,
            user_has_scanned_in.c.created_at,
            presence.c.descriptions
            ]).select_from(join_query)
        execute_join_query = conn.execute(result_join_query).fetchall()
        
        for datas_from_join in execute_join_query :
            print(datas_from_join)
            datas.append({
                "first_name": datas_from_join.first_name,
                "last_name": datas_from_join.last_name,
                "profile_picture": await profilePictures(datas_from_join.profile_picture),
                "created_at": datas_from_join.created_at,
                "descriptions": datas_from_join.descriptions
                })
        
        
        return {"detail_scan_in" :datas}
        
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> 'detailScannedIn' berhasil >> Koneksi di tutup <== \n")


@detail_scanned.get('/api/user-detail-scanned/scaned-out', tags=["DETAIL SCANNED"])
async def detailScannedOut():
    try:
        conn = engine.connect()
        datas = []
        
        
        join_query = detail_user_scanned.join(
            user_data, detail_user_scanned.c.user_id == user_data.c.id
            ).join(
                user_has_scanned_out, detail_user_scanned.c.scan_out_id == user_has_scanned_out.c.id
                ).join(
                    presence, detail_user_scanned.c.presence_id == presence.c.id
                    )
        result_join_query = select(user_data, user_has_scanned_out, presence).select_from(join_query)
        execute_join_query = conn.execute(result_join_query).fetchall()
        
        
        
        for datas_from_join in execute_join_query :
            datas.append({
                "first_name": datas_from_join.first_name,
                "last_name": datas_from_join.last_name,
                "profile_picture": await profilePictures(datas_from_join.profile_picture),
                "created_at": datas_from_join.created_at,
                "total": datas_from_join.total_hours_worked,
                "descriptions": datas_from_join.descriptions
                })
        
        return {"detail_scan_out" :datas}
        
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> 'detailScannedIn' berhasil >> Koneksi di tutup <== \n")
