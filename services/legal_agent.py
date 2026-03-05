import asyncio
import os
# 🌟 加上这一行：强制将 Windows 端的 Hugging Face 请求劫持到国内镜像站！
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver # 🌟 引入核心的记忆快照模块
import logging
logger = logging.getLogger(__name__)
from database.chroma_mgr import chroma_mgr
from database.neo4j_mgr import Neo4jManager
from services.llm_service import llm_service
import torch
import json
from transformers import AutoModelForSequenceClassification, AutoTokenizer
# 🌟 全局单例：加载 BGE-Reranker 交叉编码器 (放在函数外面！)
logger.info("🧠 正在全局加载 BGE-Reranker 精排模型，请稍候...")
reranker_tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-reranker-base")
reranker_model = AutoModelForSequenceClassification.from_pretrained(
    "/app/models/bge-reranker-base",  # 使用容器内的本地路径
    local_files_only=True             # 禁止联网，强制只用本地文件
)
reranker_model.eval() # 切换到推理模式
logger.info("✅ BGE-Reranker 加载完毕！")

# 🌟 1. 全新升级的全局共享案卷（高度贴合真实业务）
class LegalState(TypedDict):
    question: str           # 用户的原始长篇自述/提问
    user_graph_facts: str   # 【预留给 Node 1】用户的图谱事实（目前暂为空）
    similar_cases: str      # 【预留给 Node 2】相似的历史判例（目前暂为空）
    laws: str               # 【Node 3 负责】精准法条
    advice: str             # 【Node 4 负责】最终法律建议
    extract_error: str       # 【负责】错误提示
    extract_retries: int     # 【负责】错误重试次数
# ----------------- 智能体定义区 -----------------


async def graph_extractor_node(state: LegalState):
    logger.info("🕸️ [Node 1 - 图谱中枢] 正在执行【先查后写】双轨图谱操作...")
    question = state.get("question")
    
    # ==========================================
    # 🌟 轨一：读（2跳漫游，挖掘历史底牌）
    # ==========================================
    logger.info("🕸️ [Node 1] 正在探测深层图谱网络...")
    entity_prompt = f"请从这句话中提取出当事人（原告/员工）的姓名或公司名，只输出名称本身。句子：{question}"
    try:
        entity_name = await llm_service.chat_completion(entity_prompt, system_msg="你是一个精准的实体抽取器")
        entity_name = entity_name.strip()
        
        cypher_read = """
        MATCH (n)
        WHERE n.id CONTAINS $name OR n.name CONTAINS $name
        MATCH path = (n)-[*1..2]-(m)
        UNWIND relationships(path) AS r
        WITH DISTINCT startNode(r) AS source, type(r) AS relation, endNode(r) AS target
        RETURN coalesce(source.name, source.id) AS source, 
               relation, 
               coalesce(target.name, target.id) AS target
        LIMIT 20
        """
        with Neo4jManager() as driver:
            with driver.session() as session:
                result = session.run(cypher_read, name=entity_name)
                records = [f"({rec['source']})-[{rec['relation']}]->({rec['target']})" for rec in result]
                
        existing_clues = "【历史图谱档案】\n" + "\n".join(records) if records else f"【历史图谱档案】未发现关于 '{entity_name}' 的过往记录。"
        logger.info(f"🕸️ [Node 1] 漫游完成！获取到历史线索。")
    except Exception as e:
        logger.error(f"❌ 图谱漫游读取失败: {e}")
        existing_clues = "【历史图谱档案】读取系统异常。"

    # ==========================================
    # 🌟 轨二：写（动态抽取，热数据增量入库）
    # ==========================================
    logger.info("🕸️ [Node 1] 正在抽取当前案情事实并写入 Neo4j...")
    extract_prompt = f"""
    请从以下用户的法律咨询中，提取出核心实体和关系。
    只输出合法的 JSON 格式，不要任何 Markdown 标记、代码块符号或废话。
    格式要求必须严格如下：
    {{
        "source_entity": "原告姓名或'我'",
        "target_entity": "被告/公司名称/老板",
        "relation": "关系动作，例如：违法辞退、拖欠工资、未签合同"
    }}
    用户咨询：{question}
    """
    try:
        json_str = await llm_service.chat_completion(extract_prompt, system_msg="你是一个精准的JSON实体抽取机器。")
        json_str = json_str.replace("```json", "").replace("```", "").strip()
        data = json.loads(json_str)
        
        source = data.get("source_entity", "未知原告")
        target = data.get("target_entity", "未知被告")
        relation = data.get("relation", "存在纠纷")
        
        cypher_write = f"""
        MERGE (s:Client {{name: $source}})
        MERGE (t:Company {{name: $target}})
        MERGE (s)-[r:`{relation}`]->(t)
        """
        with Neo4jManager() as driver:
            with driver.session() as session:
                session.run(cypher_write, source=source, target=target)
                
        new_fact = f"【今日新增事实】({source})-[{relation}]->({target})"
        logger.info(f"✅ [Node 1] 事实增量入库成功！{new_fact}")
    except Exception as e:
        logger.error(f"❌ 图谱抽取/写入失败: {e}")
        new_fact = "【今日新增事实】实时抽取失败，退级使用纯文本。"

    # ==========================================
    # 🌟 轨三：融合移交
    # ==========================================
    final_facts = f"{existing_clues}\n\n{new_fact}"
    return {"user_graph_facts": final_facts}
