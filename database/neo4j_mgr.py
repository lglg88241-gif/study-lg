from neo4j import GraphDatabase
from config import settings

class Neo4jManager:
    """工业级 Neo4j 连接管理器"""
    def __init__(self):
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri, 
            auth=(settings.neo4j_user, settings.neo4j_password)
        )

    def __enter__(self):
        return self._driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._driver.close()

# 使用时只需：with Neo4jManager() as driver: ...