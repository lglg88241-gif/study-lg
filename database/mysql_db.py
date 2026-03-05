import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# 获取容器环境变量中的异步数据库 URL
SQLALCHEMY_DATABASE_URL = os.getenv("MYSQL_URL", "mysql+aiomysql://root:root@127.0.0.1:3306/legal_db")

# 🌟 1. 必须使用 create_async_engine
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)

# 🌟 2. sessionmaker 必须指定 class_=AsyncSession
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False # 异步环境下这个极其重要，防止 commit 后访问属性报错
)

Base = declarative_base()

# 🌟 3. get_db 必须是 async 函数，并且 yield 的是 AsyncSession
async def get_db():
    async with SessionLocal() as session:
        yield session