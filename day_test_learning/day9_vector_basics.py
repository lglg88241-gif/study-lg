import os
import asyncio
import logging
import numpy as np
from openai import AsyncOpenAI
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(message)s')

load_dotenv()
client = AsyncOpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL")
)

# 【核心算法】：计算两个向量的“余弦相似度”
# 结果越接近 1，说明两句话的意思越相近；越接近 0，说明毫无关联。
def cosine_similarity(vec1, vec2)-> float:
    """计算两个向量的“余弦相似度”"""
    dot_product = np.dot(vec1, vec2)
    norm_a = np.linalg.norm(vec1)
    norm_b = np.linalg.norm(vec2)
    return dot_product / (norm_a * norm_b) 

async def get_vector(text: str) -> list:
    """调用大模型的 Embedding 接口，把文字变成纯数字构成的向量"""
    #logging.info(f"正在将文本转化为向量: [{text}]")
    try:
        # 注意：这里调用的是 embeddings 接口，而不是 chat 接口！
        # 通义千问的默认向量模型通常是 text-embedding-v3
        response = await client.embeddings.create(
            model="text-embedding-v3", 
            input=text
        )
        # 返回的是一个包含几千个浮点数的列表
        return response.data[0].embedding
    except Exception as e:
        logging.error(f"获取向量失败，请检查模型名称或网络: {e}")
        return []

async def main():
    logging.info("=======================================")
    logging.info("🧠 开启 RAG 核心基石：向量相似度魔法测试")
    logging.info("=======================================\n")

    # 1. 模拟用户真实口语提问
    user_query = "老板没跟我签合同，还把我开除了，我能要赔偿吗？"
    
    # 2. 模拟我们数据库里存的三条不同的文本
    law_text_1 = "《劳动合同法》第八十二条：用人单位自用工之日起超过一个月不满一年未与劳动者订立书面劳动合同的，应当向劳动者每月支付二倍的工资。"
    law_text_2 = "《劳动合同法》第三十九条：劳动者严重违反用人单位的规章制度的，用人单位可以解除劳动合同。"
    random_text = "西红柿炒鸡蛋是一道非常经典的中国家常菜，需要准备番茄、鸡蛋和少许盐。"

    # 3. 将它们全部转化为数学向量
    vec_query = await get_vector(user_query)
    vec_law1 = await get_vector(law_text_1)
    vec_law2 = await get_vector(law_text_2)
    vec_random = await get_vector(random_text)

    if not vec_query:
        return

    # 4. 见证奇迹的时刻：计算相似度分数！
    logging.info("\n📊 开始计算空间几何相似度分数：")
    
    score1 = cosine_similarity(vec_query, vec_law1)
    logging.info(f"🟢 [用户提问] 与 [法条1-未签合同双倍工资] 的相似度: {score1:.4f}")
    
    score2 = cosine_similarity(vec_query, vec_law2)
    logging.info(f"🟡 [用户提问] 与 [法条2-严重违纪解除合同] 的相似度: {score2:.4f}")
    
    score3 = cosine_similarity(vec_query, vec_random)
    logging.info(f"🔴 [用户提问] 与 [菜谱-西红柿炒蛋] 的相似度: {score3:.4f}")

    logging.info("\n💡 结论：相似度最高的那条文本，就是我们要喂给大模型的『精准知识』！")

if __name__ == "__main__":
    asyncio.run(main())