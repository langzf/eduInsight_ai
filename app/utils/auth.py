from functools import wraps
from typing import List, Optional
from flask import request, jsonify, current_app, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
import logging

def get_token_from_header() -> Optional[str]:
    """从请求头获取token"""
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    return None

def role_required(allowed_roles: List[str]):
    """
    角色验证装饰器
    :param allowed_roles: 允许的角色列表
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                
                # 从数据库获取用户信息
                from app.models.user import User
                user = User.query.get(user_id)
                if not user:
                    return jsonify({'message': 'User not found'}), 404
                
                # 验证角色
                if user.role not in allowed_roles:
                    return jsonify({'message': 'Permission denied'}), 403
                
                # 将用户信息存储在g对象中，方便后续使用
                g.current_user = user
                return fn(*args, **kwargs)
                
            except Exception as e:
                logging.error(f"认证失败: {str(e)}")
                return jsonify({'message': 'Authentication failed'}), 401
        return wrapper
    return decorator

def admin_required(fn):
    """管理员权限装饰器"""
    return role_required(['admin'])(fn)

def teacher_required(fn):
    """教师权限装饰器"""
    return role_required(['teacher', 'admin'])(fn) 