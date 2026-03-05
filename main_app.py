import os
# 🌟 新增这一行：强制将所有 HuggingFace 的请求重定向到国内官方镜像站！
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["NO_PROXY"] = "dashscope.aliyuncs.com"
from fastapi import FastAPI, Depends
from openai import AsyncOpenAI
from config import settings
from services.legal_agent import LegalGraphAgent
from api.auth_router import router as auth_router
from api.auth_router import get_current_user # 刚才写的保安
from celery_app import celery_app, ask_agent_task
from celery.result import AsyncResult
from models.user import User
import logging
app = FastAPI(title="双刀流 AI 法律 SaaS 平台")

# 🌟 2. 配置全局日志基座：强制输出 INFO 级别，并带上时间戳和模块名
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    force=True
)
# 1. 初始化 Agent (全局共享一个 Agent 实例，靠 session_id 隔离记忆)
client = AsyncOpenAI(api_key=settings.api_key, base_url=settings.base_url)
legal_agent = LegalGraphAgent(client)
loger = logging.getLogger(__name__)
# 2. 挂载路由
app.include_router(auth_router)

# 3. 编写核心对话接口
@app.post("/chat/async", summary="高并发版：异步提交提问")
async def chat_async(
    question: str, 
    current_user: User = Depends(get_current_user) 
):
    session_id = f"user_{current_user.username}"
    
    # 🌟 瞬间操作：把任务扔给 Redis，直接拿回排队号，耗时 < 0.05 秒！
    task = ask_agent_task.delay(session_id, question)
    
    return {
        "status": "任务已受理",
        "message": "问题已接收，AI 律师正在后台深度查阅卷宗...",
        "task_id": task.id  # 把取件凭证发给前端
    }

@app.get("/chat/result/{task_id}", summary="前端轮询：获取咨询结果")
async def get_chat_result(task_id: str):
    # 🌟 拿着凭证，去 Redis 的 1 号取件柜查状态
    result = AsyncResult(task_id, app=celery_app)
    
    if result.successful():
        # 跑完了，返回最终大模型的回答
        return {"status": "SUCCESS", "answer": result.result}
    elif result.failed():
        # 出错了，返回错误信息
        return {"status": "FAILURE", "message": "AI 咨询出错，请稍后再试..."}
    else:
        # 还没跑完，让前端继续等着转圈
        return {"status": "PENDING", "message": "AI 还在疯狂运算中，请稍后再试..."}