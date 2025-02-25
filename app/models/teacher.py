from app import db
from datetime import datetime

class Teacher(db.Model):
    """教师模型"""
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    subject = db.Column(db.String(50))  # 教授科目
    class_ids = db.Column(db.JSON)      # 负责的班级ID列表
    teaching_stats = db.Column(db.JSON)  # 教学统计数据
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = db.relationship('User', backref='teacher_profile')
    resources = db.relationship('Resource', backref='teacher', lazy='dynamic')
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subject': self.subject,
            'class_ids': self.class_ids,
            'teaching_stats': self.teaching_stats,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 