import logging
from llama_index.core import PropertyGraphIndex
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from config import settings
# 确保在初始化 Agent 前，底层的全局大模型配置已经生效
from services.llm_service import llm_service 
# 🌟 1. 引入 LlamaIndex 的 Text-to-Cypher 神器
from llama_index.core.indices.property_graph import TextToCypherRetriever
# 🌟 1. 引入我们的 Chroma 向量库组件
from llama_index.vector_stores.chroma import ChromaVectorStore
from database.chroma_mgr import chroma_mgr

logger = logging.getLogger(__name__)

class LlamaGraphAgent:
    """基于 LlamaIndex 框架重构的工业级图谱 Agent"""
    
    def __init__(self):
        logger.info("🚀 正在初始化 LlamaIndex 混合检索引擎 (Graph + Vector)...")
        
        # 1. 原生对接：直接连上我们之前辛苦建好的 Neo4j 图谱库
        self.graph_store = Neo4jPropertyGraphStore(
            username=settings.neo4j_user,
            password=settings.neo4j_password,
            url=settings.neo4j_uri,
        )
        # 🌟 2. 向量数据库连接：接管我们原有的 ChromaDB
        self.vector_store = ChromaVectorStore(
            chroma_collection=chroma_mgr.get_collection()
        )
        
        # 2. 核心魔法：直接从现有图谱库恢复大模型索引
        # 注意：这里它会自动使用我们在 llm_service 中配好的通义千问大模型和向量模型！
        self.index = PropertyGraphIndex.from_existing(
            property_graph_store=self.graph_store,
            vector_store=self.vector_store,  # 告诉框架向量去这里找！
        )
        # 🌟 2. 破局核心：实例化智能检索器，让它适配我们手写的数据库
        cypher_retriever = TextToCypherRetriever(
            graph_store=self.graph_store,
        )
        # 🌟 3. 将智能检索器装载进查询引擎，并开启 verbose 偷窥底层
        self.query_engine = self.index.as_query_engine(
            sub_retrievers=[cypher_retriever],
            include_text=True,  # 🌟 关键：开启纯文本/向量检索能力
            similarity_top_k=2, # 🌟 匹配最相关的 2 条法律条文
            verbose=True # 开启日志，我们将亲眼看到 AI 自动写的 Cypher 语句！

        )

        logger.info("✅ LlamaGraphAgent 自动化引擎就绪！")

    async def ask(self, question: str) -> str:
        """极简的调度入口，告别手动拼接"""
        logger.info(f"🎯 LlamaIndex 开始处理复杂提问: {question}")
        
        # 🌟 降维打击就在这一行：它会自动提取人名、生成查询、检索向量并交给大模型总结！
        response = await self.query_engine.aquery(question)
        
        logger.info("✅ LlamaIndex 推理合成完毕")
        return str(response)