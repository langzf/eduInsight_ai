from typing import Optional, List, Dict, Any
from app import db
from app.models.user import User
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.homework import Homework
from app.models.class_model import Class
import logging

class DataService:
    """数据服务类"""
    
    @staticmethod
    def create_user(data: Dict[str, Any]) -> Optional[User]:
        """创建用户"""
        try:
            user = User(
                username=data['username'],
                email=data['email'],
                role=data['role']
            )
            user.set_password(data['password'])
            db.session.add(user)
            db.session.commit()
            return user
        except Exception as e:
            logging.error(f"创建用户失败: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def get_student_progress(student_id: int) -> Dict[str, Any]:
        """获取学生学习进度"""
        try:
            # 获取作业完成情况
            homework = Homework.query.filter_by(student_id=student_id).all()
            homework_stats = {
                'total': len(homework),
                'completed': len([h for h in homework if h.status == 'graded']),
                'average_score': sum(h.score or 0 for h in homework) / len(homework) if homework else 0
            }
            
            # 获取学生信息
            student = Student.query.get(student_id)
            
            return {
                'homework_stats': homework_stats,
                'weak_points': student.weak_points,
                'learning_path': student.learning_path
            }
        except Exception as e:
            logging.error(f"获取学生进度失败: {str(e)}")
            return {}
    
    @staticmethod
    def get_teacher_dashboard(teacher_id: int) -> Dict[str, Any]:
        """获取教师仪表盘数据"""
        try:
            teacher = Teacher.query.get(teacher_id)
            classes = Class.query.filter(Class.id.in_(teacher.class_ids)).all()
            
            class_stats = []
            for class_ in classes:
                # 获取班级作业统计
                students = Student.query.filter_by(class_id=class_.id).all()
                homework = Homework.query.filter(
                    Homework.student_id.in_([s.id for s in students])
                ).all()
                
                class_stats.append({
                    'class_id': class_.id,
                    'class_name': class_.name,
                    'student_count': len(students),
                    'homework_completion': len([h for h in homework if h.status == 'graded']) / len(homework) if homework else 0,
                    'average_score': sum(h.score or 0 for h in homework) / len(homework) if homework else 0
                })
            
            return {
                'teacher': teacher.to_dict(),
                'class_stats': class_stats,
                'teaching_stats': teacher.teaching_stats
            }
        except Exception as e:
            logging.error(f"获取教师仪表盘失败: {str(e)}")
            return {}
    
    @staticmethod
    def manage_class(action: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        班级管理（创建、更新、删除）
        :param action: 操作类型 (create/update/delete)
        :param data: 班级数据
        :return: 操作结果
        """
        try:
            if action == 'create':
                class_ = Class(
                    name=data['name'],
                    grade=data['grade'],
                    teacher_id=data['teacher_id']
                )
                db.session.add(class_)
                db.session.commit()
                return class_.to_dict()
                
            elif action == 'update':
                class_ = Class.query.get(data['id'])
                if not class_:
                    return None
                    
                for key, value in data.items():
                    if hasattr(class_, key):
                        setattr(class_, key, value)
                
                db.session.commit()
                return class_.to_dict()
                
            elif action == 'delete':
                class_ = Class.query.get(data['id'])
                if not class_:
                    return None
                    
                db.session.delete(class_)
                db.session.commit()
                return {'message': 'Class deleted successfully'}
                
        except Exception as e:
            logging.error(f"班级管理操作失败: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def manage_class_students(class_id: int, action: str, student_ids: List[int]) -> bool:
        """
        管理班级学生
        :param class_id: 班级ID
        :param action: 操作类型 (add/remove)
        :param student_ids: 学生ID列表
        :return: 是否成功
        """
        try:
            class_ = Class.query.get(class_id)
            if not class_:
                return False
            
            if action == 'add':
                students = Student.query.filter(Student.id.in_(student_ids)).all()
                for student in students:
                    student.class_id = class_id
                class_.student_count = Class.student_count + len(students)
                
            elif action == 'remove':
                Student.query.filter(
                    Student.id.in_(student_ids),
                    Student.class_id == class_id
                ).update({'class_id': None}, synchronize_session=False)
                class_.student_count = Class.student_count - len(student_ids)
            
            db.session.commit()
            return True
            
        except Exception as e:
            logging.error(f"管理班级学生失败: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_class_analytics(class_id: int) -> Dict[str, Any]:
        """
        获取班级分析数据
        :param class_id: 班级ID
        :return: 分析结果
        """
        try:
            class_ = Class.query.get(class_id)
            if not class_:
                return {}
            
            # 获取学生列表
            students = Student.query.filter_by(class_id=class_id).all()
            student_ids = [s.id for s in students]
            
            # 获取作业统计
            homework = Homework.query.filter(
                Homework.student_id.in_(student_ids)
            ).all()
            
            # 计算各科目平均分
            subject_scores = {}
            for hw in homework:
                if hw.score:
                    if hw.subject not in subject_scores:
                        subject_scores[hw.subject] = []
                    subject_scores[hw.subject].append(hw.score)
            
            subject_averages = {
                subject: sum(scores)/len(scores)
                for subject, scores in subject_scores.items()
            }
            
            # 识别需要关注的学生
            attention_needed = []
            for student in students:
                student_homework = [h for h in homework if h.student_id == student.id]
                if student_homework:
                    avg_score = sum(h.score or 0 for h in student_homework) / len(student_homework)
                    if avg_score < 60:  # 假设60分为及格线
                        attention_needed.append({
                            'student_id': student.id,
                            'name': student.user.username,
                            'average_score': avg_score,
                            'weak_points': student.weak_points
                        })
            
            return {
                'class_info': class_.to_dict(),
                'student_count': len(students),
                'subject_averages': subject_averages,
                'homework_completion_rate': len([h for h in homework if h.status == 'graded']) / len(homework) if homework else 0,
                'attention_needed_students': attention_needed,
                'class_ranking': class_.stats.get('ranking') if class_.stats else None
            }
            
        except Exception as e:
            logging.error(f"获取班级分析数据失败: {str(e)}")
            return {} 