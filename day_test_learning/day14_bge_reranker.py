import asyncio
import logging
from sentence_transformers import CrossEncoder


logging.basicConfig(level=logging.INFO,format="%(message)s")

async def test_reranker():
    logging.info("=======================================")
    logging.info("🚀 正在加载清华 BAAI 开源的 BGE-Reranker 模型...")
    logging.info("   (初次运行会自动从 HuggingFace 下载模型权重，约 1.1GB，请耐心等待)")
    logging.info("=======================================\n")
    # 🌟 核心魔法：实例化交叉编码器模型
    # 我们使用 bge-reranker-base，这是大厂在 CPU/轻量 GPU 上最常用的版本
    model = CrossEncoder('BAAI/bge-reranker-base', max_length=512)

    # 模拟用户的棘手提问
    user_query = "老板没跟我签合同，还把我开除了，我能要赔偿吗？"

    # 模拟 ChromaDB 粗排找出来的 3 个法条（在 ChromaDB 眼里，法条1得分最高）
    # 但我们作为人类知道，法条2 才是真正解决“没签合同”痛点的绝杀法条！
    documents = [
        "法条1（字面很像）：《劳动法》规定，用人单位辞退员工，应当按照规定给予经济补偿，并提前三十日以书面形式通知劳动者本人。",
        "法条2（字面不像但极度相关）：《劳动合同法》第八十二条：用人单位自用工之日起超过一个月不满一年未与劳动者订立书面劳动合同的，应当向劳动者每月支付二倍的工资。",
        "法条3（完全无关）：《公司法》规定，有限责任公司的股东以其认缴的出资额为限对公司承担责任。"
    ]
    logging.info(f"👤 用户提问: 【{user_query}】\n")

    # 🌟 组合提问与文档，准备进行交叉打分
    # 格式必须是：[(问题, 文档1), (问题, 文档2), ...]
    sentence_pairs = [[user_query, doc] for doc in documents]
    
    logging.info("🧠 Reranker 正在进行深度语义阅读理解交叉打分...")
    # 直接调用 predict 方法，它会返回一个包含分数的数组
    scores = model.predict(sentence_pairs)
    
    # 将文档和对应的分数打包，并按分数从高到低排序！
    scored_docs = list(zip(documents, scores))
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    
    logging.info("\n🎯 重排结束！见证奇迹的时刻（相关性得分越高越好）：")
    for rank, (doc, score) in enumerate(scored_docs):
        # 工业界通常使用 Sigmoid 激活函数将原始 logit 转换到 0~1 之间，
        # 为了直观，我们这里直接看原始打分的大小关系
        logging.info(f"Top {rank + 1} | 得分: {score:+.4f} | 内容: {doc[:30]}...")

if __name__ == "__main__":
    asyncio.run(test_reranker())