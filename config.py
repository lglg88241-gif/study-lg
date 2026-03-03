from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # API 核心配置
    api_key: str = Field(..., env="API_KEY")
    base_url: str = Field(..., env="BASE_URL")
    
    # Neo4j 配置
    neo4j_uri: str = Field(..., env="NEO4J_URI")
    neo4j_user: str = Field(..., env="NEO4J_USER")
    neo4j_password: str = Field(..., env="NEO4J_PASSWORD")
    
    # ChromaDB 配置
    chroma_path: str = "./chroma_data"
    law_collection_name: str = "labor_law_collection"

    # 🌟 新增：根据你 day4 的配置，生成的专属 MySQL 连接字符串
    mysql_url: str = "mysql+pymysql://root:200467@127.0.0.1:3306/test_db?charset=utf8mb4"

    class Config:
        env_file = ".env"

settings = Settings()