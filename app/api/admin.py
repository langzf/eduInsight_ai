from flask import Blueprint, request, jsonify
from app.utils.auth import admin_required
from app.middleware.permission import PermissionMiddleware
from app.services.data import DataService
from app.services.resource import ResourceService
from app import db
import logging

admin_bp = Blueprint('admin', __name__)
permission = PermissionMiddleware(admin_bp)

@admin_bp.route('/users', methods=['GET'])
@admin_required
@permission.check_permission()
def get_users():
    """获取用户列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        role = request.args.get('role')
        
        from app.models.user import User
        query = User.query
        
        if role:
            query = query.filter_by(role=role)
            
        users = query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'total': users.total,
            'pages': users.pages,
            'current_page': users.page,
            'users': [user.to_dict() for user in users.items]
        }), 200
    except Exception as e:
        logging.error(f"获取用户列表失败: {str(e)}")
        return jsonify({'message': 'Failed to get users'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT', 'DELETE'])
@admin_required
@permission.check_permission()
def manage_user(user_id):
    """管理用户"""
    try:
        from app.models.user import User
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        if request.method == 'DELETE':
            db.session.delete(user)
            db.session.commit()
            return jsonify({'message': 'User deleted successfully'}), 200
            
        # PUT方法更新用户信息
        data = request.json
        for key, value in data.items():
            if hasattr(user, key) and key != 'id':
                setattr(user, key, value)
                
        db.session.commit()
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        logging.error(f"管理用户失败: {str(e)}")
        db.session.rollback()
        return jsonify({'message': 'Failed to manage user'}), 500

@admin_bp.route('/resources/review', methods=['GET', 'POST'])
@admin_required
@permission.check_permission()
def review_resources():
    """审核资源"""
    try:
        if request.method == 'GET':
            # 获取待审核资源列表
            from app.models.resource import Resource
            resources = Resource.query.filter_by(status='pending').all()
            return jsonify([r.to_dict() for r in resources]), 200
            
        # POST方法处理审核
        resource_id = request.json.get('resource_id')
        action = request.json.get('action')  # approve/reject
        
        if not resource_id or not action:
            return jsonify({'message': 'Invalid request'}), 400
            
        from app.models.resource import Resource
        resource = Resource.query.get(resource_id)
        if not resource:
            return jsonify({'message': 'Resource not found'}), 404
            
        resource.status = 'approved' if action == 'approve' else 'rejected'
        db.session.commit()
        
        return jsonify({'message': f'Resource {action}d successfully'}), 200
        
    except Exception as e:
        logging.error(f"审核资源失败: {str(e)}")
        return jsonify({'message': 'Failed to review resource'}), 500

@admin_bp.route('/metrics', methods=['GET'])
@admin_required
@permission.check_permission()
def get_metrics():
    """获取系统监控指标"""
    try:
        from app.models.user import User
        from app.models.resource import Resource
        from app.models.homework import Homework
        
        # 用户统计
        user_stats = {
            'total': User.query.count(),
            'students': User.query.filter_by(role='student').count(),
            'teachers': User.query.filter_by(role='teacher').count()
        }
        
        # 资源统计
        resource_stats = {
            'total': Resource.query.count(),
            'pending': Resource.query.filter_by(status='pending').count(),
            'approved': Resource.query.filter_by(status='approved').count()
        }
        
        # 作业统计
        homework_stats = {
            'total': Homework.query.count(),
            'graded': Homework.query.filter_by(status='graded').count(),
            'pending': Homework.query.filter_by(status='submitted').count()
        }
        
        # 系统性能指标（示例）
        import psutil
        system_stats = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent
        }
        
        return jsonify({
            'user_stats': user_stats,
            'resource_stats': resource_stats,
            'homework_stats': homework_stats,
            'system_stats': system_stats
        }), 200
        
    except Exception as e:
        logging.error(f"获取系统指标失败: {str(e)}")
        return jsonify({'message': 'Failed to get metrics'}), 500

@admin_bp.route('/backup', methods=['POST'])
@admin_required
@permission.check_permission()
def backup_system():
    """系统备份"""
    try:
        from datetime import datetime
        import os
        
        # 创建备份目录
        backup_dir = os.path.join(current_app.config['BACKUP_DIR'], 
                                datetime.now().strftime('%Y%m%d_%H%M%S'))
        os.makedirs(backup_dir, exist_ok=True)
        
        # 导出数据库
        from flask import current_app
        db_url = current_app.config['SQLALCHEMY_DATABASE_URI']
        os.system(f'pg_dump {db_url} > {os.path.join(backup_dir, "database.sql")}')
        
        # 备份上传的文件
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.system(f'cp -r {upload_dir} {backup_dir}/files')
        
        return jsonify({
            'message': 'Backup completed successfully',
            'backup_path': backup_dir
        }), 200
        
    except Exception as e:
        logging.error(f"系统备份失败: {str(e)}")
        return jsonify({'message': 'Failed to backup system'}), 500 