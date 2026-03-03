from database.mysql_db import engine, Base
# ⚠️ 极其重要：必须导入模型，Base 才能扫描到它并建表
from models.user import User 

print("🚀 正在向 MySQL 发送自动建表指令...")
# 这一行魔法代码，会自动在 test_db 里建好 users 表！
Base.metadata.create_all(bind=engine)
print("✅ 建表完成！请去 MySQL 数据库里检查！")