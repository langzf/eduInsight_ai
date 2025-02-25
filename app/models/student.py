from app import db
from .user import User

class Student(db.Model):
    """学生模型"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    grade = db.Column(db.String(20))
    class_name = db.Column(db.String(20))
    learning_path = db.Column(db.JSON)  # 存储学习路径
    weak_points = db.Column(db.JSON)    # 存储薄弱点
    interests = db.Column(db.JSON)      # 存储兴趣点
    points = db.Column(db.Integer, default=0)  # 积分
    
    # 关系
    user = db.relationship('User', backref='student_profile')
    assignments = db.relationship('Assignment', backref='student', lazy='dynamic')
    exam_scores = db.relationship('ExamScore', backref='student', lazy='dynamic') 