async def vector_researcher_node(state: LegalState):
    logger.info("📚 [Node 3 - 向量法条检索员] 正在执行【粗排+精排】双阶段检索...")
    question = state.get("question")
    
    # ---------------- 阶段一：ChromaDB 粗排撒大网 (Recall) ----------------
    query_vector = await llm_service.get_vector(question)

    collection = chroma_mgr.get_collection()
    # 粗排捞取 Top 10，宁可错杀一千，不可放过一个
    # 🌟 修改后：增加对空向量的判断
    if query_vector is None:
        logger.error("❌ 严重错误：未能生成有效的向量，跳过检索")
        return {"law_context": "无法检索相关法条（网络连接失败）"}

    results = collection.query(query_embeddings=[query_vector], n_results=10)
    results = collection.query(query_embeddings=[query_vector], n_results=10)
    candidate_docs = results.get('documents', [[]])[0]
    
    if not candidate_docs:
        return {"laws": "未查到相关法条"}

    # ---------------- 阶段二：BGE-Reranker 交叉精排 (Rerank) ----------------
    logger.info("🧠 [Node 3] 粗排捞取 10 条，正在呼叫 Reranker 进行深度交叉打分...")
    pairs = [[question, doc] for doc in candidate_docs]
    
    with torch.no_grad():
        inputs = reranker_tokenizer(pairs, padding=True, truncation=True, return_tensors='pt', max_length=512)
        scores = reranker_model(**inputs, return_dict=True).logits.view(-1,).float()
    
    # 将得分和文档组合，并按得分从高到低排序
    scored_docs = sorted(zip(scores.tolist(), candidate_docs), key=lambda x: x[0], reverse=True)
    
    # 🌟 阈值拦截：只保留得分 > 0（或者前 2 名）的绝对精准法条
    top_docs = [doc for score, doc in scored_docs if score > 0][:2]
    
    # 如果精排后全军覆没（得分都太低），说明都不相关
    if not top_docs:
        real_laws = "检索到的法条经 AI 交叉比对，关联度过低，已被全部拦截弃用。"
    else:
        real_laws = "\n".join(top_docs)
        
    logger.info(f"🎯 [Node 3] 精排完成！最终截取了 {len(top_docs)} 条致命法条。")
    return {"laws": real_laws}
async def advisor_node(state: LegalState):
    logger.info("👨‍⚖️ [Node 4 - 首席法律顾问] 正在整合全盘卷宗，生成专业法律建议...")
    
    # 🌟 极客调优：给 1.8B 小模型定制的【铁血纪律 Prompt】
    prompt = f"""
    请根据以下提供的信息，直接为用户提供法律维权建议。
    
    【已知卷宗信息】：
    - 用户的遭遇：{state.get('question')}
    - 系统检索到的适用法条：{state.get('laws', '暂无法条依据')}
    
    【输出铁律】（你必须严格遵守，否则将被开除）：
    1. 绝对禁止寒暄！不要输出“尊敬的客户”、“您好”、“首先”等客套话，不要输出任何占位符（如 [客户姓名]）。
    2. 直接开头给出你的核心结论（支持维权还是证据不足）。
    3. 严格使用以下 Markdown 结构输出：
       ### ⚖️ 案情诊断
       （一句话定性用户的遭遇，例如：公司涉嫌违法解除劳动合同）
       
       ### 📜 核心法律依据
       （结合上面检索到的法条，用大白话解释为什么用户占理）
       
       ### 🛡️ 维权行动指南
       （分点列出用户下一步该怎么做，例如：1. 收集什么证据 2. 去哪里仲裁）
    """
    
    # 🌟 强化 System Prompt：锁死它的角色设定
    system_msg = "你是一个冷酷、高效、直奔主题的中国资深劳动仲裁律师。你从不说废话，严格按照给定的格式输出。"
    
    advice = await llm_service.chat_completion(prompt, system_msg=system_msg)
    return {"advice": advice}
