import time
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') 

def sync_task(x: int) -> None:
    """模拟一个同步任务，记录开始和完成的日志"""
    try:
        logging.info(f"正在执行同步任务，参数为：{x}")
        time.sleep(x)  # 模拟耗时操作
        logging.info("同步任务完成")
    except Exception as e:
        logging.error(f"系统出错：{e}")


if __name__ == "__main__":
    print("开始执行同步任务...")
    sync_task(30)
    print("同步任务已完成，继续执行后续操作...")