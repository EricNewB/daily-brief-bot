#!/bin/bash
cd "$(dirname "$0")"

# 创建并激活虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动测试面板
python app.py