# 双刀流 AI 法律知识图谱系统

## 项目概述

这是一个基于知识图谱和向量检索的智能法律咨询系统，采用"双刀流"技术架构，结合了图数据库（Neo4j）和向量数据库（ChromaDB）的优势，为用户提供专业、准确的法律建议。

### 核心特性

- **知识图谱引擎**：通过Neo4j存储和查询法律实体关系
- **法条向量引擎**：通过ChromaDB进行法律条文的相似度检索
- **全局记忆流**：使用Redis实现会话记忆，支持多轮对话
- **分布式云脑**：基于OpenAI API的智能推理系统
- **Web服务接口**：FastAPI实现的RESTful API，支持用户认证

## 技术栈

- **后端框架**：FastAPI、Python 3.10+
- **数据库**：Neo4j（图数据库）、ChromaDB（向量数据库）、MySQL（用户数据）、Redis（会话记忆）
- **AI模型**：基于OpenAI API的大语言模型
- **认证**：JWT token认证

## 依赖库

| 库名称 | 用途 | 来源 |
|-------|------|------|
| asyncio | 异步编程支持 | day2_async_basic.py, day4_legal_db_manager.py, day6_redis_basics.py, day9_vector_basics.py, day10_chroma_db.py, day11_neo4j_basics.py, day13_graph_rag_agnet.py, main.py |
| logging | 日志记录 | day1_log.py, day2_async_basic.py, day3_agent_api_server.py, day4_legal_db_manager.py, day6_redis_basics.py, day9_vector_basics.py, day10_chroma_db.py, day11_neo4j_basics.py, day13_graph_rag_agnet.py, services/legal_agent.py, main.py |
| fastapi | Web框架 | day3_agent_api_server.py, day3_hello_api.py, day3_path_api.py, main_app.py |
| pydantic | 数据验证 | day3_agent_api_server.py, config.py, main_app.py |
| pydantic_settings | 配置管理 | config.py |
| aiomysql | 异步MySQL客户端 | day4_legal_db_manager.py, database/mysql_db.py |
| redis.asyncio | 异步Redis客户端 | day6_redis_basics.py, memory/redis_mgr.py |
| numpy | 科学计算 | day9_vector_basics.py |
| openai | OpenAI API客户端 | day9_vector_basics.py, day10_chroma_db.py, day13_graph_rag_agnet.py, services/legal_agent.py, main.py, main_app.py |
| python-dotenv | 环境变量管理 | day9_vector_basics.py, day10_chroma_db.py, day13_graph_rag_agnet.py |
| chromadb | 向量数据库 | day10_chroma_db.py, day13_graph_rag_agnet.py, database/chroma_mgr.py |
| neo4j | 图数据库客户端 | day11_neo4j_basics.py, day13_graph_rag_agnet.py, database/neo4j_mgr.py |
| httpx | HTTP客户端（OpenAI依赖） | main.py |
| jose | JWT token生成与验证 | utils/auth_utils.py |
| passlib | 密码哈希 | utils/auth_utils.py |

## 项目结构

```
├── api/                # API路由
│   └── auth_router.py  # 认证相关路由
├── data/               # 数据文件
├── database/           # 数据库管理
│   ├── chroma_mgr.py   # ChromaDB管理器
│   ├── mysql_db.py     # MySQL数据库管理
│   └── neo4j_mgr.py    # Neo4j图数据库管理
├── day_test_learning/  # 学习测试文件
│   ├── agent_concurrent_call.py    # 代理并发调用测试
│   ├── dataset_loader.py           # 数据集加载器
│   ├── day10_chroma_db.py          # ChromaDB向量数据库测试
│   ├── day11_neo4j_basics.py       # Neo4j图数据库基础测试
│   ├── day12_knowledge_extraction.py # 知识提取测试
│   ├── day13_graph_rag_agnet.py    # 图RAG代理测试
│   ├── day14_bge_reranker.py       # BGE重排序测试
│   ├── day1_log.py                 # 日志配置测试
│   ├── day2_async_basic.py         # 异步基础测试
│   ├── day2_sync_test.py           # 同步测试
│   ├── day3_agent_api_server.py    # Agent API服务器测试
│   ├── day3_hello_api.py           # Hello API测试
│   ├── day3_path_api.py            # 路径API测试
│   ├── day4_legal_db_manager.py    # 法律数据库管理测试
│   ├── day5_test_import.py         # 导入测试
│   ├── day6_redis_basics.py        # Redis基础测试
│   ├── day9_vector_basics.py       # 向量基础测试
│   ├── generate_data.py            # 数据生成器
│   ├── llm_brain.py                # LLM大脑测试
│   ├── main_api.py                 # 主API测试
│   ├── messy_data.txt              # 测试数据
│   ├── process_data.py             # 数据处理
│   ├── schema.sql                  # 数据库 schema
│   ├── test1.py                    # 测试文件
│   └── test_env.py                 # 环境测试
├── memory/             # 记忆管理
│   └── redis_mgr.py    # Redis记忆管理器
├── models/             # 数据模型
│   └── user.py         # 用户模型
├── raw_laws/           # 原始法律条文
├── services/           # 服务层
│   ├── legal_agent.py  # 法律代理服务
│   ├── llama_agent.py  # Llama代理服务
│   └── llm_service.py  # LLM服务
├── utils/              # 工具函数
│   └── auth_utils.py   # 认证工具
├── .gitignore          # Git忽略文件
├── app.log             # 应用日志
├── build_graph_from_text.py  # 从文本构建图谱
├── clean_data.txt      # 清洗后的数据
├── config.py           # 配置文件
├── ingest_law_vector.py # 法律条文向量化
├── main.py             # 命令行入口
├── main_app.py         # Web服务入口
├── requirements.txt    # 依赖文件
└── structure.txt       # 结构说明
```

