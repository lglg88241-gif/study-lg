from fastapi import FastAPI
from pydantic import BaseModel
import logging      

# 1. 依然保持良好的工程习惯：配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s') 

#2. 实例化后端服务器对象
app = FastAPI()

# 3. 核心：定义前端发来的数据结构（数据契约）
# 只要继承了 BaseModel，这个类就具备了强大的自动校验能力

class QueryRequest(BaseModel):
    user_name: str # 用户名，必须是字符串
    question: str # 用户的问题，必须是字符串
    is_short: bool # 是否需要简短回答，必须是布尔值

# 4. 定义一个 POST 接口，路径是 /ask
@app.post("/ask")
#5. 参数类型注解：这里的 request_data 必须符合我们上面定义的 QueryRequest 模型
async def ask_agent(request_data: QueryRequest):
    """
    接收前端发来的复杂结构化请求，并交给 AI Agent 处理。
    """
    logging.info("▶️ 收到来自前端的 POST 请求！")
    # 6. 获取请求参数
    name = request_data.user_name
    question = request_data.question
    is_short = request_data.is_short

    logging.info(f"请求参数 - 用户名: {name}, 问题: {question}, 是否简短: {is_short}")
    # 7. 模拟 AI Agent 处理请求
    response_msg = f"用户 {name} 的问题 {question} 用户问题已收到。"
    if is_short:
        response_msg += "我会尽量简短地回答。"
    logging.info(f"✅ 处理完毕，准备向前端返回结果。")
    return{
        "status": "success",
        "agent_reply": response_msg
    }