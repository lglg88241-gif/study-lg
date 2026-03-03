import asyncio
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s  - %(message)s') 
# 2. 定义模拟的大模型调用任务
async def mock_agent_task(task_name: str,delay: int) -> str:
    """
    模拟一个耗时的网络请求任务（作为异步技术的练手案例）。
    
    参数:
        task_name (str): 任务的名称
        delay (int): 模拟的网络延迟时间（秒）
        
    返回:
        str: 任务完成的提示信息
    """
    logging.info(f"▶️ 开始执行任务: [{task_name}], 预计耗时 {delay} 秒...")
    try:
        await asyncio.sleep(delay)  # 模拟网络请求的延迟
        logging.info(f"✅ 任务完成: [{task_name}]")
        return f"任务 [{task_name}] 已完成"
    except Exception as e:
        logging.error(f"❌ 任务 [{task_name}] 执行出错: {e}")
        return f"任务 [{task_name}] 执行出错"
# 3. 主协调函数：并发执行多个任务
async def main():
    """
    主函数，负责协调并发执行多个模拟任务。
    """
    logging.info("🚀 开始执行模拟任务...")
    # 记录开始时间，用于最终验证异步的威力
    start_time = time.time()    
    # 核心语法：asyncio.gather
    # 把多个协程任务作为参数传进去，前面必须加 await 等待它们全部跑完
    # results 会以列表的形式，按照你传入任务的顺序，依次保存它们的返回值 
    try:
        results = await asyncio.gather(
            mock_agent_task("任务A", 5),  # 模拟一个耗时5秒的任务
            mock_agent_task("任务B", 3),  # 模拟一个耗时3秒的任务
            mock_agent_task("任务C", 2)   # 模拟一个耗时2秒的任务
        )
        logging.info(f"所有任务结果: {results}")
        # 计算总耗时
        total_time = time.time() - start_time
        logging.info(f"总耗时: {total_time:.2f} 秒")
    except Exception as e:
        logging.error(f"主函数出错: {e}")

if __name__ == "__main__":
    print("--- 启动模拟的大模型调用任务程序 ---")
    asyncio.run(main())
    print("--- 运行结束 ---")
