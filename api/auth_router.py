from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession  # 🌟 必须用这个类型
from pydantic import BaseModel
from jose import JWTError, jwt

from database.mysql_db import get_db
from models.user import User
from utils.auth_utils import get_password_hash, verify_password, create_access_token
from utils.auth_utils import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/auth", tags=["身份验证"])

class UserAuth(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ✅ 1. 门卫鉴权异步改造
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
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
        
    result = await db.execute(select(User).filter(User.username == username))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    return user

# ✅ 2. 注册接口异步改造
@router.post("/register", summary="新用户注册")
async def register(user_data: UserAuth, db: AsyncSession = Depends(get_db)):
    # 🌟 必须使用 await db.execute(select(...))
    result = await db.execute(select(User).filter(User.username == user_data.username))
    db_user = result.scalar_one_or_none()
    
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已被占用")
    
    new_user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password)
    )
    db.add(new_user)
    await db.commit()          # 🌟 必须 await
    await db.refresh(new_user) # 🌟 必须 await
    return {"message": "注册成功", "user_id": new_user.id}

# ✅ 3. 登录接口异步改造
@router.post("/login", response_model=Token, summary="用户登录")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.username == form_data.username))
    db_user = result.scalar_one_or_none()
    
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}