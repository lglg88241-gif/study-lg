from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer ,OAuth2PasswordRequestForm

from sqlalchemy.orm import Session
from pydantic import BaseModel
from jose import JWTError, jwt

from database.mysql_db import get_db
from models.user import User
from utils.auth_utils import get_password_hash, verify_password, create_access_token
from utils.auth_utils import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/auth", tags=["身份验证"])

# 前端发来的请求体规范
class UserAuth(BaseModel):
    username: str
    password: str

# 令牌响应规范
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# 🌟 核心门卫：提取 Token 并去数据库核实身份
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证失败，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", summary="新用户注册")
async def register(user_data: UserAuth, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user_data.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已被占用")
    
    new_user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "注册成功", "user_id": new_user.id}

@router.post("/login", response_model=Token, summary="用户登录")
# 🌟 修改点 2：把 user_data 换成 form_data: OAuth2PasswordRequestForm = Depends()
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 🌟 下面的 user_data 全部换成 form_data
    db_user = db.query(User).filter(User.username == form_data.username).first()
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}