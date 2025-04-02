from app import db
from datetime import datetime

class Teacher(db.Model):
    """教师模型"""
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.String(50), unique=True, nullable=False, comment='工号')
    name = db.Column(db.String(50), nullable=False, comment='姓名')
    gender = db.Column(db.String(1), nullable=False, comment='性别')
    title = db.Column(db.String(50), nullable=False, comment='职称')
    department = db.Column(db.String(100), nullable=False, comment='所属部门')
    phone = db.Column(db.String(20), nullable=False, comment='联系电话')
    email = db.Column(db.String(120), nullable=False, comment='邮箱')
    office = db.Column(db.String(50), nullable=True, comment='办公室')
    research_area = db.Column(db.Text, nullable=True, comment='研究方向')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = db.relationship('User', backref='teacher_profile')
    resources = db.relationship('Resource', backref='teacher', lazy='dynamic')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'name': self.name,
            'gender': self.gender,
            'title': self.title,
            'department': self.department,
            'phone': self.phone,
            'email': self.email,
            'office': self.office,
            'research_area': self.research_area,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 