
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc
from config.db import engine
from sqlalchemy.sql import select
from schema.schemas import userSick 
from fastapi import APIRouter, HTTPException
from models.tabel import presence, sick, attendance, user_data
from config.jakarta_timezone import jkt_current_date
from config.picture_drive import drive
from config.email_sender_message import EmailSender
import base64


router_sick_user = APIRouter()




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






@router_sick_user.post('/api/attendance/presence/sick-user/', tags=['SICK USER'])
async def sickUser(data:userSick):
    try :
        conn = engine.connect()
        curr_date = jkt_current_date()
        get_user_sick_data = conn.execute(sick.select().where(sick.c.user_id == data.user_id)).first()
        join_query = attendance.join(user_data, attendance.c.user_id == user_data.c.id)
        resp_join = select([user_data.c.first_name, user_data.c.last_name, user_data.c.email]).select_from(join_query).where(user_data.c.id == data.user_id)
        exec_join = conn.execute(resp_join).first()
        get_attendance_data = conn.execute(attendance.select().where(attendance.c.user_id == data.user_id)).first()
        
        # return get_attendance_data
        
        
        if data.options == "sakit":
            insert_sick_user = conn.execute(sick.insert().values(user_id = data.user_id, descriptions = data.descriptions, created_at = curr_date))
            if insert_sick_user.rowcount > 0 :
                get_user_sick_data = conn.execute(sick.select().where(sick.c.user_id == data.user_id)).first()
                get_curr_presence = conn.execute(presence.select().where(presence.c.attendance_id == get_attendance_data.id)).first()
                update_presence = conn.execute(presence.update().values(presence_status = 'sakit', sick = get_user_sick_data.id, descriptions = get_user_sick_data.descriptions).where(presence.c.attendance_id == get_attendance_data.id, presence.c.created_at_in == data.created_at_in))
                if update_presence.rowcount > 0 :
                    presence_dates = get_curr_presence.created_at_in
                    EmailSender(reciver_email=exec_join.email, reciver_name=f"{exec_join.first_name} {exec_join.last_name}", reciver_presence_status="Sakit diperbaharui", description="sakit", date=curr_date).sender()
                    return {
                            "message": "success",
                            "name": f"{exec_join.first_name} {exec_join.last_name}",
                            "presence_status": get_curr_presence.presence_status,
                            "presence_date" : presence_dates.date(),
                            "update_at" : get_user_sick_data.created_at
                            }
        elif data.options == 'alfa':
            update_presence = conn.execute(presence.update().values(presence_status = data.options, sick = None, descriptions = 'tanpa keterangan').where(presence.c.attendance_id == get_attendance_data.id))
            delete_sick_user = conn.execute(sick.delete().where(sick.c.user_id == data.user_id))
            if delete_sick_user.rowcount > 0 :
                get_user_sick_data = conn.execute(sick.select().where(sick.c.user_id == data.user_id)).first()
                get_curr_presence = conn.execute(presence.select().where(presence.c.attendance_id == get_attendance_data.id)).first()
                presence_dates = get_curr_presence.created_at_in
                return {
                        "message": "success",
                        "name": f"{exec_join.first_name} {exec_join.last_name}",
                        "presence_status": get_curr_presence.presence_status,
                        "presence_date" : presence_dates.date(),
                        "update_at" : None
                        }
    except SQLAlchemyError as e :
        print("terdapat error di 'sickUser' --> ", e)
    finally :
        conn.close()
        print("\n --> 'sickUser' berhasil >> Koneksi di tutup <-- \n")
    
    

@router_sick_user.get('/api/attendance/presence/multi/user/', tags=['SICK USER'])
async def showAllUser():
    try :
        conn = engine.connect()
        
        join_query = user_data.join(
            attendance, user_data.c.id == attendance.c.user_id
            ).join(
                presence, presence.c.attendance_id == attendance.c.id)
        result_join = select([user_data.c.id, user_data.c.first_name, user_data.c.last_name, presence.c.id, presence.c.created_at_in, presence.c.presence_status, attendance.c.id, user_data.c.profile_picture,]).select_from(join_query)
        exec_join = conn.execute(result_join).fetchall()
        
        async def userInSickTable(user_id:int, options:str):
            try :
                conn = engine.connect()
                sick_data = conn.execute(sick.select().where(sick.c.user_id == user_id)).first()
                if sick_data:
                    created_at = sick_data['created_at']
                    descriptions = sick_data['descriptions']
                    if options == "created_at":
                        return created_at
                    elif options  == "descriptions":
                        return descriptions
                        
                else:
                    return None
            except SQLAlchemyError as e :
                print("terdapat error di 'userInSickTable' --> ", e)
            finally :
                conn.close()
                print("\n --> 'userInSickTable >> Koneksi di tutup <-- \n")
        
        
        
        return_datas = []
        modify_datas = []
        
        for datas in exec_join :
            modify_datas.append(dict(datas))
        
        
        for modify_items in modify_datas :
            if modify_items['profile_picture'] != None :
                modify_items['profile_picture'] = await profilePictures(modify_items['profile_picture'])
            
            return_datas.append({
                "user_id": modify_items['id'],
                "first_name": modify_items['first_name'],
                "last_name": modify_items['last_name'],
                "presence_id": modify_items['id_1'],
                "presence_status": modify_items['presence_status'],
                "created_at_in": modify_items['created_at_in'],
                "attendance_id": modify_items['id_2'],
                "profile_picture":modify_items['profile_picture'],
                'updated_at' : await userInSickTable(modify_items['id'], "created_at"),
                'descriptions' : await userInSickTable(modify_items['id'], "descriptions")
                })
        return return_datas
    except SQLAlchemyError as e :
        print("terdapat error di 'showAllUser' --> ", e)
    finally :
        conn.close()
        print("\n --> 'showAllUser' berhasil >> Koneksi di tutup <-- \n")
    
    
    
    

