from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from datetime import timedelta, datetime
import bcrypt
import logging

from app.models.user import User
from app import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

logger = logging.getLogger(__name__)

@auth_bp.route('/ping', methods=['GET'])
def ping():
    """简单的测试端点，确认服务是否正常运行"""
    return jsonify({
        'status': 'ok',
        'message': '服务正常运行',
    }), 200

@auth_bp.route('/status', methods=['GET'])
def status():
    """API状态检查"""
    return jsonify({
        'status': 'ok',
        'message': 'API服务运行正常',
        'version': '1.0.0'
    }), 200

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400
    
    phone = data.get('phone')
    password = data.get('password')
    
    if not phone or not password:
        return jsonify({'error': '手机号和密码为必填项'}), 400
    
    # 检查手机号是否已存在
    existing_user = User.query.filter_by(phone=phone).first()
    if existing_user:
        return jsonify({'error': '该手机号已被注册'}), 409
    
    # 创建新用户
    user = User(
        phone=phone,
        password=password,
        role=data.get('role', 'student')  # 默认角色为学生
    )
    
    # 可选字段
    if 'email' in data:
        user.email = data.get('email')
    if 'username' in data:
        user.username = data.get('username')
    if 'full_name' in data:
        user.full_name = data.get('full_name')
    
    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': '注册成功', 'user_id': user.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'注册失败: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400
    
    phone = data.get('phone')
    password = data.get('password')
    
    if not phone or not password:
        return jsonify({'error': '手机号和密码为必填项'}), 400
    
    # 首先尝试从内存字典获取用户 (server.py)
    try:
        from app.server import users as memory_users
        memory_user = memory_users.get(phone)
        
        if memory_user:
            # 确保password_hash是字符串
            password_hash = memory_user['password_hash']
            if isinstance(password_hash, bytes):
                password_hash_bytes = password_hash
            else:
                password_hash_bytes = password_hash.encode('utf-8')
                
            # 使用bcrypt验证密码 - 内存用户
            if bcrypt.checkpw(password.encode('utf-8'), password_hash_bytes):
                # 检查用户状态
                if not memory_user.get('is_active', True):
                    return jsonify({'error': '账号已被禁用'}), 403
                
                # 更新最后登录时间
                memory_user['last_login_at'] = datetime.now().isoformat()
                
                # 创建访问令牌
                access_token = create_access_token(
                    identity=phone,
                    additional_claims={
                        'phone': phone,
                        'role': memory_user.get('role', 'student')
                    },
                    expires_delta=timedelta(hours=24)
                )
                
                # 用户信息（不包含密码哈希）
                user_info = {k: v for k, v in memory_user.items() if k != 'password_hash'}
                
                return jsonify({
                    'access_token': access_token,
                    'user': user_info
                }), 200
            else:
                # 密码不匹配
                return jsonify({'error': '手机号或密码错误'}), 401
    except Exception as e:
        logger.warning(f"内存用户验证失败: {str(e)}")
        # 记录错误但继续尝试数据库用户认证
        pass
    
    # 如果内存用户认证失败，尝试数据库用户认证
    try:
        # 根据手机号查找用户
        user = User.query.filter_by(phone=phone).first()
        
        if not user:
            return jsonify({'error': '手机号或密码错误'}), 401
            
        # 验证密码
        if user.check_password(password):
            # 检查用户状态
            if not user.is_active:
                return jsonify({'error': '账号已被禁用'}), 403
            
            # 更新最后登录时间
            user.last_login_at = datetime.utcnow()
            db.session.commit()
            
            # 创建访问令牌
            access_token = create_access_token(
                identity=user.id,
                additional_claims={
                    'phone': user.phone,
                    'role': user.role
                },
                expires_delta=timedelta(hours=24)
            )
            
            return jsonify({
                'access_token': access_token,
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'error': '手机号或密码错误'}), 401
    except Exception as e:
        logger.error(f"数据库用户认证失败: {str(e)}")
        return jsonify({'error': '登录失败', 'message': str(e)}), 500

@auth_bp.route('/users/me', methods=['GET'])
def get_current_user():
    """获取当前用户信息"""
    from flask_jwt_extended import get_jwt_identity, jwt_required
    
    @jwt_required()
    def protected():
        # 获取当前用户ID
        current_user_id = get_jwt_identity()
        # 查询用户
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        return jsonify(user.to_dict()), 200
    
    return protected()

# 在app/api/__init__.py中注册这个蓝图 