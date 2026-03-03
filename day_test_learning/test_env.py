#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试虚拟环境配置"""

import sys
print(f"Python 版本: {sys.version}")
print(f"Python 路径: {sys.executable}\n")

# 测试 openai
try:
    import openai
    print(f"✓ openai 已安装，版本: {openai.__version__}")
except ImportError as e:
    print(f"✗ openai 未安装: {e}")

# 测试 fastapi
try:
    import fastapi
    print(f"✓ fastapi 已安装，版本: {fastapi.__version__}")
except ImportError as e:
    print(f"✗ fastapi 未安装: {e}")

# 测试 uvicorn
try:
    import uvicorn
    print(f"✓ uvicorn 已安装，版本: {uvicorn.__version__}")
except ImportError as e:
    print(f"✗ uvicorn 未安装: {e}")

print("\n✓ 虚拟环境配置成功！")
