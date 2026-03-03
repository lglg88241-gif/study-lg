from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database.mysql_db import Base

class User(Base):
    __tablename__ = "users"  # 对应 MySQL 里的真实表名

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False) # 账号唯一
    hashed_password = Column(String(255), nullable=False)                  # 存加密后的密码
    created_at = Column(DateTime(timezone=True), server_default=func.now())