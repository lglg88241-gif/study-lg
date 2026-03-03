import chromadb
import logging
from config import settings

logger = logging.getLogger(__name__)

class ChromaManager:
    """工业级 ChromaDB 资源管理器"""
    def __init__(self):
        try:
            # 1. 初始化持久化客户端
            self.client = chromadb.PersistentClient(path=settings.chroma_path)
            # 2. 获取预定义的集合
            self.collection = self.client.get_or_create_collection(
                name=settings.law_collection_name
            )
            logger.info(f"✅ ChromaDB 客户端已就绪，集合: {settings.law_collection_name}")
        except Exception as e:
            logger.error(f"❌ ChromaDB 初始化失败: {e}")
            raise

    def get_collection(self):
        """提供给业务层调用的接口"""
        return self.collection

# 实例化为一个单例，供全项目使用
chroma_mgr = ChromaManager()