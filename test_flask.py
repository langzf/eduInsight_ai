dfrom flask import Flask
import socket
import sys

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World! 端口6060测试成功!'

def check_port(port):
    """检查端口是否可用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(('127.0.0.1', port))
        sock.close()
        return True
    except:
        sock.close()
        return False

if __name__ == '__main__':
    port = 6060
    
    if not check_port(port):
        print(f"端口 {port} 已被占用")
        sys.exit(1)
    
    print(f"端口 {port} 可用，启动服务")
    
    # 添加socket选项
    options = {
        'host': '127.0.0.1',
        'port': port,
        'debug': True,
        'use_reloader': False,  # 禁用重加载器
        'threaded': True
    }
    
    app.run(**options) 