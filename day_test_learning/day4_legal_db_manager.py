import asyncio
import logging
import aiomysql

# 保持企业级规范：配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s') 

# 1. 数据库配置字典 (把配置抽离出来是极好的工程习惯)
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "200467",
    "db": "test_db",
    "autocommit": True # 2. 开启自动提交，省得每次都要 commit()
}

# 2. 核心异步入库函数

async def save_consultation(user_name: str, question: str, is_short: bool, ai_answer: str) -> bool:
    """
    将用户的法律咨询记录，异步安全地存入 MySQL 数据库。
    """
    logging.info(f"建立连接，正在将[{user_name}]咨询保存到数据库中...")
    try:
        # 建立异步连接 (这里会产生网络延迟，所以必须 await)
        conn = await aiomysql.connect(**DB_CONFIG)
        # 获取异步游标 (游标是用来执行 SQL 语句的执行官)
        async with conn.cursor() as cursor:
            # 3. 编写 SQL 插入语句
            # 【主管强调的铁律】：绝对不能用 f-string 把变量拼接到 SQL 里！会被黑客注入攻击！
            # 必须用 %s 作为占位符，让数据库驱动自动帮你安全转义。
            sql ="""
            INSERT INTO consultation_records (user_name, question, is_short,ai_answer) VALUES (%s, %s, %s, %s)
            """
            # 4. 执行 SQL，把真实的数据作为元组 (tuple) 传进去填充占位符
            await cursor.execute(sql, (user_name, question, is_short, ai_answer))


            logging.info("✅ 咨询记录已成功保存到数据库！")
            return True
    except Exception as e:
        logging.error(f"❌ 数据库操作出错: {e}")
        return False
    finally:
        # 5. 释放连接# 兜底规范：不管上面报没报错，最后一定要把数据库连接释放掉，防止内存泄漏
        if 'conn' in locals() and conn:
            conn.close()
        logging.info("✅ 数据库连接已关闭。")

async def get_all_consultations() -> list:
    """
    【新增功能】从 MySQL 数据库中读取所有的历史咨询记录。
    """
    logging.info("▶️ 正在从数据库中获取所有历史法律咨询记录...")
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        # 【企业级魔法】: aiomysql.DictCursor 极其重要！
        # 它会让数据库返回的数据直接变成字典格式（如 {"id": 1, "user_name": "张三"}）
        # 这样 FastAPI 就能直接把它变成最标准的 JSON 发给前端！
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # SQL: 按时间倒序排列（最新的问题在最前面）
            sql = "SELECT id, user_name,question,is_short, created_at FROM consultation_records ORDER BY created_at DESC;"
            await cursor.execute(sql)

            # fetchall() 把所有查询到的数据一次性全部抓出来
            results = await cursor.fetchall()
            logging.info(f"✅ 成功获取到 {len(results)} 条咨询记录！")
            return results
    except Exception as e:
        logging.error(f"❌ 获取历史咨询记录出错: {e}")
        return []
    finally:
        if 'conn' in locals() and conn:
            conn.close()
        logging.info("✅ 数据库连接已关闭。")

async def clean_duplicate_records() -> int: 
    """
    清理重复的咨询记录（相同用户名且相同问题），只保留最新（id最大）的一条。
    返回被删除的记录数量。
    """
    logging.info("▶️ 正在清理重复咨询记录...")
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        async with conn.cursor() as cursor:
            # 1. 先查询出所有重复记录（按用户名+问题分组，id 最小的是旧的）
            sql_check = """
            DELETE t1 FROM consultation_records t1
            INNER JOIN consultation_records t2 
            WHERE t1.id < t2.id 
            AND t1.user_name = t2.user_name 
            AND t1.question = t2.question;
            """
            await cursor.execute(sql_check)
            # 获取受影响（被删除）的行数
            deleted_count = cursor.rowcount
            logging.info(f"✅ 已成功清理 {deleted_count} 条重复记录！")
            return deleted_count
    except Exception as e:
        logging.error(f"❌ 清理重复记录出错: {e}")
        return 0
    finally:
        if 'conn' in locals() and conn:
            conn.close()
        logging.info("✅ 数据库连接已关闭。")
    



# --- 模拟测试运行区域 ---
if __name__ == "__main__":
    print("--- 开始测试数据库入库模块 ---")
    # 模拟从昨天 FastAPI 接口里接到的前端数据
    test_name = "PythonDeveloper"
    test_question = "公司没签劳动合同，试用期被无故辞退，能申请劳动仲裁索赔双倍工资吗？"
    test_is_short = True

    # 启动异步事件循环，运行入库函数
    asyncio.run(save_consultation(test_name, test_question, test_is_short))
