from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc
from config.db import engine
from schema.schemas import QrcodeIsScanning 
from fastapi import APIRouter, HTTPException
from models.tabel import qrcode_data, qrcode_data_in, qrcode_data_out
from config.jakarta_timezone import jkt_current_date, jkt_current_datetime
# from config.jakarta_timezone import jkt_current_date
import datetime
import pytz
# from schema.schemas import 

router_qrcode_data = APIRouter()


@router_qrcode_data.get("/api/qrcode/today-qrcode-data/{data_option}", tags=["QRCODE DATA"])
async def getQrCodeData(data_option : str):

    # ===================== tmstmp =====================
    # Membuat timestamp saat ini
    timestamp = jkt_current_datetime()
    # timestamp dalam format khusus dengan padding nol
    timestamp_string = timestamp.strftime("%Y%m%d%H%M%S%f")
    # 20 digit pertama
    timestamp_string = timestamp_string[:20]
    # ==================================================
    date_now_for_compare = timestamp.strftime("%Y-%m-%d")

    try:
        conn = engine.connect()
        query_qrcode_in = qrcode_data_in.select().order_by(desc(qrcode_data_in.c.created_at))
        query_qrcode_out = qrcode_data_out.select().order_by(desc(qrcode_data_out.c.created_at))
        response_qrcode_in = conn.execute(query_qrcode_in).fetchall()
        response_qrcode_out = conn.execute(query_qrcode_out).fetchall()
        
        if len(response_qrcode_in) == 0 or len(response_qrcode_out) == 0:
            # belum ada data masuk dan keluar maka insert data
            insert_data_qrcode_in = conn.execute(qrcode_data_in.insert().values(
                tmstmp = timestamp_string, 
                status = "in",
                created_at= jkt_current_date()))
            insert_data_qrcode_out = conn.execute(qrcode_data_out.insert().values(
                tmstmp = timestamp_string,
                status = "out",
                created_at= jkt_current_date()))
            if insert_data_qrcode_in.rowcount > 0 and insert_data_qrcode_out.rowcount > 0 :
                # insert data berhasil
                # dan tampilin data
                result_data_qrcode_in = conn.execute(qrcode_data_in.select().where(qrcode_data_in.c.tmstmp == timestamp_string)).first()
                result_data_qrcode_out = conn.execute(qrcode_data_out.select().where(qrcode_data_out.c.tmstmp == timestamp_string)).first()
                if result_data_qrcode_in and result_data_qrcode_out:
                    # jika terdapat data
                    # insert data ke 'tabel qrcode_data'
                    insert_qrcode_data = conn.execute(qrcode_data.insert().values(
                        qrcode_in_id = result_data_qrcode_in.id, 
                        qrcode_out_id = result_data_qrcode_out.id, 
                        tmstmp = timestamp_string,
                        created_at= jkt_current_date()))
                    if insert_qrcode_data.rowcount > 0:
                        # jika data 'tabel qrcode_data' berhasil di input
                        # check data yang direquest user
                        
                        if data_option == "in":
                            # data yang direquest user 'in'
                            get_qrcode_data = conn.execute(qrcode_data.select().where(qrcode_data.c.tmstmp == timestamp_string)).first()
                            get_qrcode_data_in = conn.execute(qrcode_data_in.select().where(qrcode_data.c.tmstmp == get_qrcode_data.tmstmp)).first()
                            return get_qrcode_data_in
                        
                        if data_option == "out":
                            # data yang direquest user 'in'
                            get_qrcode_data = conn.execute(qrcode_data.select().where(qrcode_data.c.tmstmp == timestamp_string)).first()
                            get_qrcode_data_in = conn.execute(qrcode_data_in.select().where(qrcode_data.c.tmstmp == get_qrcode_data.tmstmp)).first()
                            return get_qrcode_data_in
        
        else :
            # if response_qrcode_in and response_qrcode_out:
            get_last_record_date_from_db_qrcode_in = str(response_qrcode_in[0].created_at)
            get_last_record_date_from_db_qrcode_out = str(response_qrcode_out[0].created_at)
            if get_last_record_date_from_db_qrcode_in == date_now_for_compare:
                if data_option == "in":
                    # data yang direquest user 'in'
                    qrcode_in_is_exist = qrcode_data_in.select().order_by(desc(qrcode_data_in.c.created_at))
                    result_qrcode_in_is_exist = conn.execute(qrcode_in_is_exist).fetchall()
                    return result_qrcode_in_is_exist[0]
                if data_option == "out":
                    # data yang direquest user 'in'
                    qrcode_out_is_exist = qrcode_data_out.select().order_by(desc(qrcode_data_out.c.created_at))
                    result_qrcode_in_is_exist = conn.execute(qrcode_out_is_exist).fetchall()
                    return result_qrcode_in_is_exist[0]
            else :
                print("data hari ini tidak ada")
                insert_data_qrcode_in = conn.execute(qrcode_data_in.insert().values(
                    tmstmp = timestamp_string, 
                    status = "in",
                    created_at= jkt_current_date()))
                insert_data_qrcode_out = conn.execute(qrcode_data_out.insert().values(
                    tmstmp = timestamp_string, 
                    status = "out",
                    created_at= jkt_current_date()))
                if insert_data_qrcode_in.rowcount > 0 and insert_data_qrcode_out.rowcount > 0 :
                    qrcode_in_after_insert = conn.execute(qrcode_data_in.select().where(qrcode_data_in.c.tmstmp == timestamp_string)).first()
                    qrcode_out_after_insert = conn.execute(qrcode_data_out.select().where(qrcode_data_out.c.tmstmp == timestamp_string)).first()
                    print("maka insert_qrcode_data")
                    insert_qrcode_data = conn.execute(qrcode_data.insert().values(
                        qrcode_in_id = qrcode_in_after_insert.id, 
                        qrcode_out_id = qrcode_out_after_insert.id, 
                        tmstmp = timestamp_string,
                        created_at= jkt_current_date()))
                    if insert_qrcode_data.rowcount > 0:
                        print("berhasil insert_qrcode_data")
                        get_qrcode_data = conn.execute(qrcode_data.select().where(qrcode_data.c.tmstmp == timestamp_string)).first()
                        if data_option == "in":
                            get_qrcode_data_in_exist = conn.execute(qrcode_data_in.select().where(qrcode_data_in.c.tmstmp == get_qrcode_data.tmstmp)).first()
                            return get_qrcode_data_in_exist
                        
                        if data_option == "out":
                            get_qrcode_data_out_exist = conn.execute(qrcode_data_out.select().where(qrcode_data_out.c.tmstmp == get_qrcode_data.tmstmp)).first()
                            return get_qrcode_data_out_exist
                    
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> getQrCodeData berhasil >> Koneksi di tutup <== \n")
        



