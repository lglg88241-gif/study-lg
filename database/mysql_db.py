import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

logger = logging.getLogger(__name__)

# 1. 创建引擎：相当于你之前的 aiomysql.connect
engine = create_engine(
    settings.mysql_url, 
    pool_pre_ping=True, # 自动重连
    echo=False          # 设为 True 可以看到底层帮你写的 SQL 语句
)

# 2. 会话工厂：每次查数据库从这里拿一个 session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. ORM 基类：所有的表模型都要继承它
Base = declarative_base()

# 4. 依赖注入函数（预留给 FastAPI 用）
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() # 相当于你代码里的 conn.close()