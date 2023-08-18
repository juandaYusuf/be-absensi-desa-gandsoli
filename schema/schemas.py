# Variable class untuk menampung data yang akang di eksekusi oleh query
from pydantic import BaseModel, Field
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
    apply_docs: str
    descriptions: str
    
class UserPermission(BaseModel):
    user_id: int
    reason: str
    start_date : str
    end_date: Optional[str] = Field(default=None)
    
class userSick(BaseModel):
    user_id : int
    descriptions: str
    created_at_in : str
    options: str

class UpdateSignature(BaseModel):
    id: int
    signature: str
    
class UpdatePermissionAgreement(BaseModel):
    user_id: int
    permission_id : int
    agreement: str
    docs: Optional[str] = Field(default=None)
    
class UpdatePersonalLeaveAgreement(BaseModel):
    user_id: int
    personal_leave_id : int
    agreement: str
    agreement_docs: Optional[str] = Field(default=None)