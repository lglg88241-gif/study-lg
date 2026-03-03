from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis.asyncio as redis
import chromadb
import logging  
from sentence_transformers import CrossEncoder
# 🌟 工业级优化：在全局初始化重排模型（避免每次请求都重新加载，占用几秒钟时间）
# device='cpu' 是为了兼容你目前的测试环境
reranker_model = CrossEncoder('BAAI/bge-reranker-base', device='cpu')
#函数引入
from day4_legal_db_manager import save_consultation, get_all_consultations, clean_duplicate_records
from day6_redis_basics import check_rate_limit 
from llm_brain import get_legal_advice
from day9_vector_basics import get_vector  # 借用你写好的向量化神技！

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="企业级法律咨询agent API(RAG 完全体)",
    description="本系统集成了风控限流、Redis短期记忆、大语言模型推理与MySQL永久存留，ChromaDB知识检索的企业级全栈系统。",
    version="3.0.0",
)


# 初始化 Redis 客户端 (全局复用，这是高级性能优化的基操)
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
# 2. 初始化 ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_data")
collection = chroma_client.get_or_create_collection(name="labor_law_collection")

class QueryRequest(BaseModel):
    is_short: bool = False
    question: str
    user_name: str

@app.post("/ask",summary="用户提问接口", description="接收用户的法律咨询问题，并返回 AI Agent 的回答。" )
async def ask_agent(request_data: QueryRequest):
    user = request_data.user_name
    question = request_data.question

    logging.info(f"▶️ 收到来自 {user} 的 POST 请求！")

    # ---------------------------------------------------------
    # 第一关：Redis 保安防刷拦截
    # ---------------------------------------------------------
    logging.info("🔐 正在进行速率限制检查...")
    is_allowed = await check_rate_limit(redis_client, user)
    if not is_allowed:
        logging.warning(f"❌ {user} 的请求被拒绝，请稍后再试。")
        raise HTTPException(status_code=429, detail="请求被拒绝，请60秒后重试。")
    # ---------------------------------------------------------
    # 第二关：Redis 短期记忆提取 (可选，为下一代 Agent 铺路)
    # ---------------------------------------------------------
    logging.info("🧠 正在提取短期记忆...")
    last_question = await redis_client.get(f"user_context:{user}")
    if last_question:
        logging.info(f"🔍 发现用户 {user} 的上一个问题：{last_question}")

        combinequestion = f"用户 {user} 的上一个问题是：{last_question}，当前问题为：{question}"
    else:
        logging.info(f"🔍 用户 {user} 没有上一个问题记录。")
        combinequestion = question
    # ---------------------------------------------------------
    # 第三关：ChromaDB 向量知识库检索 (RAG 核心)//双阶段检索 (Recall + Rerank)
    # ---------------------------------------------------------
    logging.info("🔎 [Step 1: 粗排] 正在 ChromaDB 中极速召回 Top 10 候选件...")
    retrieved_context = ""
    # 注意：我们拿用户当前最核心的 question 去检索，而不是拼接后的长句子，这样更精准
    question_vector = await get_vector(question)
    if question_vector:
        recall_results = collection.query(
            query_embeddings=[question_vector],
            n_results=10 # 只要最匹配的前 10 条
        )
        candidates = recall_results['documents'][0]
        if candidates:
            logging.info(f"🧠 [Step 2: 精排] Reranker 正在对 {len(candidates)} 条数据进行深度阅读理解...")
            
            # 构造 (问题, 文档) 对
            pairs = [[question, doc] for doc in candidates]
            
            # 交叉打分
            rerank_scores = reranker_model.predict(pairs)
            
            # 排序并过滤
            scored_candidates = sorted(zip(candidates, rerank_scores), key=lambda x: x[1], reverse=True)
            
            # 🌟 工业级硬核门槛：我们只取分数 > 0.1 且排名前 2 的法条
            # （注意：BGE-Reranker 的 Logit 分数，通常 > 0 才有参考价值）
            top_docs = [doc for doc, score in scored_candidates if score > 0][:2]
            
            if top_docs:
                retrieved_context = "\n".join(top_docs)
                logging.info(f"🎯 重排完成！最终入选法条数量: {len(top_docs)}")
            else:
                logging.warning("⚠️ 警告：精排后所有法条均未达标，已拦截噪音数据。")

    # ---------------------------------------------------------
    # 第四关：召唤 AI 大模型进行深度思考
    # ---------------------------------------------------------
    logging.info("🤖 正在调用大模型进行推理...")
    llm_answer = await get_legal_advice(combinequestion, retrieved_context)
    # ---------------------------------------------------------
    # 第五关：MySQL 永久落盘归档
    # ---------------------------------------------------------
    logging.info("💾 正在保存咨询记录到数据库...")
    db_success = await save_consultation(user, question, request_data.is_short, llm_answer)
    logging.info("✅ 咨询记录保存成功！")
    if not db_success:
        # 即使存库失败，我们也把 AI 的回答给用户，但要打个错误日志
        logging.error(f"❌ 数据库保存失败，但不影响大模型本次的回答返回")
    # ---------------------------------------------------------
    # 第六关：更新 Redis 短期记忆
    # ---------------------------------------------------------
    logging.info("🔄 正在更新用户短期记忆...生命周期5分钟")
    # 只记住用户最后一次问了什么，5分钟后阅后即焚
    await redis_client.set(f"user_context:{user}", question, ex=300)

    logging.info(f"✅ 咨询成功！AI 回答为：{llm_answer}")
    return {
        "status": "success",
        "user": user,
        "retrieved_context": retrieved_context,
        "agent_reply": llm_answer
    }


# 历史记录接口保持不变
@app.get("/api/history", summary="获取 MySQL 历史咨询记录")
async def get_history():
    history_data = await get_all_consultations()
    return {"status": "success", "total_count": len(history_data), "data": history_data}
@app.delete("/api/clean", summary="🧹 清理数据库中的重复历史提问")
async def clean_database():
    deleted_count = await clean_duplicate_records()
    return {
        "status": "success", 
        "message": f"大扫除完成！已成功清理 {deleted_count} 条重复记录。"
    } 