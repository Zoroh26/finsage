from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session
from models.schemas import UserCreate, UserLogin
from models.user import User
from services.auth import hash_password, verify_password
from utils.jwt import create_access_token
from core.database import get_db
from models.user import User
router = APIRouter()

@router.post("/register")
def register(user:UserCreate, db:Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email==user.email).first()
    if db_user:
        raise HTTPException(status_code=400,detail="Email already registered")
    hashed_password = hash_password(user.password)
    new_user = User(
        email=user.email,
        hashed_password=hashed_password,
        name=user.name,
        age=user.age,
        income=user.income,
        risk_tolerance=user.risk_tolerance
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"msg":"User created successfully"}

@router.post("/login")
def login(user:UserLogin, db:Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password,db_user.hashed_password):
        raise HTTPException(status_code=400,detail="Invalid credentials")
    token = create_access_token(data={"sub":db_user.email})
    return {"access_token":token,"token_type":"bearer"}