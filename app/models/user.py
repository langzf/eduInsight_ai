"""
用户模型
"""
from app import db
import datetime
import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 用户基本信息
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True, comment='手机号')
    email = db.Column(db.String(120), unique=True, nullable=True, index=True, comment='邮箱')
    username = db.Column(db.String(50), unique=True, nullable=True, index=True, comment='用户名')
    password_hash = db.Column(db.String(128), nullable=False, comment='密码哈希')
    
    # 用户角色和状态
    role = db.Column(db.String(20), nullable=False, default='student', comment='角色: student, teacher, admin')
    is_active = db.Column(db.Boolean, nullable=False, default=True, comment='是否激活')
    
    # 用户资料
    full_name = db.Column(db.String(50), nullable=True, comment='姓名')
    avatar = db.Column(db.String(255), nullable=True, comment='头像URL')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, 
                           onupdate=datetime.datetime.utcnow, comment='更新时间')
    last_login_at = db.Column(db.DateTime, nullable=True, comment='最后登录时间')

    def __init__(self, phone, password, **kwargs):
        self.phone = phone
        self.set_password(password)
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'phone': self.phone,
            'email': self.email,
            'username': self.username,
            'role': self.role,
            'is_active': self.is_active,
            'full_name': self.full_name,
            'avatar': self.avatar,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }

    def __repr__(self):
        return f'<User {self.phone}>' 