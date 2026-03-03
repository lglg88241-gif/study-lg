import asyncio
import logging
# 【核心魔法】：把你昨天文件里的函数“借”过来！
# ⚠️注意：如果你昨天的文件名不是 day4_legal_db_manager.py，请把这里改成你的真实文件名
from day4_legal_db_manager import save_consultation

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

async def main():
    logging.info("开始测试从 day4_legal_db_manager.py 导入的 save_consultation 函数...")

    # 我们在这个新文件里，直接使用了昨天写好的数据库入库函数
    try:
        is_success = await save_consultation(
            "TestUser",
            "这是一条测试跨文件调用的数据",
            False
        )
        if is_success:
            logging.info("✅ 从 day4_legal_db_manager.py 导入的函数运行成功！")
        else:
            logging.error("❌ 从 day4_legal_db_manager.py 导入的函数运行失败！")
    except Exception as e:
        logging.error(f"❌ 调用导入的函数时发生异常: {e}")
        
if __name__ == "__main__":
    print("--- 测试开始 ---")
    asyncio.run(main())
    print("--- 测试结束 ---")