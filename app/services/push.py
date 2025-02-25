from typing import List, Dict, Any
from flask import current_app
import firebase_admin
from firebase_admin import messaging
import logging

class PushService:
    """推送服务类"""
    
    def __init__(self):
        self.firebase_app = firebase_admin.initialize_app()
    
    def send_notification(self, token: str, title: str, body: str, data: Dict[str, Any] = None) -> bool:
        """
        发送单个推送通知
        :param token: 设备token
        :param title: 通知标题
        :param body: 通知内容
        :param data: 额外数据
        :return: 是否成功
        """
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                token=token
            )
            messaging.send(message)
            return True
        except Exception as e:
            logging.error(f"推送失败: {str(e)}")
            return False
    
    def send_batch_notifications(self, tokens: List[str], title: str, body: str, 
                               data: Dict[str, Any] = None) -> Dict[str, int]:
        """
        批量发送推送通知
        :param tokens: 设备token列表
        :param title: 通知标题
        :param body: 通知内容
        :param data: 额外数据
        :return: 发送结果统计
        """
        results = {'success': 0, 'failure': 0}
        
        for token in tokens:
            success = self.send_notification(token, title, body, data)
            if success:
                results['success'] += 1
            else:
                results['failure'] += 1
                
        return results 

    def schedule_daily_notifications(self):
        """安排每日推送任务"""
        try:
            from app.models.student import Student
            from app.models.homework import Homework
            from datetime import datetime, timedelta
            
            # 获取所有学生
            students = Student.query.all()
            
            for student in students:
                # 检查未完成作业
                pending_homework = Homework.query.filter_by(
                    student_id=student.id,
                    status='submitted'
                ).all()
                
                if pending_homework:
                    # 获取学生设备token
                    token = student.user.device_token
                    if token:
                        self.send_notification(
                            token=token,
                            title="作业提醒",
                            body=f"你有 {len(pending_homework)} 个作业待完成",
                            data={'homework_ids': [h.id for h in pending_homework]}
                        )
            
            return True
        except Exception as e:
            logging.error(f"安排每日推送失败: {str(e)}")
            return False 