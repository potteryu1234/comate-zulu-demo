# -*- coding: utf-8 -*-
"""
简单的Flask服务器启动脚本
"""
from app import app

if __name__ == '__main__':
    print("=" * 60)
    print("智能手环选购分析平台")
    print("=" * 60)
    print("访问地址: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
