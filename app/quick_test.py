"""
最小化Flask应用用于测试端口连接
不依赖项目中的其他模块
"""
from flask import Flask, jsonify, render_template, send_from_directory
import os

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    # 优先尝试渲染模板
    try:
        return render_template('index.html')
    except:
        # 如果没有模板，返回JSON
        return jsonify({
            'status': 'ok',
            'message': '服务正常运行'
        }), 200

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({
        'status': 'ok',
        'message': 'pong'
    }), 200

@app.route('/hello', methods=['GET'])
def hello():
    return jsonify({
        'status': 'ok',
        'message': '你好，世界！'
    }), 200

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    import sys
    port = 8090
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    
    print(f"启动简易测试服务器在 http://localhost:{port}")
    # 确保json响应为UTF-8编码
    app.config['JSON_AS_ASCII'] = False
    app.run(host='127.0.0.1', port=port, debug=True) 