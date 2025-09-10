from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from core.database import SessionLocal
from core.database import get_db
from controllers.auth import router as auth_router

app = FastAPI()



@app.get("/")
def read_root(db: Session = Depends(get_db)):
    return {"message": "Connected to database"}

app.include_router(auth_router, prefix="/auth")