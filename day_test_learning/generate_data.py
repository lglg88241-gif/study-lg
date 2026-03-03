import random
import string

def generate_messy_data(filename="messy_data.txt", lines=100000):
    print(f"正在生成 {lines} 行杂乱数据...")
    
    # 常用随机字符库
    chars = string.ascii_letters + string.digits
    
    with open(filename, "w", encoding="utf-8") as f:
        for i in range(lines):
            # 模拟：用户ID | 随机指纹 | 评分
            uid = f"USER_{random.randint(10000, 99999)}"
            fingerprint = ''.join(random.choices(chars, k=12))
            score = round(random.uniform(0, 100), 2)
            
            # 故意制造“脏数据”：每隔 500 行插入一个空行或异常行
            if i % 500 == 0:
                f.write("\n") # 纯空行
            elif i % 700 == 0:
                f.write(f"{uid} | CORRUPTED_DATA | ###\n") # 无法解析的数值
            else:
                f.write(f"{uid} | {fingerprint} | {score}\n")
                
    print(f"✅ 生成完毕！文件已保存为: {filename}")

if __name__ == "__main__":
    generate_messy_data()