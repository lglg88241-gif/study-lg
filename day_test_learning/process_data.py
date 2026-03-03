import time
import os

def clean_and_sort_data(input_file="messy_data.txt", output_file="clean_data.txt"):
    print(f"--- 启动数据清洗管道 ---")
    start_time = time.time()

    if not os.path.exists(input_file):
        print(f"错误：找不到文件 {input_file}，请先运行数据生成脚本。")
        return

    # 1. 读取并清洗 (后端思维：尽量减少内存中不必要的操作)
    cleaned_data = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and "|" in line:  # 剔除空行和格式不对的行
                parts = line.split("|")
                # 结构化数据：(UID, String, Score)
                try:
                    score = float(parts[2].strip())
                    cleaned_data.append((line, score))
                except (IndexError, ValueError):
                    continue

    # 2. 排序 (后端思维：利用 Python 内置的高效 Timsort 算法)
    # 按 score (索引为 1 的元素) 降序排列
    cleaned_data.sort(key=lambda x: x[1], reverse=True)

    # 3. 写入结果
    with open(output_file, "w", encoding="utf-8") as f:
        for data_tuple in cleaned_data:
            f.write(f"{data_tuple[0]}\n")

    end_time = time.time()
    duration = end_time - start_time
    
    print(f"管道运行结束！")
    print(f"处理行数: {len(cleaned_data)}")
    print(f"总耗时: {duration:.4f} 秒")
    print(f"清洗后的数据已存入: {output_file}")

if __name__ == "__main__":
    clean_and_sort_data()