import asyncio
import logging
# 导入支持异步的 redis 模块
import redis.asyncio as redis

logging.basicConfig(level=logging.INFO, format='%(message)s')
# ---------------------------------------------------------
# 核心业务组件：防刷限流器
# ---------------------------------------------------------
async def check_rate_limit(client: redis.Redis, username: str) -> bool:
    """
    检查用户是否超过了速率限制
    :param username: 用户唯一标识符
    :return: 如果用户未超过速率限制则返回 True，否则返回 False
    """
    #1.拼凑键名
    key = f"rate_limit:{username}"
    #2. 调用 redis 的 incr 方法，把数字 +1，并拿到加完后的结果
    current_count = await client.incr(key)
    #3. 如果这是第一次访问，设置过期时间为 60 秒
    if current_count == 1:
        await client.expire(key, 60)
    # 4. 判断并返回
    if current_count > 3 :
        logging.warning(f"❌ 用户 {username} 已超过速率限制，请稍后再试")
        return False
    else:
        logging.info(f"✅ 用户 {username} 当前请求次数: {current_count}")
        return True

      

# async def test_redis():
#     logging.info("▶️ 尝试连接本地 Redis...")

#     # 1. 建立异步连接 (Redis 没有密码的话，只需要指定 host 和 port)
#     # decode_responses=True 非常关键！它让存取的数据自动变成字符串，而不是难读的 bytes 类型
#     client = redis.Redis(host='localhost', port=6379, decode_responses=True)

#     try:
#         # 2. 测试存入一条数据 (SET)
#         # 模拟保存 PythonDeveloper 刚刚提问的最后一条上下文
#         await client.set("user_context:PythonDeveloper", "劳动仲裁问题")
#         logging.info("✅ 成功将短期记忆存入 Redis！")

#         # 3. 测试读取这条数据 (GET)
#         memory = await client.get("user_context:PythonDeveloper")
#         logging.info(f"✅ 从 Redis 秒读出数据: {memory}")

#         # 4. 企业级核心特性：TTL (Time To Live) 过期时间
#         # ex=10 表示这条数据 10 秒后自动灰飞烟灭！这对管理 AI 对话状态极其好用
#         await client.set("temp_status", "正在输入中...", ex=10)
#         logging.info("✅ 存入一条带有 10 秒生命周期的临时状态数据。")

#     except Exception as e:
#         logging.error(f"❌ Redis 连接或操作失败，请检查 redis-server.exe 是否已启动: {e}")
#     finally:
#         # 5. 释放连接
#         await client.aclose()

# ---------------------------------------------------------
# 主测试流程
# ---------------------------------------------------------
async def main():
    logging.info("▶️ 正在连接本地Redis")
    # decode_responses=True 会自动把存入的乱码转成我们能看懂的字符串
    client = redis.Redis(host='localhost', port=6379, decode_responses=True)

    try:
        # --- 【测试 1：基础的短期记忆存取】 ---
        logging.info("----------------------------------")
        await client.set("user_context:PythonDeveloper", "上个问题是：劳动仲裁")
        memory = await client.get("user_context:PythonDeveloper")
        logging.info(f"✅ 从 Redis 秒读出短期记忆: {memory}")

        # --- 【测试 2：高并发防刷系统测试】 ---
        logging.info("----------------------------------")
        logging.info("▶️ 开始模拟恶意用户连续狂点 5 次提问...")
        
        test_user = "PythonDeveloper"
        
        for i in range(1, 6):
            logging.info(f"--- 模拟第 {i} 次点击 ---")
            is_allowed = await check_rate_limit(client, test_user)
            
            if not is_allowed:
                logging.error("❌ 滴滴滴！触发风控，请求被后端服务器无情拒绝！\n")
            else:
                logging.info("✅ 请求成功处理完毕！\n")
                
            # 稍微停顿 0.5 秒，模拟用户的真实点击间隔
            await asyncio.sleep(0.5)
            
    except Exception as e:
        logging.error(f"❌ Redis 错误: {e}")
    finally:
        # 无论如何，一定要关闭连接
        await client.aclose()
        logging.info("✅ Redis 连接已安全关闭。")


if __name__ == "__main__":
    logging.info("启动测试流程...")
    asyncio.run(main())
    logging.info("测试流程结束！")
    
