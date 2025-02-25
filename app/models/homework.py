from app import db
from datetime import datetime

class Homework(db.Model):
    """作业模型"""
    __tablename__ = 'homework'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    subject = db.Column(db.String(50))
    content = db.Column(db.Text)
    file_url = db.Column(db.String(256))
    status = db.Column(db.String(20), default='submitted')  # submitted, graded
    score = db.Column(db.Float, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    analysis = db.Column(db.JSON, nullable=True)  # 模型分析结果
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'subject': self.subject,
            'content': self.content,
            'file_url': self.file_url,
            'status': self.status,
            'score': self.score,
            'feedback': self.feedback,
            'analysis': self.analysis,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 