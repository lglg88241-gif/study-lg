import logging
from openai import AsyncOpenAI
from config import settings

# 🌟 新增：引入 LlamaIndex 的核心组件
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.dashscope import DashScopeEmbedding
from llama_index.llms.openai_like import OpenAILike
logger = logging.getLogger(__name__)

class LLMService:
    """工业级大模型调用服务封装"""
    def __init__(self):
        # 1. 创建 OpenAI 客户端
        self.client = AsyncOpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url
        )
        logger.info("✅ LLMService 客户端初始化成功")
        # 2. 🌟 核心重构：配置 LlamaIndex 的全局大脑
        self._setup_llamaindex_globals()
        
        logger.info("✅ LLMService 客户端及 LlamaIndex 全局引擎初始化成功")
    def _setup_llamaindex_globals(self):
        """初始化 LlamaIndex 的全局 Settings"""
        logger.info("⚙️ 正在向 LlamaIndex 注入阿里云 DashScope 兼容模型...")
        #配置大模型 (因为阿里云兼容 OpenAI 接口，我们直接用 LlamaIndex 的 OpenAI 类)
        llm = OpenAILike(
            model="qwen3.5-plus", 
            api_key=settings.api_key,
            api_base=settings.base_url,
            is_chat_model=True,     # 明确告诉框架这是对话模型
            context_window=32000,   # 手动指定通义千问的上下文窗口大小
            temperature=0.2,
            timeout=120.0  # 🌟 给它充足的时间去阅读我们庞大的图谱结构
        )
        # 配置向量模型 (1024维标准模型)
        embed_model = DashScopeEmbedding(
            model="text-embedding-v3",
            api_key=settings.api_key
        )
        # 将配置好的模型赋给 LlamaIndex 的全局对象
        Settings.llm = llm
        Settings.embed_model = embed_model
        logger.info("✅ LlamaIndex 全局 Settings (LLM + Embedding) 注入完成")
    async def get_vector(self, text: str):
        """将文本转化为 1024 维向量"""
        try:
            logger.info(f"🧬 正在生成文本向量...")
            response = await self.client.embeddings.create(
                model="text-embedding-v3", # 确保使用 1024 维标准模型
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"❌ 向量生成失败: {e}")
            return None

    async def chat_completion(self, prompt: str, system_msg: str = "你是一个专业的法律助手"):
        """通用的文本生成接口"""
        try:
            response = await self.client.chat.completions.create(
                model="qwen3.5-plus",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"❌ 文本生成失败: {e}")
            return "抱歉，系统生成回答时遇到了问题。"

# 实例化单例
llm_service = LLMService()