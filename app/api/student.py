from flask import Blueprint, request, g, jsonify
from app.utils.auth import role_required
from app.middleware.permission import PermissionMiddleware
from app.services.data import DataService
from app.services.resource import ResourceService
import logging

student_bp = Blueprint('student', __name__)
permission = PermissionMiddleware(student_bp)

@student_bp.route('/progress', methods=['GET'])
@role_required(['student', 'teacher', 'admin'])
@permission.check_permission()
def get_progress():
    """获取学习进度"""
    try:
        student_id = request.args.get('student_id', g.current_user.id)
        progress = DataService.get_student_progress(student_id)
        return jsonify(progress), 200
    except Exception as e:
        logging.error(f"获取学习进度失败: {str(e)}")
        return jsonify({'message': 'Failed to get progress'}), 500

@student_bp.route('/homework', methods=['POST'])
@role_required(['student'])
@permission.check_permission()
def submit_homework():
    """提交作业"""
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'message': 'No file uploaded'}), 400
            
        data = {
            'student_id': g.current_user.id,
            'subject': request.form.get('subject'),
            'content': request.form.get('content'),
        }
        
        # 保存作业
        from app.models.homework import Homework
        from app import db
        
        # 上传文件
        resource_service = ResourceService()
        file_url = resource_service.upload_to_s3(file, 'homework')
        if not file_url:
            return jsonify({'message': 'Failed to upload file'}), 500
            
        homework = Homework(
            student_id=data['student_id'],
            subject=data['subject'],
            content=data['content'],
            file_url=file_url
        )
        
        db.session.add(homework)
        db.session.commit()
        
        return jsonify({
            'homework_id': homework.id,
            'message': 'Homework submitted successfully'
        }), 201
        
    except Exception as e:
        logging.error(f"提交作业失败: {str(e)}")
        return jsonify({'message': 'Failed to submit homework'}), 500

@student_bp.route('/resources/recommended', methods=['GET'])
@role_required(['student'])
@permission.check_permission()
def get_recommended_resources():
    """获取推荐资源"""
    try:
        limit = request.args.get('limit', 5, type=int)
        resource_service = ResourceService()
        resources = resource_service.get_recommended_resources(
            student_id=g.current_user.id,
            limit=limit
        )
        return jsonify(resources), 200
    except Exception as e:
        logging.error(f"获取推荐资源失败: {str(e)}")
        return jsonify({'message': 'Failed to get recommended resources'}), 500

@student_bp.route('/points', methods=['GET'])
@role_required(['student'])
@permission.check_permission()
def get_points():
    """获取积分和排名"""
    try:
        from app.models.student import Student
        student = Student.query.get(g.current_user.id)
        if not student:
            return jsonify({'message': 'Student not found'}), 404
            
        # 获取班级排名
        class_rank = Student.query.filter_by(class_id=student.class_id)\
            .filter(Student.points > student.points).count() + 1
            
        return jsonify({
            'points': student.points,
            'class_rank': class_rank
        }), 200
    except Exception as e:
        logging.error(f"获取积分信息失败: {str(e)}")
        return jsonify({'message': 'Failed to get points info'}), 500 