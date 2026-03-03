import asyncio
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

#1.async def : 定义一个异步函数
async def fetch_llm_api(prompt: str) -> str:
    """模拟调用大模型API，发送提示词并等待结果返回。"""
    try:
        logging.info(f"发送提示词到大模型：'{prompt}'···")
        #2.await : 等待异步函数执行完成
        #asyncio.sleep(2) 模拟一个耗时的异步操作，花费2秒
        #在这2秒里，CPU不会傻等，而是可以去干别的活儿！
        await asyncio.sleep(2)
        logging.info(f"大模型返回结果：'{prompt}'")
        return f"大模型返回结果：'{prompt}'"
    except Exception as e:
        logging.error(f"大模型调用出错：{e}")
#3.所有的异步函数，必须被另一个异步函数调用，或者通过事件循环启动
async def main():
    """
    主函数，用于启动异步任务
    """
    try:
        start_time = time.time()#记录开始时间
        #await 必须写在异步函数内部。我们要拿到结果，就必须 await 它。
        result = await fetch_llm_api("讲个笑话")
        logging.info(f"result: {result}")
        logging.info(f"总耗时: {time.time() - start_time:.2f} 秒")
    except Exception as e:
        logging.error(f"主函数出错：{e}")
    

if __name__ == "__main__":
    # 4. asyncio.run()：这是异步程序的唯一入口（启动钥匙）
    # 不能直接写 main()，必须用 asyncio.run(main()) 来启动“事件循环”
    print("--- 启动异步程序 ---")
    asyncio.run(main())
    print("--- 运行结束 ---")