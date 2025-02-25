from flask import request, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
import logging
from typing import Optional
from app.models.user import User

class AuthMiddleware:
    """认证中间件"""
    
    def __init__(self, app):
        self.app = app
        
        # 注册before_request处理器
        @app.before_request
        def before_request():
            # 跳过不需要认证的路由
            if request.endpoint in self.app.config.get('PUBLIC_ROUTES', []):
                return
                
            # 验证token
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                user = self._get_user(user_id)
                if not user:
                    return {'message': 'User not found'}, 404
                    
                # 存储用户信息
                g.current_user = user
                
            except Exception as e:
                logging.error(f"认证中间件错误: {str(e)}")
                return {'message': 'Authentication failed'}, 401
    
    @staticmethod
    def _get_user(user_id: int) -> Optional[User]:
        """获取用户信息"""
        try:
            return User.query.get(user_id)
        except Exception as e:
            logging.error(f"获取用户信息失败: {str(e)}")
            return None 