## 核心功能模块

### 1. 法律代理服务 (LegalGraphAgent)

**主要功能**：
- 接收用户法律咨询问题
- 调用图数据库检索案件详情
- 调用向量数据库检索相关法条
- 结合检索结果生成专业法律建议
- 维护会话记忆，支持多轮对话

**核心方法**：
- `ask(session_id, question)`: 处理用户问题并返回法律建议
- `_execute_neo4j_search(entity_name)`: 检索图数据库中的实体关系
- `_execute_chroma_search(keyword)`: 检索向量数据库中的相关法条

### 2. 图数据库管理 (Neo4jManager)

**主要功能**：
- 管理Neo4j数据库连接
- 执行Cypher查询，检索实体关系
- 支持多跳查询，获取更全面的关系网络

### 3. 向量数据库管理 (ChromaManager)

**主要功能**：
- 管理ChromaDB向量存储
- 执行相似度搜索，查找相关法律条文
- 维护法律条文的向量索引

### 4. 记忆管理 (RedisManager)

**主要功能**：
- 管理用户会话记忆
- 存储和加载对话历史
- 支持多用户会话隔离

### 5. Web服务接口

**主要端点**：
- `/chat`: 受保护的AI法律咨询接口，需要JWT认证
- 认证相关接口（登录、注册等）

## 安装与部署

### 前提条件

- Python 3.10+
- Neo4j数据库
- Redis服务
- MySQL数据库
- OpenAI API密钥

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <项目地址>
   cd <项目目录>
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   创建 `.env` 文件，填写以下内容：
   ```
   # API 配置
   API_KEY=<你的OpenAI API密钥>
   BASE_URL=<OpenAI API基础URL>
   
   # Neo4j 配置
   NEO4J_URI=<Neo4j连接URI>
   NEO4J_USER=<Neo4j用户名>
   NEO4J_PASSWORD=<Neo4j密码>
   ```

4. **初始化数据库**
   - 启动Neo4j、Redis和MySQL服务
   - 执行数据库初始化脚本（如果需要）

5. **导入法律条文**
   ```bash
   python ingest_law_vector.py
   ```

6. **构建知识图谱**
   ```bash
   python build_graph_from_text.py
   ```

## 使用方法

### 1. 命令行交互模式

```bash
python main.py
```

启动后，你可以直接在命令行中输入法律问题，系统会返回专业的法律建议。

### 2. Web服务模式

```bash
uvicorn main_app:app --reload
```

启动后，访问 `http://localhost:8000/docs` 查看API文档，使用认证接口获取token后，调用 `/chat` 接口进行法律咨询。

## API使用示例

### 认证获取token

```bash
POST /login
Content-Type: application/json

{
  "username": "test",
  "password": "password"
}
```

### 法律咨询

```bash
POST /chat
Content-Type: application/json
Authorization: Bearer <your-token>

{
  "question": "劳动合同到期后公司不续签，我能获得赔偿吗？"
}
```

## 系统工作流程

1. **用户输入问题**：用户通过命令行或API输入法律问题
2. **记忆加载**：从Redis加载用户的历史对话记录
3. **智能分析**：大语言模型分析问题，决定是否需要调用工具
4. **工具调用**：
   - 如需案件详情，调用Neo4j图数据库
   - 如需法律条文，调用ChromaDB向量数据库
5. **结果整合**：大语言模型结合检索结果，生成专业法律建议
6. **记忆存储**：将对话历史和结果存储到Redis
7. **返回答案**：将法律建议返回给用户

## 系统优势

1. **知识全面**：结合知识图谱和向量检索，覆盖实体关系和法律条文
2. **记忆持久**：使用Redis存储会话记忆，支持多轮对话
3. **智能推理**：基于大语言模型的深度推理能力
4. **安全可靠**：JWT认证保护，确保用户数据安全
5. **易于扩展**：模块化设计，便于添加新功能和数据源

## 注意事项

- 系统需要有效的OpenAI API密钥才能正常工作
- 首次使用需要导入法律条文和构建知识图谱
- 确保Neo4j、Redis和MySQL服务正常运行
- 系统仅提供法律参考，不构成正式法律意见

## 未来规划

- 增加更多法律领域的知识图谱
- 优化向量检索算法，提高法条匹配精度
- 支持更多语言的法律咨询
- 开发前端界面，提升用户体验
- 增加法律案例库，提供更丰富的参考资料
