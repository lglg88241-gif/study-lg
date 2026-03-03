import asyncio
import logging
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO, format='%(message)s')

# ⚠️ 请把这里替换成你刚刚在 AuraDB 网页上拿到的真实信息！
# 彻底抛弃云端，连接本地物理机！
NEO4J_URI = "bolt://localhost:7687"  # 本地专用协议和端口
NEO4J_USER = "neo4j"                 # 桌面版默认账号永远是 neo4j
NEO4J_PASSWORD = "12345678"          # 填入你刚才在软件里设置的密码！

async def test_graph_db():
    logging.info("=======================================")
    logging.info("🕸️ 正在连接 Neo4j 知识图谱引擎...")
    
    # 建立图数据库连接
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        # 开启一个会话 (Session)
        with driver.session() as session:
            logging.info("✅ 成功连上 Neo4j 云端大脑！")
            
            # 1. 【核心魔法：Cypher 语言】
            # 我们用极其直观的 ASCII 艺术画法，在数据库里创造两个“节点”和一条“关系”
            # (p:Person) 表示创造一个标签为 Person 的节点
            # -[:HIRED]-> 表示创造一条名为 HIRED(雇佣) 的指向性关系
            create_query = """
            MERGE (c:Company {name: '宇宙字节科技有限公司'})
            MERGE (e:Employee {name: 'PythonDeveloper', role: '高级后端工程师'})
            MERGE (c)-[:HIRED {date: '2026-02-27'}]->(e)
            RETURN c.name, e.name
            """
            
            logging.info("▶️ 正在图数据库中创建【公司-雇佣->员工】的三元组关系...")
            result = session.run(create_query)
            
            for record in result:
                logging.info(f"✨ 知识图谱节点创建成功！实体1: {record['c.name']}, 实体2: {record['e.name']}")

            # 2. 查询验证：找出所有被“宇宙字节”雇佣的员工
            search_query = """
            MATCH (c:Company {name: '宇宙字节科技有限公司'})-[:HIRED]->(e:Employee)
            RETURN e.name, e.role
            """
            logging.info("\n🔍 正在通过关系链路进行反向图谱检索...")
            search_result = session.run(search_query)
            
            for record in search_result:
                logging.info(f"🎯 检索到匹配链路！员工姓名: {record['e.name']}, 职位: {record['e.role']}")
                
    except Exception as e:
        logging.error(f"❌ Neo4j 交互失败: {e}")
    finally:
        driver.close()
        logging.info("=======================================")

if __name__ == "__main__":
    asyncio.run(test_graph_db())