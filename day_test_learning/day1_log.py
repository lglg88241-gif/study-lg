import logging
#配置日志，设置输出级别为info，并定义输出格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_legal_qeury(query: str) -> str:
    """
    处理法律查询问题，返回处理后的结果
    :param query: 用户输入的字符串
    :return: 清理后的字符串，错误返回空白字符串
    """
    try:
        #尝试可能出错的业务逻辑代码
        if not query:
            raise ValueError("输入的问题不能为空") #抛出异常
        
        cleaned_query = query.strip() #清理输入的字符串
        logging.info(f"处理后的查询: {cleaned_query}") #记录处理后的查询
        return cleaned_query
    except ValueError as ve:
        #处理输入为空的异常
        logging.error(f"数据校验失败: {ve}")
        return "" #返回空白字符串表示处理失败
    except Exception as e:
        #兜底：捕获其他异常
        logging.critical(f"处理法律查询问题时发生错误: {e}")
        return "" #返回空白字符串表示处理失败


if __name__ == "__main__":#主函数
    print("正常输入：")
    result_good = process_legal_qeury("   劳动合同法关于辞退的规定是什么？   ")
    print("\n异常输入：（触发ValueError异常）")
    result_bad = process_legal_qeury("")
    

