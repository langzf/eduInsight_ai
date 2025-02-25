from app import create_app
from app.celery_app import create_celery
from app.services.push import PushService
import logging

app = create_app()
celery = create_celery(app)

@celery.task(name='app.tasks.notifications.send_daily_notifications')
def send_daily_notifications():
    """发送每日通知任务"""
    try:
        push_service = PushService()
        result = push_service.schedule_daily_notifications()
        return {'success': result}
    except Exception as e:
        logging.error(f"发送每日通知失败: {str(e)}")
        return {'success': False, 'error': str(e)}

@celery.task(name='app.tasks.notifications.send_homework_reminder')
def send_homework_reminder(student_id: int, homework_ids: list):
    """发送作业提醒"""
    try:
        from app.models.student import Student
        from app.models.homework import Homework
        
        student = Student.query.get(student_id)
        if not student or not student.user.device_token:
            return {'success': False, 'error': 'Invalid student or no device token'}
            
        homework_count = len(homework_ids)
        push_service = PushService()
        success = push_service.send_notification(
            token=student.user.device_token,
            title="作业提醒",
            body=f"你有{homework_count}个作业待完成",
            data={'homework_ids': homework_ids}
        )
        
        return {'success': success}
    except Exception as e:
        logging.error(f"发送作业提醒失败: {str(e)}")
        return {'success': False, 'error': str(e)} 