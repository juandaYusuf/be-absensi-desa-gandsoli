# Variable class untuk menampung data yang akang di eksekusi oleh query
from pydantic import BaseModel


# !USER
class LoginData(BaseModel):
    email: str
    encpass: str

class RegisterData(BaseModel):
    first_name:str
    last_name: str
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
    
