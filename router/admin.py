from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session  # type: ignore
from typing import Annotated
from .auth import get_current_user
from models import Todos
from database import SessionLocal

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_depency = Annotated[dict, Depends(get_current_user)]

@router.get('/todo')
async def read_todo(db: db_dependency, user: user_depency  ):
    if user is None or user.get('id') != 'admin':
        return HTTPException(status_code=401,details='Authentication Failed')
    return db.query(Todos).all()

@router.delete('/delete/{todo_id}')
async def delete_admin(db:db_dependency, user:user_depency,todo_id:int):
    if user is None or user.get('id')!='admin':
        return HTTPException(status_code=401,detail='authentication failed')
    todo_model= db.query(Todos).filter(Todos.id==todo_id).first()
    if todo_model is None:
        return HTTPException(status_code=404,detail='todo not found')
    
    db.query(Todos).filter(Todos.id == todo_id).delete()
    db.commit()

