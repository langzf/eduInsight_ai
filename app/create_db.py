"""
数据库初始化工具
用于创建数据库表并插入初始数据
"""
import os
import sys

# 添加项目根目录到系统路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# 导入应用和模型
from app import create_app, db
from app.models.user import User

def setup_db():
    """初始化数据库"""
    app = create_app('development')
    with app.app_context():
        # 创建所有表
        db.create_all()
        
        # 检查是否已有管理员用户
        admin = User.query.filter_by(phone='13800000000').first()
        if not admin:
            # 创建管理员用户
            admin = User(
                phone='13800000000',
                password='admin123',
                email='admin@eduinsight.com',
                username='admin',
                role='admin',
                full_name='系统管理员'
            )
            db.session.add(admin)
            
            # 提交更改
            db.session.commit()
            print("创建管理员用户成功")
        else:
            print("管理员用户已存在")
            
        print("数据库初始化完成")

if __name__ == '__main__':
    setup_db() 