"""
简单的独立Flask应用用于测试服务器连接
"""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/ping', methods=['GET'])
def ping():
    """简单的测试端点"""
    return jsonify({
        'status': 'ok',
        'message': '服务正常运行',
    }), 200

@app.route('/', methods=['GET'])
def home():
    """首页"""
    return jsonify({
        'app': 'eduInsight',
        'status': 'running',
        'message': '欢迎使用教育洞察AI系统'
    }), 200

if __name__ == '__main__':
    import sys
    port = 8081
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    
    print(f"启动简易测试服务器在 http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True) 