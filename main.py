import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from database import SessionLocal, SQLALCHEMY_DATABASE_URL, Base
from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel
from user import User, Token, TokenData, UserInDB

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

users_db = {}


pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()
Base.metadata.create_all(bind=create_engine(SQLALCHEMY_DATABASE_URL))

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(username: str):
    return users_db.get(username)

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    
    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/users/")
async def create_User(username: str, email: str, password: str):
    if username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user_id = len(users_db) + 1
    hashed_password = get_password_hash(password)
    
    user = UserInDB(
        id=user_id,
        username=username,
        email=email,
        hashed_password=hashed_password,
        full_name=None,
        disabled=False,
    )
    
    users_db[user.username] = user
    return user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user

def update_user(username: str, name: str, email: str):
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.username = name
    user.email = email
    return {"message": "User updated successfully", "user": user}

@app.put("/users/{username}")
async def update_User(
    username: str,
    email: str | None = None,
    full_name: str | None = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.username != username:
        raise HTTPException(status_code=403, detail="You can only update your own account")

    if email:
        user.email = email
    if full_name:
        user.full_name = full_name

    users_db[username] = user

    return {"message": "User updated successfully", "user": user}

def delete_user(username: str):
    if username in users_db:
        del users_db[username]
        return {"message": "User deleted successfully"}
    
    raise HTTPException(status_code=404, detail="User not found")

@app.delete("/users/{username}")
async def delete_User(username: str, current_user: Annotated[UserInDB, Depends(get_current_active_user)]):
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.username != username:
        raise HTTPException(status_code=403, detail="You can only delete your own account")

    del users_db[username]

    return {"message": "User deleted successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
