from app import db
from datetime import datetime

class Student(db.Model):
    """学生模型"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False, comment='学号')
    name = db.Column(db.String(50), nullable=False, comment='姓名')
    gender = db.Column(db.String(1), nullable=False, comment='性别')
    grade = db.Column(db.String(20), nullable=False, comment='年级')
    class_name = db.Column(db.String(50), nullable=False, comment='班级')
    phone = db.Column(db.String(20), nullable=False, comment='联系电话')
    
    # 家长信息
    parent_name = db.Column(db.String(50), nullable=False, comment='家长姓名')
    parent_phone = db.Column(db.String(20), nullable=False, comment='家长电话')
    parent_address = db.Column(db.String(200), nullable=True, comment='家庭住址')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.name,
            'gender': self.gender,
            'grade': self.grade,
            'class_name': self.class_name,
            'phone': self.phone,
            'parent': {
                'name': self.parent_name,
                'phone': self.parent_phone,
                'address': self.parent_address
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 