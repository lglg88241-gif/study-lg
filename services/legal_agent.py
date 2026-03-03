import json
import logging
from openai import AsyncOpenAI
# 🌟 1. 引入我们自己写的图数据库管理器
from database.neo4j_mgr import Neo4jManager
# 🌟 新增：引入向量生成服务和 ChromaDB 管理器
from services.llm_service import llm_service
from database.chroma_mgr import chroma_mgr
# 🌟 新增：引入 Redis 记忆引擎
from memory.redis_mgr import memory_mgr
logger = logging.getLogger(__name__)

class LegalGraphAgent:
    def __init__(self, client: AsyncOpenAI):
        self.client = client
        self.model_name = "qwen3.5-plus"
        # 🌟 核心改变：删除了本地的 self.history 列表！
        # 🌟 现在只保留一个系统人设，每次请求都会用它去 Redis 里兜底
        self.system_prompt = "你是一位顶尖的法律咨询专家。你可以调用外部工具查案情或法条，请基于查到的客观事实，给出专业、严谨的法律建议。"
        
        logger.info("🚀 原生 Function Calling Agent 初始化中...")
        
        # 🌟 1. 打造工具的“说明书” (JSON Schema)
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_case_details",
                    "description": "当用户询问案件中的具体实体关系时调用此工具，例如：谁开除了谁、拖欠了多少工资、负责什么项目等。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "entity_name": {
                                "type": "string",
                                "description": "案件中的关键实体名称，例如 '李四', '黑心资本有限公司'"
                            }
                        },
                        "required": ["entity_name"]
                    }
                }
            },
            # 👇 新增的第二把武器：法条检索工具
            {
                "type": "function",
                "function": {
                    "name": "search_law_articles",
                    "description": "当用户询问通用的法律规定、法定赔偿标准、或者某个行为是否违法时调用此工具。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {
                                "type": "string",
                                "description": "用于检索法律条文的关键词或短语，例如 '违法解除劳动合同赔偿标准', '试用期工资规定'"
                            }
                        },
                        "required": ["keyword"]
                    }
                }
            }
        ]
        
    # 🌟 2. 物理执行层：升级为“多跳 (Multi-Hop)”关联检索！
    async def _execute_neo4j_search(self, entity_name: str) -> str:
        logger.info(f"🔍 正在深入图谱进行 2 跳漫游查询: {entity_name}")
        
        # 🌟 终极 Cypher：查找距离目标实体 1 到 2 步的所有关系，彻底消除盲区！
        cypher = """
        MATCH (n)
        WHERE n.id CONTAINS $name OR n.name CONTAINS $name
        // 顺藤摸瓜：查找与起点距离为 1 到 2 步的所有路径
        MATCH path = (n)-[*1..2]-(m)
        // 拆解路径，去重
        UNWIND relationships(path) AS r
        WITH DISTINCT startNode(r) AS source, type(r) AS relation, endNode(r) AS target
        // 兼容不同的属性命名
        RETURN coalesce(source.name, source.id) AS source, 
               relation, 
               coalesce(target.name, target.id) AS target
        LIMIT 100
        """
        with Neo4jManager() as driver:
            with driver.session() as session:
                result = session.run(cypher, name=entity_name)
                # 把图谱关系拼接成大模型能看懂的纯文本字符串
                records = [f"({rec['source']})-[{rec['relation']}]->({rec['target']})" for rec in result]
        
        if not records:
            return f"图数据库中未找到关于 {entity_name} 的线索。"
        
        return "\n".join(records)
    # 🌟 2. 新增物理执行层：去 ChromaDB 查法条
    async def _execute_chroma_search(self, keyword: str) -> str:
        logger.info(f"📚 正在翻阅法典，检索关键词: {keyword}")
        
        # 将关键词转为 1024 维向量
        query_vector = await llm_service.get_vector(keyword)
        if not query_vector:
            return "向量生成失败，无法检索法条。"
            
        # 在 ChromaDB 中进行相似度搜索
        collection = chroma_mgr.get_collection()
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=2 # 拿最相关的 2 条法条
        )
        
        documents = results.get('documents', [[]])[0]
        if not documents:
            logger.warning(f"⚠️ 遗憾，未找到与 '{keyword}' 相关的法律条文。")
            return f"未找到与 '{keyword}' 相关的法律条文。"
        # 👇 🌟 你的严谨优化：将查到的法条拼接后，直接用日志打印在控制台上！
        law_content = "\n\n".join(documents)
        logger.info(f"⚖️ 成功精准检索到以下法条：\n{law_content}")    
        return law_content
    async def ask(self, session_id: str, question: str) -> str:
        logger.info(f"🧠 Agent 开始思考: {question}")
        
        # 🌟 1. 记忆加载：从 Redis 捞出当前用户的完整上下文（新用户会自动带上 system_prompt）
        current_history = await memory_mgr.load_history(session_id, self.system_prompt)
        # 🌟 2. 记忆写入：存入用户的新问题
        user_msg = {"role": "user", "content": question}
        await memory_mgr.save_message(session_id, user_msg)
        current_history.append(user_msg) # 本次推理要用，所以本地也要加上

        # ✈️ Trip 1: 第一次请求，带上工具箱
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=current_history,
            tools=self.tools,
            tool_choice="auto"
        )
        # 获取大模型的回复
        response_message = response.choices[0].message
        
        if response_message.tool_calls:
                    logger.info("🛠️ 大模型决策：我需要调用外部工具！")
                    
                    # 1. 先把大模型的“工具调用决策”存入 Redis
                    tool_call_msg = {
                        "role": "assistant",
                        "content": response_message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                            } for tc in response_message.tool_calls
                        ]
                    }
                    await memory_mgr.save_message(session_id, tool_call_msg)
                    current_history.append(tool_call_msg)
                    
                    # 🌟🌟🌟 高能预警：进入高危操作区，开启 try-except 保护伞！
                    try:
                        for tool_call in response_message.tool_calls:
                            function_name = tool_call.function.name
                            function_args = json.loads(tool_call.function.arguments) 
                            
                            tool_result = ""
                            if function_name == "search_case_details":
                                tool_result = await self._execute_neo4j_search(function_args.get("entity_name"))
                            elif function_name == "search_law_articles":
                                tool_result = await self._execute_chroma_search(function_args.get("keyword"))
                            
                            # 2. 如果工具成功执行，把结果也存入 Redis
                            tool_result_msg = {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": function_name,
                                "content": tool_result
                            }
                            await memory_mgr.save_message(session_id, tool_result_msg)
                            current_history.append(tool_result_msg)
                        
                        # ✈️ Trip 2: 带着装满数据的消息历史，进行第二次请求！
                        logger.info("🧠 带着查到的线索，请求大模型进行终极推理...")
                        final_response = await self.client.chat.completions.create(
                            model=self.model_name,
                            messages=current_history
                        )
                        final_answer = final_response.choices[0].message.content
                        
                        # 3. 完美大结局写入！
                        await memory_mgr.save_message(session_id, {"role": "assistant", "content": final_answer})
                        return final_answer

                    # 🌟🌟🌟 核心逻辑：一旦出事，立刻回滚！
                    except Exception as e:
                        logger.error(f"💥 工具执行或推理过程中发生严重错误: {e}")
                        # 致命补救：把刚才存进去的那个“孤立的 tool_call_msg”从 Redis 里弹出来！
                        await memory_mgr.pop_last_message(session_id)
                        # 给用户返回一个优雅的错误提示，而不是让前端直接死机
                        return f"抱歉，AI 律师在翻阅系统卷宗时遇到了网络波动（{str(e)}），请稍后重新提问。"