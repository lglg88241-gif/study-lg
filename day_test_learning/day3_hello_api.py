from fastapi import FastAPI

import logging

logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(message)s')

#1.实例化 FastAPI 核心对象，这就是你的后端服务器
app = FastAPI(
    title="我的企业级后端 API",
    description="这是一个演示规范化编码的 FastAPI 应用。",
    version="1.0.0"
)

# 2. 路由装饰器：规定了用什么方法(GET)、访问哪个路径("/")能触发下面的函数
@app.get("/",response_model=dict)
async def root():
    """
    根路径欢迎接口 (Hello World)

    这是一个演示用的标准 GET 接口。它不接收任何输入参数，
    并在成功调用后返回一条包含欢迎信息的 JSON 响应。

    Returns:
        dict: 包含 "message" 键的字典
    """
    # 3. 认出这个 async 了吗？因为处理网络请求会有延迟，所以后端接口必须是异步的！
    logging.info("有人访问了根路径")
    # FastAPI 会自动把返回的 Python 字典转换成标准的 JSON 格式发给前端
    try:
        return {"message": "Hello,, 欢迎来到你的第一个规范化企业级后端接口！"}
    except Exception as e:
        logging.error(f"❌ 错误: {e}")
        return {"message": "服务器内部错误"}