import json
import logging
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class RedisMemoryManager:
    def __init__(self, host='localhost', port=6379, db=0):
        # 🌟 初始化异步 Redis 连接池
        self.redis = redis.Redis(
            host=host, 
            port=port, 
            db=db, 
            decode_responses=True # 自动将 bytes 解码为 string
        )
        self.ttl = 3600  # 记忆保质期：1小时无对话则自动遗忘，释放内存

    async def load_history(self, session_id: str, system_prompt: str) -> list:
        """根据 session_id 从 Redis 捞出当前用户的完整记忆"""
        redis_key = f"agent_memory:{session_id}"
        
        # 从 Redis 的 List 结构中取出所有历史消息
        raw_messages = await self.redis.lrange(redis_key, 0, -1)
        
        if not raw_messages:
            logger.info(f"🆕 检测到新会话 {session_id}，初始化系统人设...")
            # 如果是新会话，返回只包含系统人设的初始记忆
            return [{"role": "system", "content": system_prompt}]
            
        logger.info(f"🧠 成功从 Redis 唤醒会话 {session_id} 的 {len(raw_messages)} 条记忆！")
        # 将 JSON 字符串反序列化回 Python 字典
        return [json.loads(msg) for msg in raw_messages]

    async def save_message(self, session_id: str, message: dict):
        """
            【记忆存储】：将单条新消息（用户说的，或者 AI 回复的）追加到 Redis 记忆流
            
            功能：
                - 将新消息存储到指定会话的 Redis 列表中
                - 支持存储用户输入和 AI 回复
                - 自动管理会话记忆的过期时间
                
            参数：
                session_id: str - 会话唯一标识符，用于构建 Redis 键名
                message: dict - 消息字典，包含消息内容、发送者、时间戳等信息
                
            实现逻辑：
                1. 构建 Redis 键名，格式为 "agent_memory:{session_id}"
                2. 将消息字典序列化为 JSON 字符串
                3. 使用 Redis 的 rpush 命令从右侧推入列表
                4. 重置 Redis 键的过期时间，确保活跃会话的记忆不会被过早清除
                
            注意事项：
                - 消息字典应包含必要的字段，如消息内容、发送者类型、时间戳等
                - 序列化后的 JSON 字符串大小应合理，避免超过 Redis 的限制
                - 此方法会覆盖之前设置的过期时间，确保会话持续活跃时记忆得以保留
        """
        redis_key = f"agent_memory:{session_id}"
        
        # 将字典序列化为 JSON 字符串并从右侧推入 List
        await self.redis.rpush(redis_key, json.dumps(message))
        # 每次有新消息，重置一次过期时间
        await self.redis.expire(redis_key, self.ttl)
    #
    async def pop_last_message(self, session_id: str):
        """
    【时光倒流】：当发生异常时，紧急撤回 Redis 列表最右侧（最新）的一条残缺记忆
    
    功能：
        - 从指定会话的 Redis 列表中移除最后添加的元素
        - 用于异常处理场景，当消息处理失败时进行回滚操作
        - 确保存储的记忆都是完整有效的
        
    参数：
        session_id: str - 会话唯一标识符，用于构建 Redis 键名
        
    实现逻辑：
        1. 构建 Redis 键名，格式为 "agent_memory:{session_id}"
        2. 使用 Redis 的 rpop 命令移除列表最右侧（最新）的元素
        3. 记录警告级别日志，提示已执行回滚操作
        
    注意事项：
        - 此方法不会返回被移除的元素
        - 即使列表为空，rpop 操作也不会抛出异常
        - 仅在异常处理场景下调用，正常流程不应使用
    """
        redis_key = f"agent_memory:{session_id}"
        await self.redis.rpop(redis_key)
        logger.warning(f"⏪ 触发事务回滚：已撤回会话 {session_id} 的最后一条残缺记忆！")

# 实例化单例供全局使用
memory_mgr = RedisMemoryManager()