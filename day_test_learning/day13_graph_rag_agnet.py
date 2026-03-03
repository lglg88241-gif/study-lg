import os
import asyncio
from openai import AsyncOpenAI
from neo4j import GraphDatabase
from dotenv import load_dotenv
from chromadb.utils import embedding_functions
import chromadb
import logging
from day9_vector_basics import get_vector # 确保这个文件在你目录下
load_dotenv()

logging.basicConfig(level=logging.INFO  , format='%(asctime)s - %(levelname)s - %(message)s' )
#初始化配置
client = AsyncOpenAI(api_key=os.getenv("API_KEY"),base_url=os.getenv("BASE_URL"))
#连接 Neo4j 本地
neo4j_driver =GraphDatabase.driver("bolt://localhost:7687",auth=("neo4j","12345678") )
#连接 ChromaDB
default_ef = embedding_functions.DefaultEmbeddingFunction()
chroma_client = chromadb.PersistentClient(path="./chroma_data")
collection = chroma_client.get_or_create_collection(name="labor_law_collection")
target_name = "李四"
async def graph_rag_reasoning(user_query: str): 
    logging.info("=======================================")
    logging.info(f"🔍 用户咨询: {user_query}")
    # 1. 图谱检索：查询案情中的核心人物与纠纷点
    # 我们查出与“李四”相关的全部关系网
    with neo4j_driver.session() as session:
        graph_data = session.run("MATCH (p:Person {name: $name})-[r]-(target) RETURN p, r, target", 
            name=target_name).data()
    
    context_graph = f"案情关联背景：{str(graph_data)}"
    logging.info(f"🔗 图谱信息：\n{context_graph}")
    # 2. 向量检索：基于案情关键词匹配法律条文
    # 2. 向量检索：不再使用 query_texts，改用 query_embeddings
    try:
        # 🌟 关键动作：手动把搜索词变成大模型标准的 1024 维向量
        search_string = f"{target_name} 违法解除劳动合同 赔偿金 拖欠工资"
        question_vector = await get_vector(search_string) 
        
        search_results = collection.query(
            query_embeddings=[question_vector], # 使用处理好的向量
            n_results=2
        )
    except Exception as e:
        logging.error(f"❌ 检索失败: {e}")
        return
    context_law = f"相关法律条文：{search_results['documents'][0]}"
    logging.info(f"📜 法律条文：\n{context_law}")
    # 3. 终极合成：大模型生成法律建议
    prompt = f"""
    你是一个法律咨询专家，请根据案情背景、法律条文，生成针对该案情的法律建议。
    案情背景：{context_graph}
    法律条文：{context_law}
    用户提问：{user_query}
    请生成法律建议，请用中文回答。
    """
    response = await client.chat.completions.create(
        model="qwen3.5-plus",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    logging.info(f"✅ 法律建议：\n{response.choices[0].message.content}")    

if __name__ == "__main__":
    asyncio.run(graph_rag_reasoning(f"我被开除了，还没拿到工资，我该向谁维权？"))
    neo4j_driver.close()

