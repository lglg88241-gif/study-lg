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
@app.post("/chat", summary="受保护的 AI 法律咨询接口")
async def chat(
    question: str, 
    # 🌟 这里的 Depends 是精髓：
    # 只有带了合法 Token 的人才能进来，且我们直接拿到了 current_user 对象！
    current_user: User = Depends(get_current_user) 
):
    # 🌟 真正的“千人千面”：直接用数据库里的 username 或 id 作为 Redis 的 session_id
    session_id = f"user_{current_user.username}"
    
    # 调用分布式云脑 Agent
    answer = await legal_agent.ask(session_id=session_id, question=question)
    
    return {
        "user": current_user.username,
        "answer": answer
    }