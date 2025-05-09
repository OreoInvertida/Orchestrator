from pydantic import BaseModel

class UserData(BaseModel):
    user_id: int
    name: str
    email: str
    address: str
    password: str
