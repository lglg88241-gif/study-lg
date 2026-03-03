import asyncio
import logging
import os
os.environ["NO_PROXY"] = "dashscope.aliyuncs.com"

# 🌟 引入 LlamaIndex 的分块神器
from llama_index.core.node_parser import SentenceSplitter

# 引入我们自己写的底层武器
from services.llm_service import llm_service
from database.chroma_mgr import chroma_mgr

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("🚀 启动法律法典向量化注入引擎...")

    file_path = "./raw_laws/law_full.txt"
    if not os.path.exists(file_path):
        logger.error(f"❌ 找不到文件: {file_path}，请建好 raw_laws 文件夹并放入法律文本！")
        return

    # 1. 读取整部法律
    with open(file_path, "r", encoding="utf-8") as f:
        law_text = f.read()
    logger.info(f"✅ 成功读取法律文本，总字数：{len(law_text)} 字")

    # 2. 🌟 架构师级切分策略 (Chunking)
    # 法条通常较长，我们将块大小设为 512，并保留 50 个 token 的重叠(Overlap)
    # 这样可以防止“第二十条”的标题和它的内容被生硬地切到两个不同的块里
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    chunks = splitter.split_text(law_text)
    logger.info(f"✂️ 文本已被完美切分为 {len(chunks)} 个语义片段")

    # 3. 连接向量数据库
    collection = chroma_mgr.get_collection()

    logger.info("🧬 正在请求阿里云大模型逐段生成 1024 维向量，并存入 ChromaDB...")
    logger.info("⏳ 这个过程需要把整部法律翻译成高维数字，请耐心等待...")

    # 4. 遍历切片，逐个向量化并入库
    success_count = 0
    for i, chunk in enumerate(chunks):
        # 调用我们的 llm_service 把文本变成向量
        vector = await llm_service.get_vector(chunk)
        if vector:
            # 🌟 核心：把文本、向量、元数据一并存入数据库
            collection.add(
                embeddings=[vector],
                documents=[chunk],
                metadatas=[{"source": "中华人民共和国劳动合同法", "chunk_index": i}],
                ids=[f"law_chunk_{i}"]
            )
            success_count += 1
            
        if (i + 1) % 10 == 0:
            logger.info(f"⏳ 进度: 已处理 {i + 1}/{len(chunks)} 个片段...")

    logger.info(f"🎉 知识库重构完成！成功注入 {success_count} 条法律知识向量！")

if __name__ == "__main__":
    asyncio.run(main())