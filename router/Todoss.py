from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session  # type: ignore
from typing import Annotated
from .auth import get_current_user
from models import Todos
from database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_depency = Annotated[dict, Depends(get_current_user)]

class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=60)
    priority: int = Field(gt=0, lt=6)
    complete: bool

@router.get('/')
async def read_all(user: user_depency, db: db_dependency):
    todos = db.query(Todos).filter(Todos.owner_id == user.get('id')).all()
    return todos

@router.get('/todos/{todos_id}')
async def read_todo(user:user_depency,todos_id: int, db: db_dependency):
    todo_model = db.query(Todos).filter(Todos.owner_id == user.get('id')).filter(Todos.id == todos_id).first()
    if todo_model is not None:
        return todo_model
    else:
        raise HTTPException(status_code=404, detail='Not found')
    
@router.post('/todo')
async def create_todo(user: user_depency, todo_request: TodoRequest, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Unauthorized')
    todo_model = Todos(**todo_request.dict(), owner_id=user.get('id'))
    
    db.add(todo_model)
    db.commit()
    db.refresh(todo_model)
    return todo_model

@router.put('/todo/{todo_id}')
async def update_todo(user:user_depency,db: db_dependency, todo_request: TodoRequest, todo_id: int = Path(gt=0)):
    todo_model = db.query(Todos).filter(Todos.owner_id == user.get('id')).filter(Todos.id == todo_id).first()

    if todo_model is None:
        raise HTTPException(status_code=404, detail='Not found')
    
    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete

    db.commit()
    db.refresh(todo_model)
    return todo_model

@router.delete('/todos/{todo_id}')
async def delete_todo(user:user_depency,todo_id: int, db: db_dependency):
    todo_model = db.query(Todos).filter(Todos.owner_id == user.get('id')).filter(Todos.id == todo_id).first()

    if todo_model is None:
        raise HTTPException(status_code=404, detail='Not found')
    
    db.delete(todo_model)
    db.commit()
    return {"detail": "Todo deleted successfully"}
