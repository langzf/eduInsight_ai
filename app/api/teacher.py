from flask import Blueprint, request, g, jsonify
from app.utils.auth import teacher_required
from app.middleware.permission import PermissionMiddleware
from app.services.data import DataService
from app.services.resource import ResourceService
import logging

teacher_bp = Blueprint('teacher', __name__)
permission = PermissionMiddleware(teacher_bp)

@teacher_bp.route('/dashboard', methods=['GET'])
@teacher_required
@permission.check_permission()
def get_dashboard():
    """获取教师仪表盘"""
    try:
        dashboard_data = DataService.get_teacher_dashboard(g.current_user.id)
        return jsonify(dashboard_data), 200
    except Exception as e:
        logging.error(f"获取教师仪表盘失败: {str(e)}")
        return jsonify({'message': 'Failed to get dashboard'}), 500

@teacher_bp.route('/class/manage', methods=['POST'])
@teacher_required
@permission.check_permission()
def manage_class():
    """管理班级"""
    try:
        action = request.json.get('action')
        data = request.json.get('data', {})
        
        if not action or not data:
            return jsonify({'message': 'Invalid request'}), 400
            
        result = DataService.manage_class(action, data)
        if not result:
            return jsonify({'message': 'Operation failed'}), 400
            
        return jsonify(result), 200
    except Exception as e:
        logging.error(f"管理班级失败: {str(e)}")
        return jsonify({'message': 'Failed to manage class'}), 500

@teacher_bp.route('/class/<int:class_id>/students', methods=['POST'])
@teacher_required
@permission.check_permission()
def manage_class_students(class_id):
    """管理班级学生"""
    try:
        action = request.json.get('action')
        student_ids = request.json.get('student_ids', [])
        
        if not action or not student_ids:
            return jsonify({'message': 'Invalid request'}), 400
            
        success = DataService.manage_class_students(class_id, action, student_ids)
        if not success:
            return jsonify({'message': 'Operation failed'}), 400
            
        return jsonify({'message': 'Students updated successfully'}), 200
    except Exception as e:
        logging.error(f"管理班级学生失败: {str(e)}")
        return jsonify({'message': 'Failed to manage students'}), 500

@teacher_bp.route('/class/<int:class_id>/analytics', methods=['GET'])
@teacher_required
@permission.check_permission()
def get_class_analytics(class_id):
    """获取班级分析数据"""
    try:
        analytics = DataService.get_class_analytics(class_id)
        return jsonify(analytics), 200
    except Exception as e:
        logging.error(f"获取班级分析失败: {str(e)}")
        return jsonify({'message': 'Failed to get analytics'}), 500

@teacher_bp.route('/resources', methods=['POST'])
@teacher_required
@permission.check_permission()
def upload_resource():
    """上传教学资源"""
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'message': 'No file uploaded'}), 400
            
        metadata = {
            'title': request.form.get('title'),
            'type': request.form.get('type'),
            'tags': request.form.getlist('tags'),
            'description': request.form.get('description')
        }
        
        resource_service = ResourceService()
        result = resource_service.process_resource(file, metadata)
        
        if not result:
            return jsonify({'message': 'Failed to process resource'}), 500
            
        return jsonify(result), 201
    except Exception as e:
        logging.error(f"上传资源失败: {str(e)}")
        return jsonify({'message': 'Failed to upload resource'}), 500 