import socket
import sys
import time

def create_socket_server(port):
    # 创建socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # 设置SO_REUSEADDR选项
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # 绑定到端口
        server_socket.bind(('127.0.0.1', port))
        print(f"成功绑定到端口 {port}")
        
        # 开始监听
        server_socket.listen(5)
        print(f"服务器正在监听 127.0.0.1:{port}")
        
        # 简单的服务循环
        counter = 0
        while counter < 10:  # 只运行10秒
            print(f"等待连接... (还剩 {10-counter} 秒)")
            time.sleep(1)
            counter += 1
            
    except OSError as e:
        print(f"错误: 无法绑定到端口 {port}: {e}")
        return False
    finally:
        server_socket.close()
        print("服务器已关闭")
        
    return True

if __name__ == "__main__":
    PORT = 6060
    print(f"尝试启动服务器在端口 {PORT}")
    
    # 第一次尝试
    result = create_socket_server(PORT)
    if result:
        print(f"第一次测试成功: 端口 {PORT} 可用")
    else:
        print(f"第一次测试失败: 端口 {PORT} 不可用")
        sys.exit(1)
    
    # 等待一会儿
    print("\n等待2秒...\n")
    time.sleep(2)
    
    # 第二次尝试
    result = create_socket_server(PORT)
    if result:
        print(f"第二次测试成功: 端口 {PORT} 可用")
    else:
        print(f"第二次测试失败: 端口 {PORT} 不可用")
        sys.exit(1) 