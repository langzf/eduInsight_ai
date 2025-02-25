from app import db
from datetime import datetime

class Class(db.Model):
    """班级模型"""
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    grade = db.Column(db.String(20))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    student_count = db.Column(db.Integer, default=0)
    stats = db.Column(db.JSON)  # 班级统计数据
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    students = db.relationship('Student', backref='class', lazy='dynamic')
    teacher = db.relationship('Teacher', backref='classes')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'grade': self.grade,
            'teacher_id': self.teacher_id,
            'student_count': self.student_count,
            'stats': self.stats,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 