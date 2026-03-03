from fastapi import FastAPI
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO, format='%(message)s')
# 1. 在路径中用大括号 {} 定义变量名
@app.get("/law/{law_id}")
# 2. 核心魔法：我们在第一天死磕的 Type Hints (law_id: int) 在这里发威了！
async def get_law_by_id(law_id: int):
    logging.info(f"前端请求查询的条文 ID 是: {law_id}，类型是 {type(law_id)}")
    # FastAPI 看到 `int`，会自动帮你把 URL 里的字符串转换成整数！
    # 如果前端乱传字母，FastAPI 会直接拦截并报错，根本不用你写 try-except 去校验！
    return{
        "status": "success",
        "data": {
            "law_id": law_id,
            "content": f"这是第 {law_id} 条法律的内容。"
        }
    }
