from sqlalchemy.exc import SQLAlchemyError
from config.db import engine
from fastapi import APIRouter, HTTPException
from models.tabel import attendance_rules
from schema.schemas import (AttendanceRules, AttendanceRulesActivation)



router_attendance_rules = APIRouter()

@router_attendance_rules.get("/api/attendance_rule/show-all-attendance-rules", tags=["ATTENDANCE RULES"])
async def showAttendancerule():
    try:
        conn = engine.connect()
        response = conn.execute(attendance_rules.select()).fetchall()
        return response
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> addAttendancerule berhasil >> Koneksi di tutup <== \n")



@router_attendance_rules.post("/api/attendance_rule/add-attendance-rule", tags=["ATTENDANCE RULES"])
async def addAttendanceRule(data: AttendanceRules):
    try:
        conn = engine.connect()
        response = conn.execute(
            attendance_rules.insert().values(
                title = data.title,
                work_start_time = data.work_start_time,
                work_times_up = data.work_times_up,
                late_deadline = data.late_deadline,
                description=data.description))
        if response.rowcount > 0:
            return {"message": "data has been posted"}
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> addAttendanceRule berhasil >> Koneksi di tutup <== \n")

@router_attendance_rules.delete("/api/attendance_rule/delete-attendance-rules/{id}", tags=["ATTENDANCE RULES"])
async def deleteAttendancerule(id: int):
    try:
        conn = engine.connect()
        response = conn.execute(attendance_rules.delete().where(attendance_rules.c.id == id))
        if response.rowcount > 0 :
            return {"message": "data has been deleted"}
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> addAttendancerule berhasil >> Koneksi di tutup <== \n")

@router_attendance_rules.put("/api/attendance_rule/usage-attendance-rules", tags=["ATTENDANCE RULES"])
async def usageAttendancerule(data : AttendanceRulesActivation):
    try:
        conn = engine.connect()
        reset_usages = conn.execute(attendance_rules.update().values(usage = 0))
        if reset_usages.rowcount > 0:
            response = conn.execute(attendance_rules.update().values(usage = data.usage).where(attendance_rules.c.id == data.id))
            if response.rowcount > 0 :
                return {"messages" : "attendance_rules has been updated"} 
    except SQLAlchemyError as e:
        print("terdapat error ==> ", e)
    finally:
        conn.close()
        print("\n ==> usageAttendancerule berhasil >> Koneksi di tutup <== \n")

