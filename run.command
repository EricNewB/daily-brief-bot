#!/bin/bash

# 输出带颜色的信息
print_info() {
    echo -e "\033[0;34m[INFO] $1\033[0m"
}

print_error() {
    echo -e "\033[0;31m[ERROR] $1\033[0m"
}

print_success() {
    echo -e "\033[0;32m[SUCCESS] $1\033[0m"
}

# 切换到脚本所在目录
cd "$(dirname "$0")"
print_info "切换到工作目录: $(pwd)"

# 检查 Python 3 是否安装
if ! command -v python3 &> /dev/null; then
    print_error "未找到 Python 3，请先安装 Python 3"
    exit 1
fi

# 检查 pip3 是否安装
if ! command -v pip3 &> /dev/null; then
    print_error "未找到 pip3，请先安装 pip3"
    exit 1
fi

# 检查是否存在虚拟环境
if [ ! -d ".venv" ]; then
    print_info "创建虚拟环境..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        print_error "创建虚拟环境失败"
        exit 1
    fi
    print_success "虚拟环境创建成功"
fi

# 激活虚拟环境
print_info "激活虚拟环境..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    print_error "激活虚拟环境失败"
    exit 1
fi
print_success "虚拟环境激活成功"

# 安装依赖
print_info "安装依赖..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    print_error "安装依赖失败"
    exit 1
fi
print_success "依赖安装成功"

# 启动应用
print_info "启动应用..."
python3 app.py

# 如果应用异常退出，等待用户按键
if [ $? -ne 0 ]; then
    print_error "应用异常退出"
    read -p "按任意键继续..."
fi