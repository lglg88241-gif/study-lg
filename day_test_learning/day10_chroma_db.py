import os
import asyncio
import logging
import chromadb # 引入我们的新核武器：向量数据库
from openai import AsyncOpenAI
from dotenv import load_dotenv
from day9_vector_basics import get_vector

logging.basicConfig(level=logging.INFO, format='%(message)s')

load_dotenv()
client = AsyncOpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL")
)


async def main():
    logging.info("=======================================")
    logging.info("📚 启动 ChromaDB 向量数据库引擎...")
    logging.info("=======================================\n")

    # 1. 初始化持久化客户端（它会在你的项目里生成一个 chroma_data 文件夹，永久保存向量！）
    chroma_client = chromadb.PersistentClient(path="./chroma_data")

    # 2. 创建或获取一个“集合” (Collection，相当于 MySQL 里的 Table 表)
    collection = chroma_client.get_or_create_collection(name="labor_law_collection")

    # 3. 准备微型【法律知识库】
    laws = [
        {"id": "law_82", "text": "《劳动合同法》第八十二条：用人单位自用工之日起超过一个月不满一年未与劳动者订立书面劳动合同的，应当向劳动者每月支付二倍的工资。"},
        {"id": "law_39", "text": "《劳动合同法》第三十九条：劳动者严重违反用人单位的规章制度的，用人单位可以解除劳动合同。"},
        {"id": "law_46", "text": "《劳动合同法》第四十六条：用人单位依照本法规定解除或终止劳动合同的，应当向劳动者支付经济补偿。"},
        {"id": "law_47", "text": "《劳动合同法》第四十七条：经济补偿按劳动者在本单位工作的年限，每满一年支付一个月工资的标准向劳动者支付。六个月以上不满一年的，按一年计算；不满六个月的，向劳动者支付半个月工资的经济补偿。"}
    ]

    logging.info("▶️ 正在将法典逐条转化为向量，并写入 ChromaDB (建库过程)...")
    for law in laws:
        # 先把文字变成多维坐标 (向量)
        vector = await get_vector(law["text"])
        if vector:
            # upsert：如果 id 存在就更新，不存在就插入
            collection.upsert(
                ids=[law["id"]],         # 数据的唯一身份牌
                embeddings=[vector],     # 核心：数字坐标！
                documents=[law["text"]]  # 原始的中文文本，方便查出来后给人看
            )
    logging.info("✅ 4 条核心法典已成功入库并建立高维索引！\n")

    # ---------------------------------------------------------
    # 模拟真实业务：用户提问检索
    # ---------------------------------------------------------
    user_question = "公司把我辞退了，我在那干了8个月，能拿多少钱补偿？"
    logging.info(f"👤 用户口语提问: 【{user_question}】")
    logging.info("🔍 正在向量空间中进行毫秒级语义检索...")

    # 第一步：把用户的问题也变成向量坐标
    question_vector = await get_vector(user_question)

    if question_vector:
        # 第二步：见证奇迹！直接命令 ChromaDB 找出距离最近的 2 条法条
        results = collection.query(
            query_embeddings=[question_vector],
            n_results=2 # 只要最匹配的前 2 条
        )

        logging.info("\n🎯 检索完成！找到的最匹配法条如下：")
        # results['documents'][0] 里面存放的就是查出来的原始中文文本
        for i, doc in enumerate(results['documents'][0]):
            logging.info(f"⭐ TOP {i+1} : {doc}")

if __name__ == "__main__":
    asyncio.run(main())