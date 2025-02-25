from flask import request, g
from functools import wraps
import logging
from typing import List, Dict, Any

class PermissionMiddleware:
    """权限控制中间件"""
    
    def __init__(self, app):
        self.app = app
        self.permission_map = self._init_permission_map()
    
    def _init_permission_map(self) -> Dict[str, List[str]]:
        """初始化权限映射"""
        return {
            'GET': {
                '/api/v1/student/progress': ['student', 'teacher', 'admin'],
                '/api/v1/teacher/dashboard': ['teacher', 'admin'],
                '/api/v1/admin/metrics': ['admin']
            },
            'POST': {
                '/api/v1/homework': ['student'],
                '/api/v1/resources': ['teacher', 'admin'],
                '/api/v1/class/manage': ['teacher', 'admin']
            }
        }
    
    def check_permission(self):
        """检查权限装饰器"""
        def decorator(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                try:
                    # 获取当前请求的方法和路径
                    method = request.method
                    path = request.path
                    
                    # 获取所需权限
                    required_roles = self.permission_map.get(method, {}).get(path)
                    if not required_roles:
                        return fn(*args, **kwargs)
                    
                    # 检查用户角色
                    if not hasattr(g, 'current_user') or g.current_user.role not in required_roles:
                        return {'message': 'Permission denied'}, 403
                    
                    return fn(*args, **kwargs)
                    
                except Exception as e:
                    logging.error(f"权限检查失败: {str(e)}")
                    return {'message': 'Permission check failed'}, 500
            return wrapper
        return decorator 