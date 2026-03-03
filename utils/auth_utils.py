import logging
from datetime import datetime, timedelta ,timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

# 🌟 1. 配置密码加密上下文
# 使用 bcrypt 算法，这是目前工业界最推荐的强力哈希算法之一
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# 🌟 2. JWT 配置（这些以后可以抽离到 config.py）
SECRET_KEY = "your-super-secret-key-don-not-leak" # 签名密钥，绝对不能泄露
ALGORITHM = "HS256" # 加密算法
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 令牌有效期：24小时

logger = logging.getLogger(__name__)


# --- 密码相关函数 ---
def get_password_hash(password: str) -> str:
    """将明文密码转化为不可逆的哈希字符串"""
    return pwd_context.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码和哈希密码是否匹配"""
    return pwd_context.verify(plain_password, hashed_password)


# --- JWT 令牌相关函数 ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """为登录成功的用户签发一张‘电子通行证’ (JWT)"""
    to_encode = data.copy()
    if expires_delta:
        # 🌟 替换为 .now(timezone.utc)
        expire = datetime.now(timezone.utc) + expires_delta 
    else:
        # 🌟 替换为 .now(timezone.utc)
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 将过期时间写入负载 (Payload)
    to_encode.update({"exp": expire})
    
    # 使用密钥进行签名加密
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt