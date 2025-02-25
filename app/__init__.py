from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from config import config

# 初始化扩展
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app(config_name='development'):
    """
    应用工厂函数
    :param config_name: 配置名称
    :return: Flask应用实例
    """
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # 注册蓝图
    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # 注册中间件
    from .middleware.auth import AuthMiddleware
    from .middleware.permission import PermissionMiddleware
    
    auth_middleware = AuthMiddleware(app)
    permission_middleware = PermissionMiddleware(app)
    
    # 配置不需要认证的路由
    app.config['PUBLIC_ROUTES'] = [
        'auth.login',
        'auth.register',
        'static'
    ]
    
    # 初始化Celery
    from .celery_app import create_celery
    celery = create_celery(app)
    
    return app 