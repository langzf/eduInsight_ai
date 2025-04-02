#!/usr/bin/env python3
"""
简易Web服务器
提供静态页面和API测试功能
"""
import sys
import os

# 获取conda环境路径
python_path = os.popen("conda run -n eduinsight python -c \"import sys; print(sys.executable)\"").read().strip()
site_packages = os.path.join(os.path.dirname(python_path), "lib", "python3.11", "site-packages")

# 添加site-packages到搜索路径
if site_packages not in sys.path:
    sys.path.insert(0, site_packages)

try:
    from flask import Flask, jsonify, render_template, send_from_directory
except ImportError:
    print("错误: 无法导入Flask，请确保已安装: pip install flask")
    sys.exit(1)

# 创建应用实例
app = Flask(__name__)

# 配置JSON响应
app.config['JSON_AS_ASCII'] = False

@app.route('/', methods=['GET'])
def home():
    """首页"""
    try:
        return render_template('index.html')
    except Exception as e:
        print(f"渲染模板错误: {e}")
        return jsonify({
            'status': 'ok',
            'message': '服务正常运行'
        }), 200

@app.route('/ping', methods=['GET'])
def ping():
    """Ping测试"""
    return jsonify({
        'status': 'ok',
        'message': 'pong'
    }), 200

@app.route('/hello', methods=['GET'])
def hello():
    """中文测试"""
    return jsonify({
        'status': 'ok',
        'message': '你好，世界！'
    }), 200

@app.route('/favicon.ico')
def favicon():
    """图标"""
    return '', 204

def main():
    """主函数"""
    port = 8091
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    
    print(f"启动Web服务器在 http://127.0.0.1:{port}")
    print(f"Python解释器: {sys.executable}")
    print(f"Flask版本: {getattr(app, '__version__', '未知')}")
    
    # 启动服务器
    app.run(host='127.0.0.1', port=port, debug=True)

if __name__ == "__main__":
    main() 