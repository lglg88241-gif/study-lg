CREATE TABLE IF NOT EXISTS consultation_records (
    id INT AUTO_INCREMENT PRIMARY KEY, --自动递增的唯一流水号
    user_name VARCHAR(50) NOT NULL, --用户名,最长50个字符，不能为空
    query_text TEXT NOT NULL, --查询文本，不能为空
    is_short BOOLEAN DEFAULT FALSE, --是否需要简短回答，默认值为FALSE
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP --记录创建时间，默认为当前时间戳
);