@router_qrcode_data.post("/api/qrcode/qrcode-data-scan-in/validator/{data_option}", tags=["QRCODE DATA"])
async def qrcodeScanInValidator (data_options : QrcodeIsScanning) :
    try :
        conn = engine.connect()
        scanning_in_query = conn.execute(qrcode_data_in.select().where(qrcode_data_in.c.id == data_options.id, qrcode_data_in.c.tmstmp == data_options.tmstmp,  qrcode_data_in.c.status == data_options.status)).first()
        
        if scanning_in_query:
            return {"message" : "data has been validated"}
        else :
            return {"message" : "data couldn't be validated"}
        
    except SQLAlchemyError as e :
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> getQrCodeData berhasil >> Koneksi di tutup <== \n")
        


@router_qrcode_data.post("/api/qrcode/qrcode-data-scan-out/validator/{data_option}", tags=["QRCODE DATA"])
async def qrcodeScanOutValidator (data_options : QrcodeIsScanning) :
    try :
        conn = engine.connect()
        scanning_in_query = conn.execute(qrcode_data_out.select().where(qrcode_data_out.c.id == data_options.id, qrcode_data_out.c.tmstmp == data_options.tmstmp,  qrcode_data_out.c.status == data_options.status)).first()
        
        if scanning_in_query:
            return {"message" : "data has been validated"}
        else :
            return {"message" : "data couldn't be validated"}
        
    except SQLAlchemyError as e :
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> getQrCodeData berhasil >> Koneksi di tutup <== \n")
        
