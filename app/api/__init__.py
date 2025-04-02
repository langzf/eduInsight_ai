from flask import Blueprint

# 创建API版本蓝图
api = Blueprint('api', __name__, url_prefix='/api/v1')

# 导入并注册子蓝图
from app.api.auth import auth_bp
api.register_blueprint(auth_bp)

# 导入其他蓝图
# from app.api.courses import courses_bp
# from app.api.users import users_bp
# api.register_blueprint(courses_bp)
# api.register_blueprint(users_bp)

def init_app(app):
    """在应用程序上注册API蓝图"""
    app.register_blueprint(api) 