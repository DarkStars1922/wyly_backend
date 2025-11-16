#!/bin/bash

# 五音疗愈音乐生成器 - 依赖安装脚本
echo "==========================================="
echo "  五音疗愈音乐生成器 - 依赖安装"
echo "==========================================="
echo ""

# 检查并激活虚拟环境
if [ -f "../env/bin/activate" ]; then
    echo "✓ 找到虚拟环境，正在激活..."
    source ../env/bin/activate
elif [ -f "env/bin/activate" ]; then
    echo "✓ 找到虚拟环境，正在激活..."
    source env/bin/activate
else
    echo "⚠ 未找到虚拟环境，将在全局环境中安装"
fi

echo ""
echo "正在安装依赖包..."
echo "-------------------------------------------"

# 安装所有依赖
pip install -r requirements.txt

echo ""
echo "==========================================="
echo "  安装完成！"
echo "==========================================="
echo ""
echo "✅ 所有依赖已安装"
echo "✅ 支持中文音乐描述（自动翻译功能）"
echo ""
echo "使用方法："
echo "  python manage.py runserver"
echo "  然后访问: http://localhost:8000/api/generate/"
echo ""
echo "您现在可以使用中文描述来生成音乐了！"
echo "例如：'浪漫的钢琴旋律，轻柔的弦乐背景'"
echo ""
