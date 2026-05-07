# -*- coding: utf-8 -*-
"""
智能手环选购分析平台 - 启动脚本
"""
import subprocess
import sys
import os

def check_dependencies():
    """检查依赖是否安装"""
    try:
        import flask
        import pymysql
        import snownlp
        import jieba
        print("✓ 所有依赖已安装")
        return True
    except ImportError as e:
        print(f"✗ 缺少依赖: {e}")
        print("请运行: python -m pip install flask pymysql snownlp jieba")
        return False

def init_databases():
    """初始化数据库"""
    print("\n正在初始化数据库...")
    try:
        import init_db
        import init_user_db
        print("✓ 数据库初始化完成")
        return True
    except Exception as e:
        print(f"✗ 数据库初始化失败: {e}")
        return False

def main():
    print("=" * 60)
    print("智能手环选购分析与健康功能评估平台")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 初始化数据库
    if not init_databases():
        print("警告: 数据库初始化可能未完全成功，但应用仍可尝试启动")
    
    print("\n" + "=" * 60)
    print("启动Web应用...")
    print("访问地址: http://localhost:5000")
    print("测试账号: test_user / test123")
    print("=" * 60 + "\n")
    
    # 启动Flask应用
    from app import app
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
