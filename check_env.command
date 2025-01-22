#!/bin/bash

echo "检查系统环境..."

# 检查Python是否安装
echo "查找系统Python..."
which python3
python3 --version

echo "===================="

# 检查pip是否可用
echo "检查pip状态..."
which pip3
pip3 --version

echo "===================="

# 检查conda是否安装
echo "检查conda状态..."
which conda
conda --version

echo "===================="

# 检查用户权限
echo "检查用户权限..."
whoami
groups

echo "===================="

# 检查miniconda安装包
echo "检查Miniconda安装包..."
ls -l Miniconda3-latest-MacOSX-x86_64.sh

echo "===================="

# 检查目录权限
echo "检查目录权限..."
ls -ld /Users/macbook/Desktop/daily-brief
ls -ld /Users/macbook/Desktop/daily-brief/.venv

echo "按任意键继续..."
read -n 1