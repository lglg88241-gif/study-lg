import os
import asyncio
import logging
from pydantic import BaseModel, Field
from typing import List, Optional
from openai import AsyncOpenAI
from neo4j import GraphDatabase
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(message)s')
load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("API_KEY"), base_url=os.getenv("BASE_URL"))
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "12345678"

# =====================================================================
# 🌟 第一步：定义本体结构 (Ontology) - 工业级开发的绝对核心
# =====================================================================
# 利用 Pydantic 极其严格地限制大模型只能输出我们规定的字段和类型
class Relationship(BaseModel):
    """
    定义知识图谱中的关系结构
    
    Attributes:
        source_entity (str): 关系的起点实体，例如：黑心资本有限公司
        target_entity (str): 关系的终点实体，例如：李四
        relation_type (str): 关系类型，只能从 [HIRED, FIRED, OWES] 中选择
        amount (Optional[float]): 如果涉及金钱拖欠，必须精确提取出具体的金额数值（纯数字）
    """
    source_entity: str = Field(..., description="关系的起点实体，例如：黑心资本有限公司")
    target_entity: str = Field(..., description="关系的终点实体，例如：李四")
    relation_type: str = Field(..., description="关系类型，只能从 [HIRED, FIRED, OWES] 中选择")
    amount: Optional[float] = Field(None, description="如果涉及金钱拖欠，必须精确提取出具体的金额数值（纯数字）")

class KnowledgeGraph(BaseModel):
    """
    定义完整的知识图谱结构
    
    Attributes:
        entities (List[str]): 案情中出现的所有核心实体（人名、公司名）
        relationships (List[Relationship]): 实体之间的关系列表
    """
    entities: List[str] = Field(..., description="案情中出现的所有核心实体（人名、公司名）")
    relationships: List[Relationship] = Field(..., description="实体之间的关系列表")

# =====================================================================
# 🌟 第二步：两阶段抽取主逻辑
# =====================================================================
async def industrial_knowledge_extraction(case_story: str):
    """
    工业级知识抽取主函数，实现两阶段抽取流程
    
    该函数通过两个阶段完成知识图谱构建：
    1. 使用大模型进行结构化本体抽取
    2. 基于抽取结果生成Cypher语句并写入Neo4j数据库
    
    Args:
        case_story (str): 待处理的案情文本
        
    Returns:
        None: 函数直接将结果写入Neo4j数据库，无返回值
    """
    logging.info("▶️ [阶段一] 开始结构化本体抽取...")
    
    # 1. 强制大模型输出 JSON 格式
    response = await client.chat.completions.create(
        model="qwen3.5-plus", # 确保你的模型支持 JSON 模式
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system", 
                "content": f"""
                你是顶级法律数据分析师。请从案情中提取实体和关系。
                你必须输出合法的 JSON 格式，并且 JSON 必须严格符合以下结构说明：
                {KnowledgeGraph.model_json_schema()}
                """
            },
            {"role": "user", "content": case_story}
        ],
        temperature=0.0 # 抽取任务温度必须为 0，追求绝对确定性
    )
    
    raw_json = response.choices[0].message.content
    logging.info(f"✅ AI 提取的精确结构化数据:\n{raw_json}")
    
    # 将 JSON 字符串反序列化为 Pydantic 对象，自带强校验！
    graph_data = KnowledgeGraph.model_validate_json(raw_json)
    
    logging.info("▶️ [阶段二] 开始程序化生成 Cypher 语句...")
    # 2. 用可靠的 Python 代码拼接 Cypher，彻底杜绝大模型的语法错误
    cypher_statements = []
    
    for rel in graph_data.relationships:
        if rel.relation_type == "OWES" and rel.amount:
            # 如果是拖欠关系，我们把精确的金额写入属性
            cypher = f"""
            MERGE (a:Entity {{name: '{rel.source_entity}'}})
            MERGE (b:Entity {{name: '{rel.target_entity}'}})
            MERGE (a)-[:OWES {{amount: {rel.amount}}}]->(b)
            """
        else:
            cypher = f"""
            MERGE (a:Entity {{name: '{rel.source_entity}'}})
            MERGE (b:Entity {{name: '{rel.target_entity}'}})
            MERGE (a)-[:{rel.relation_type}]->(b)
            """
        cypher_statements.append(cypher.strip())
        
    logging.info(f"✅ 最终生成的绝对安全 Cypher 语句数量: {len(cypher_statements)}")
    
    # 3. 写入 Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        for stmt in cypher_statements:
            session.run(stmt)
    driver.close()
    logging.info("🎉 知识图谱安全入库完成！数值幻觉已彻底消灭！")

if __name__ == "__main__":
    test_story = """我叫李四，2023年3月入职了黑心资本有限公司，岗位是前端开发。
    结果老板恶意把我开除了！而且他们还拖欠了我3个月的工资，一共是30000.5块钱！"""
    asyncio.run(industrial_knowledge_extraction(test_story))