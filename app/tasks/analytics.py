from app import create_app, db
from app.celery_app import create_celery
import logging
from datetime import datetime, timedelta

app = create_app()
celery = create_celery(app)

@celery.task(name='app.tasks.analytics.generate_weekly_reports')
def generate_weekly_reports():
    """生成周报告"""
    try:
        from app.models.class_model import Class
        
        # 获取所有班级
        classes = Class.query.all()
        reports = []
        
        for class_ in classes:
            # 生成班级周报
            report = generate_class_report(class_.id)
            reports.append(report)
            
            # 更新班级统计数据
            class_.stats = report
            
        db.session.commit()
        return {'success': True, 'reports': reports}
    except Exception as e:
        logging.error(f"生成周报告失败: {str(e)}")
        return {'success': False, 'error': str(e)}

@celery.task(name='app.tasks.analytics.analyze_student_performance')
def analyze_student_performance(student_id: int):
    """分析学生表现"""
    try:
        from app.models.student import Student
        from app.models.homework import Homework
        
        # 获取最近一周的作业
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        homework = Homework.query.filter(
            Homework.student_id == student_id,
            Homework.created_at >= one_week_ago
        ).all()
        
        # 计算统计数据
        stats = {
            'total_homework': len(homework),
            'completed': len([h for h in homework if h.status == 'graded']),
            'average_score': sum(h.score or 0 for h in homework) / len(homework) if homework else 0
        }
        
        # 更新学生数据
        student = Student.query.get(student_id)
        if student:
            student.stats = stats
            db.session.commit()
            
        return {'success': True, 'stats': stats}
    except Exception as e:
        logging.error(f"分析学生表现失败: {str(e)}")
        return {'success': False, 'error': str(e)} 