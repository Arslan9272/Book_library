# auth.py
from datetime import datetime, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.context import CryptContext  # type: ignore
from database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from models import Users

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

Secret_key = '19fndvdvndir98r398cnene939843'
Algorithm = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str  

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

def authenticate_user(username: str, password: str, db: Session):
    user = db.query(Users).filter(Users.username == username).first()
    if not user or not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username: str, user_id: int, role:str,expires_delta: timedelta) -> str:
    encode = {'sub': username, "id": user_id,"role":role}
    expires = datetime.utcnow() + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, Secret_key, algorithm=Algorithm)

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, Secret_key, algorithms=[Algorithm])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate the user')
        return {'username': username, 'id': user_id, 'user_role':user_role}
    except JWTError:
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate the user')

@router.post('/create', status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    existing_user = db.query(Users).filter((Users.username == create_user_request.username) | 
                                             (Users.email == create_user_request.email)).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Username or Email already exists')

    user_model = Users(
        username=create_user_request.username,
        email=create_user_request.email,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        is_active=True
    )
    db.add(user_model)
    db.commit()
    db.refresh(user_model)
    return user_model

@router.post('/token', response_model=Token)
async def authenticate_request(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
       raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid username or password')
    token = create_access_token(user.username, user.id, user.role,timedelta(minutes=20))
    return {'access_token': token, 'token_type': 'bearer'}
