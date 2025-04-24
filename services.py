from sqlalchemy.orm import Session
from user import User
import bcrypt
from datetime import datetime, timedelta, timezone
import jwt
from main import pwd_context, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,users_db
def validate_password(password: str):
    l, u, p, d = 0, 0, 0, 0
    capitalalphabets = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    smallalphabets = "abcdefghijklmnopqrstuvwxyz"
    specialchar = """ ~`!@#$%^&*()_-+={[}]|\:;"'<,>.?/ """
    digits = "0123456789"
    
    if len(password) >= 8:
        for char in password:
            if char in smallalphabets:
                l += 1
            if char in capitalalphabets:
                u += 1
            if char in digits:
                d += 1
            if char in specialchar:
                p += 1
    
    if l >= 1 and u >= 1 and p >= 1 and d >= 1 and len(password) >= 8:
        return True
    else:
        return False

def create_user(db: Session, name: str, email: str, password: str):
    if not validate_password(password):
        return {"error": "choose a stronger password"}
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    db_user = User(name=name, email=email, password=hashed_password, created_date="2025-04-16")
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def login_user(db: Session, user_id: int, password: str):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return {"message": "Invalid username or password"}
    
    if not bcrypt.checkpw(password.encode('utf-8'), db_user.password.encode('utf-8')):
        return {"message": "Invalid username or password"}
    
    if db_user.active == 0:
        return {"message": "User account is inactive"}
    
    return {"message": "Login successful", "user_id": db_user.id}


def read_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def update_user(db: Session, user_id: int, name: str, email: str):
    db_user = db.query(User).filter(User.id == user_id).first()
    db_user.name = name
    db_user.email = email
    db.commit()
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = db.query(User).filter(User.id == user_id).first()
    db.delete(db_user)
    db.commit()
    return {"message": "User deleted successfully"}

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