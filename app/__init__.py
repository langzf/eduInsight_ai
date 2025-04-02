from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from flask_caching import Cache
from app.config import config
import logging

# 初始化扩展，但还不绑定到应用
db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
migrate = Migrate()
cache = Cache()

# 公开路由，不需要验证
PUBLIC_ROUTES = [
    'auth.login', 
    'auth.register', 
    'auth.status', 
    'auth.ping',
    'static',
    'login',
    'register',
    'status'
]

def create_app(config_name='development'):
    """
    应用工厂函数
    :param config_name: 配置名称
    :return: Flask应用实例
    """
    app = Flask(__name__)
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    migrate.init_app(app, db)
    cache.init_app(app)
    
    # 注册蓝图
    from app.api import init_app as init_api
    init_api(app)
    
    # JWT回调
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        # 此处可检查token是否被撤销，简化版默认返回False
        return False
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'status': 'error',
            'error': 'token_expired',
            'message': '令牌已过期'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'status': 'error',
            'error': 'invalid_token',
            'message': '无效的令牌'
        }), 401
    
    # 应用错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'status': 'error',
            'error': 'not_found',
            'message': '请求的资源不存在'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'status': 'error',
            'error': 'internal_server_error',
            'message': '服务器内部错误'
        }), 500
    
    # 注册中间件
    from .middleware.auth import AuthMiddleware
    from .middleware.permission import PermissionMiddleware
    
    auth_middleware = AuthMiddleware(app)
    permission_middleware = PermissionMiddleware(app)
    
    # 配置不需要认证的路由
    app.config['PUBLIC_ROUTES'] = PUBLIC_ROUTES
    
    # 初始化Celery (可选)
    try:
        from .celery_app import create_celery
        celery = create_celery(app)
        app.logger.info("Celery 已成功初始化")
    except ImportError as e:
        app.logger.warning(f"Celery 初始化失败，后台任务将不可用: {e}")
        celery = None
    
    return app 