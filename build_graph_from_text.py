import logging
import os
os.environ["NO_PROXY"] = "dashscope.aliyuncs.com"

from llama_index.core import Document, PropertyGraphIndex, SimpleDirectoryReader, Settings
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.core.indices.property_graph import SimpleLLMPathExtractor
from llama_index.core import PromptTemplate

# 🌟 1. 引入文本分块神器
from llama_index.core.node_parser import SentenceSplitter 

from config import settings
from services.llm_service import llm_service 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 启动全自动案卷分析与图谱建库工具...")
    
    data_dir = "./data"
    documents = SimpleDirectoryReader(data_dir).load_data()
    # 创建图谱存储
    graph_store = Neo4jPropertyGraphStore(
        username=settings.neo4j_user,
        password=settings.neo4j_password,
        url=settings.neo4j_uri,
    )
    
    # 🌟 2. 泛化提示词：用抽象的例子，教会大模型“举一反三”，杜绝过拟合！
    CHINESE_EXTRACT_PROMPT = PromptTemplate(
        "你是一个专业的知识图谱实体关系抽取器。\n"
        "请从以下文本中提取所有的实体(Entity)以及它们之间的关系(Relation)。\n"
        "【重要指令】：全面提取文本中的人物、公司、时间、金额、事件、法律条款等所有关键信息。\n"
        "【严格的输出格式要求】：\n"
        "每一行输出一个关系三元组，必须严格使用英文括号和英文双引号，不要任何前缀！\n"
        "格式：(\"实体1\", \"关系\", \"实体2\")\n"
        "例子1：(\"张三\", \"就职于\", \"某科技公司\")\n"
        "例子2：(\"某科技公司\", \"违法辞退\", \"张三\")\n"
        "例子3：(\"某科技公司\", \"拖欠金额\", \"50000元\")\n\n"
        "文本: {text}\n"
        "输出:"
    )

    # 🌟 3. 解除封印：将单次提取上限提高到 50！
    kg_extractor = SimpleLLMPathExtractor(
        llm=Settings.llm, 
        extract_prompt=CHINESE_EXTRACT_PROMPT,
        max_paths_per_chunk=50, 
    )

    # 🌟 4. 文本切片策略：把千字长文切成 256 token 的小块，带 20 token 重叠防断句
    text_splitter = SentenceSplitter(chunk_size=256, chunk_overlap=20)

    # 5. 装载流水线
    index = PropertyGraphIndex.from_documents(
        documents=documents, 
        property_graph_store=graph_store,
        kg_extractors=[kg_extractor], 
        transformations=[text_splitter], # 🌟 注入切片器
        show_progress=True 
    )
    
    logger.info("✅ 自动化图谱构建完成！")

if __name__ == "__main__":
    main()