async def historical_case_node(state: LegalState):
    logger.info("🏛️ [Node 2 - 图谱判例检索员] (敏捷测试期) 直接跳过判例匹配，为流水线加速...")
    
    # 临时切除耗时的 LLM 关键字提取和 Neo4j 空库查询
    # (未来的冷热数据链接架构将在这里大展身手，但现在我们先让路)
    
    return {"similar_cases": "暂无相似判例参考（系统测试期，已临时切除判例检索）。"}
async def semantic_router(state: LegalState) -> str:
    """大模型接管的智能分发中心 (Semantic Router)"""
    logger.info("🔀 [路由中心] 呼叫大模型进行深度意图识别...")
    question = state.get("question", "")
    
    # 🌟 核心魔法：用极其严厉的 Prompt 逼迫大模型只吐出路由指令
    prompt = f"""
    你是一个极其精准的意图识别路由器。请分析用户的输入，并决定下一步走向。
    你必须且只能输出以下两个英文字符串之一，绝对不允许有任何标点符号、解释或废话：
    
    1. "graph_extractor"：如果用户正在详细描述一个新的法律案件、纠纷事实，或者正在讲述自己的长篇遭遇（包含人物、事件）。
    2. "historical_case"：如果用户只是在闲聊（如“你好”、“谢谢”）、简单提问（如“那我该怎么办”、“需要准备什么证据”）、或者针对之前的回答进行简短追问。
    
    用户的真实输入是：{question}
    """
    
    try:
        decision = await llm_service.chat_completion(prompt, system_msg="你是一个没有感情的路由分类器。")
        decision = decision.strip().strip('"').strip("'").lower() 
        
        if "graph_extractor" in decision:
            logger.info(f"🔀 大模型精准判定：【描述新案情】 -> 走向图谱抽取节点")
            return "graph_extractor"
        else:
            logger.info(f"🔀 大模型精准判定：【闲聊/短句追问】 -> 走向判例检索节点")
            return "historical_case"
            
    except Exception as e:
        logger.error(f"❌ 路由大模型请求崩溃: {e}，触发容灾降级机制！")
        return "historical_case"
class LegalGraphAgent:
    """被重构为 Multi-Agent 架构的企业级服务代理"""
    def __init__(self, client=None):
        logger.info("🚀 正在初始化 LangGraph 多智能体律所流水线...")
        workflow = StateGraph(LegalState)


        # 1. 注册所有的四个员工！
        workflow.add_node("graph_extractor", graph_extractor_node)
        workflow.add_node("historical_case", historical_case_node) # 把刚写的 2号员工 注册进来
        workflow.add_node("vector_researcher", vector_researcher_node)
        workflow.add_node("advisor", advisor_node)
        # 🌟 2. 引入条件边！起点不再固定，而是交给大模型路由器！
        workflow.add_conditional_edges(START, semantic_router)
        # 3. 重新规划主干流转路线
        workflow.add_edge("graph_extractor", "historical_case")   # 抽取完去找判例
        workflow.add_edge("historical_case", "vector_researcher") # 找完判例去找法条
        workflow.add_edge("vector_researcher", "advisor")         # 找完法条去宣判
        workflow.add_edge("advisor", END)

        # 🌟 核心破局点：挂载基于内存的 Checkpointer，开启快照能力！
        self.memory_saver = MemorySaver()
        self.app = workflow.compile(checkpointer=self.memory_saver)
        logger.info("✅ 律所流水线组装完毕，Checkpointer 已就绪！")

    async def ask(self, session_id: str, question: str):
        """兼容原有的对外接口，隐藏底层的复杂 Graph 调度"""
        logger.info(f"📨 收到来自 {session_id} 的新委托：{question}")
        
        # 🌟 绑定线程 ID：这决定了我们从哪个柜子里拿案卷
        config = {"configurable": {"thread_id": session_id}}
        
        # 将用户的最新问题写入案卷（这会自动覆盖之前案卷里的 question 字段，但保留其他历史）
        input_state = {"question": question}
        
        # 发动引擎！
        result = await self.app.ainvoke(input_state, config=config)
        return result.get("advice")  # 🌟 这里改成返回 advice