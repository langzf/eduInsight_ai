from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
import logging
from typing import Optional
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthMiddleware:
    """认证中间件"""
    
    def __init__(self, app):
        self.app = app
        
        # 注册请求处理器
        @app.before_request
        def authenticate():
            # 获取当前路由
            if request.endpoint is None:
                return
            
            # 分割路由名称
            if '.' in request.endpoint:
                # 安全处理包含多个点的路由名称
                parts = request.endpoint.split('.')
                blueprint = parts[0]
                endpoint = '.'.join(parts[1:])
            else:
                blueprint, endpoint = None, request.endpoint
            
            # 特殊路径: 静态文件和白名单路由
            if any([
                endpoint == 'static',
                endpoint == 'ping',  # 简单测试路由免认证
                request.endpoint in app.config.get('PUBLIC_ROUTES', []),
                # 添加登录和注册相关的API端点 - 这里同时支持直接路由和蓝图路由
                request.path.startswith('/api/v1/auth/login'),
                request.path.startswith('/api/v1/auth/register'),
                request.endpoint == 'api.auth.login',
                request.endpoint == 'api.auth.register'
            ]):
                return
            
            try:
                # 验证JWT令牌
                verify_jwt_in_request()
                # 获取用户ID
                user_id = get_jwt_identity()
                # 将用户ID添加到请求中以便后续使用
                request.user_id = user_id
            except Exception as e:
                logger.error(f"认证中间件错误: {str(e)}")
                return jsonify({'error': '认证失败', 'message': str(e)}), 401
    
    @staticmethod
    def _get_user(user_id: int) -> Optional[User]:
        """获取用户信息"""
        try:
            return User.query.get(user_id)
        except Exception as e:
            logging.error(f"获取用户信息失败: {str(e)}")
            return None 