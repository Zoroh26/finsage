from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email:EmailStr
    password:str
    name:str
    age:int
    income:int
    risk_tolerance:str

class UserLogin(BaseModel):
    email:EmailStr
    password:str