# Variable class untuk menampung data yang akang di eksekusi oleh query
from pydantic import BaseModel
from datetime import time, date
from typing import Optional

# !USER
class LoginData(BaseModel):
    email: str
    encpass: str
    user_device: str
    
class Verifications(BaseModel):
    user_id : int
    code : int

class RegisterData(BaseModel):
    first_name:str
    last_name: Optional[str] = None
    alamat: str
    no_telepon: str
    email:str
    password:str
    j_kelamin: str
    role: str

class EditDataProfile(BaseModel):
    user_id: int
    first_name:str
    last_name: str
    alamat: str
    no_telepon: str
    email:str

class changePassword(BaseModel):
    user_id: int
    encpass: str

class AttendanceInputData(BaseModel):
    user_id:int
    presenting: str
    
    
    
class AttendanceRules(BaseModel):
    title : str
    work_start_time : time
    work_times_up : time
    late_deadline : int
    description : str

class AttendanceRulesActivation(BaseModel):
    id : int
    usage : bool
    
class UpdateRole(BaseModel):
    id: int
    role: str
    
class userScanning(BaseModel):
    user_id: int
    status: str
    
class QrcodeIsScanning(BaseModel):
    id : int
    tmstmp : str
    status : str

class PersonalLeave(BaseModel):
    user_id: int
    start_date : date
    end_date : date
    descriptions: str
    
class UserPermission(BaseModel):
    user_id: int
    reason: str
    created_at: date
    
    
class userSick(BaseModel):
    user_id : int
    descriptions: str
    options: str
