import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_dataset(file_path: str) -> list[str]:
    """
    加载本地法律数据集，并进行初步清洗
    
    参数:
    file_path (str): 法律数据集文件的相对或绝对路径
    
    返回:
    list[str]: 包含法律文本的列表，如果读取失败或文件为空，则返回空列表[]。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = file.readlines()
            cleaned_data = [line.strip() for line in data if line.strip()]  # 去除空行和多余空格
            logging.info(f"成功加载数据集，条目数: {len(cleaned_data)}")
            return cleaned_data
    except FileNotFoundError:
        logging.error(f"文件未找到: {file_path}")
        return []
    except Exception as e:
        logging.critical(f"加载数据集时发生未知错误: {e}")
        return []

if __name__ == "__main__":
    test_file_name = "test_legal_data.txt"
    with open(test_file_name, 'w', encoding='utf-8') as f:
        f.write("   劳动合同法关于辞退的规定是什么？   \n")
        f.write("\n")  # 空行
        f.write("   公司法关于股东权益的规定是什么？   \n")
    print("开始测试")
    #场景 1：测试正常加载存在的有效文件
    print(load_dataset(test_file_name))
    #场景 2：测试加载不存在的文件
    print(load_dataset("not_exists.txt"))
    
    if os.path.exists(test_file_name):  # 删除测试文件
        os.remove(test_file_name)
    
    print("测试结束")
