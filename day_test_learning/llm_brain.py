import asyncio
import logging
# 导入官方库的异步客户端
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
logging.basicConfig(level=logging.INFO, format='%(message)s')

# 1. 核心配置：这相当于你的大脑通行证
# ⚠️ 注意：这里我暂时写的是伪代码，你需要替换成真实的 API Key 和接口地址
load_dotenv()
# 2. 实例化异步客户端
client = AsyncOpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL")
    )

async def get_legal_advice(user_question: str, retrieved_context: str = "") -> str:
    """
    将用户问题和 ChromaDB 检索到的法条一起发给大模型。
    """
    logging.info("📩 正在向大模型发送问题 (已挂载 RAG 知识库)...")
    # ---------------------------------------------------------
    # 🧠 RAG 专属 Prompt 调优
    # ---------------------------------------------------------
    if retrieved_context:
        # 如果检索到了法条，我们给 AI 戴上“严谨律师”的紧箍咒
        system_content = f"""
                            你是一个专业的中国法律顾问。
                            请**严格基于**以下提供的【参考法条】来回答用户的法律问题。
                            如果提供的法条能够解答该问题，请在回答中明确引用该法条。
                            如果法条与问题无关，请结合你的专业法律知识进行解答，但必须客观严谨。

                            【参考法条】：
                            {retrieved_context}
                        """
    else:
        # 如果没有检索到法条，我们就让 AI 正常发挥，但要注意它不能瞎编乱造
        system_content = """
                            你是一个专业的中国法律顾问。
                            你的回答必须严谨、客观。如果用户的问题不是法律问题（例如问天气、菜谱），请礼貌地拒绝回答，说明你只懂法律。
                        """
    try:
        response = await client.chat.completions.create(
            model="qwen3.5-plus",
            messages=[
                # System Prompt (系统提示词)：给 AI 设定人设、规则和边界
                {   
                    "role": "system",
                    "content": system_content
                },
                # User Prompt (用户提示词)：前端发来的真实问题
                {
                    "role": "user", 
                    "content": user_question
                }
            ],
            # 5. Temperature (温度参数)：0 到 2 之间。
            # 法律系统需要极其严谨，不能瞎编乱造，所以温度设得很低（0.2）
            temperature=0.2  
        )
        # 6. 从复杂的返回结果中，精准提取出回答的正文
        reply = response.choices[0].message.content
        logging.info("✅ 大模型返回的法律解答已思考完毕！")
        return reply
    except Exception as e:
        logging.error(f"❌ 大模型调用出错：{e}")
        return "抱歉，法律顾问暂时无法回答您的问题。"


# --- 测试运行 ---
async def main():
    # 测试 1：正常的法律提问
    question1 = "我在试用期被老板无故辞退了，他只给我发了底薪，这合法吗？我该怎么办？"
    logging.info(f"用户问题: {question1}")
    answer1 = await get_legal_advice(question1)
    logging.info(f"法律顾问回答: {answer1}\n")

    # 测试 2：测试 System Prompt 的防御机制
    question2 = "今天天气怎么样？"
    logging.info(f"用户问题: {question2}")
    answer2 = await get_legal_advice(question2)
    logging.info(f"法律顾问回答: {answer2}\n")

if __name__ == "__main__":
    logging.info("--- 启动法律顾问大模型测试 ---")
    asyncio.run(main())
    logging.info("--- 测试结束 ---")

