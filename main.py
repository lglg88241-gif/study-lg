import os
os.environ["NO_PROXY"] = "dashscope.aliyuncs.com"

import asyncio
import logging
from openai import AsyncOpenAI
from config import settings
from services.legal_agent import LegalGraphAgent
# 确保 llm_service 被导入以激活全局向量环境
from services.llm_service import llm_service

# 工业级日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log", encoding="utf-8")
    ]
)
# 屏蔽一些底层库的噪音日志，让控制台更干净
logging.getLogger("httpx").setLevel(logging.WARNING) 
logger = logging.getLogger("Main")

async def main():
    logger.info("🚀 法律知识图谱 Agent 系统启动中...")
    
    # 🌟 1. 客户端和 Agent 必须在循环外面初始化！这样才能保住“海马体”不被重置！
    client = AsyncOpenAI(api_key=settings.api_key, base_url=settings.base_url)
    agent = LegalGraphAgent(client)
    
    print("\n" + "="*50)
    print("🤖 你的专属双刀流 AI 律师已上线！")
    print("✨ 已装备: [知识图谱引擎] + [法条向量引擎] + [全局记忆流]")
    print("💡 退出请按 Ctrl+C 或输入 'q'")
    print("="*50)

    # 🌟 2. 交互式对话主循环
    while True:
        try:
            # 等待人类输入
            query = input("\n🧑‍⚖️ 你的问题: ").strip()
            if not query:
                continue
            if query.lower() in ['q', 'quit', 'exit']:
                print("\n👋 咨询结束，再见！")
                break
            
            print("\n⏳ AI 律师正在思考与翻阅卷宗，请稍候...")
            
            # 把问题丢给自带记忆的 Agent
            advice = await agent.ask(session_id="user_999", question=query)
            
            print("\n" + "="*50)
            print(f"⚖️ 专家法律建议：\n{advice}")
            print("="*50)
            
        except KeyboardInterrupt:
            print("\n\n👋 咨询结束，再见！")
            break
        except Exception as e:
            logger.error(f"💥 发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())