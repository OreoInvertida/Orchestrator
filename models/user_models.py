from pydantic import BaseModel

class UserData(BaseModel):
    user_id: int
    name: str
    email: str
    address: str
    password: str

class AuthDoc(BaseModel):
    document_id: int
    document_name: str
    document_path:str