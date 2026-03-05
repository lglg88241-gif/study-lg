import asyncio
from celery import Celery
from config import settings
from openai import AsyncOpenAI
# 引入我们真实的 AI 代理
from services.legal_agent import LegalGraphAgent
import os
os.environ["NO_PROXY"] = "dashscope.aliyuncs.com"
# 1. 初始化 Celery 实例
celery_app = Celery(
    "legal_worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1"
)

# 2. 编写真实业务的异步包装器
@celery_app.task(name="legal_worker.ask_agent")
def ask_agent_task(session_id: str, question: str):
    print(f"🚀 [Celery Worker] 收到排队任务！开始为用户 {session_id} 查阅卷宗: {question}")
    
    # 在独立进程中初始化 OpenAI 客户端和 Agent
    client = AsyncOpenAI(api_key=settings.api_key, base_url=settings.base_url)
    worker_agent = LegalGraphAgent(client)
    
    # 🌟 核心桥梁：用 asyncio.run 将我们原本的 async 耗时函数包装成同步执行
    result = asyncio.run(worker_agent.ask(session_id, question))
    
    print(f"✅ [Celery Worker] 15秒的高强度推理完成！结果已存入 Redis 1号库！")
    return result