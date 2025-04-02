import socket
import sys
import os
import traceback
import logging

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加父目录到sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
logger.info(f"添加到Python路径: {parent_dir}")

def is_port_in_use(port: int) -> bool:
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # 设置 SO_REUSEADDR 选项
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(('127.0.0.1', port))
            return False
        except OSError:
            return True

if __name__ == '__main__':
    try:
        # 导入Flask应用
        logger.info("正在导入应用...")
        from app import create_app
        
        logger.info("创建Flask应用实例...")
        app = create_app('development')
        
        # 使用固定端口6060
        port = 6060
        
        # 检查端口是否可用
        if is_port_in_use(port):
            logger.error(f"错误: 端口 {port} 已被占用，请先停止占用该端口的服务")
            sys.exit(1)
            
        logger.info(f"启动服务器在 http://127.0.0.1:{port}")
        
        # 添加socket选项
        options = {
            'use_reloader': False,  # 禁用重载器
            'threaded': True,      # 使用线程模式
            'host': '127.0.0.1',
            'port': port,
            'debug': True
        }
        
        app.run(**options)
        
    except Exception as e:
        logger.error(f"启动服务器时发生错误: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1) 