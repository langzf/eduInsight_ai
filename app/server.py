#!/usr/bin/env python3
"""
最简单的Flask测试服务器
不依赖项目中任何模块
"""
import os
import sys
import socket
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import bcrypt
from datetime import datetime, timedelta
from flask_jwt_extended import JWTManager, create_access_token

try:
    from flask import Flask, jsonify, render_template_string, send_from_directory
except ImportError:
    print("错误: 缺少Flask模块，请安装: pip install flask")
    sys.exit(1)

# 创建日志目录
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 配置日志
logger = logging.getLogger('eduinsight')
logger.setLevel(logging.DEBUG)

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# 文件处理器
file_handler = RotatingFileHandler(
    os.path.join(log_dir, 'backend.log'),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# 添加处理器
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# 固定端口为6060
PORT = 6060

# 查找可用端口函数保留，但不再使用
def find_available_port(start_port=8091):
    """查找可用端口，从start_port开始尝试"""
    port = start_port
    max_port = start_port + 100  # 尝试100个端口
    
    # 设置socket选项SO_REUSEADDR
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind(('127.0.0.1', port))
        sock.close()
        return port
    except OSError:
        logger.warning(f"端口 {port} 已被占用，尝试其他端口...")
        # 端口被占用，返回None，使用下一个可用端口
        return None
    finally:
        sock.close()

# 创建Flask应用
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 配置
app.config['JSON_AS_ASCII'] = False  # 确保中文正确显示
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')  # 实际应用中应该使用环境变量
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
jwt = JWTManager(app)

# 数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:eduinsight123@localhost:3306/eduinsight'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 定义模型
class Teacher(db.Model):
    """教师模型"""
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(1), nullable=False)
    title = db.Column(db.String(50), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'name': self.name,
            'gender': self.gender,
            'title': self.title,
            'department': self.department,
            'phone': self.phone,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Student(db.Model):
    """学生模型"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(1), nullable=False)
    grade = db.Column(db.String(20), nullable=False)
    major = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.name,
            'gender': self.gender,
            'grade': self.grade,
            'major': self.major,
            'class_name': self.class_name,
            'phone': self.phone,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# 主页HTML模板
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>教育洞察AI系统 - API服务</title>
    <style>
        body {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        h2 {
            color: #3498db;
            margin-top: 30px;
        }
        code {
            background: #f8f8f8;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 2px 5px;
            font-family: Monaco, monospace;
        }
        pre {
            background: #f8f8f8;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            overflow: auto;
        }
        .endpoint {
            margin-bottom: 25px;
            border-left: 3px solid #3498db;
            padding-left: 15px;
        }
        .method {
            display: inline-block;
            padding: 3px 6px;
            border-radius: 3px;
            font-weight: bold;
            margin-right: 10px;
        }
        .get {
            background-color: #61affe;
            color: white;
        }
        .post {
            background-color: #49cc90;
            color: white;
        }
    </style>
</head>
<body>
    <h1>教育洞察AI系统 - API文档</h1>
    <p>欢迎使用教育洞察AI系统后端API服务。以下是可用的API端点：</p>
    
    <h2>认证API</h2>
    
    <div class="endpoint">
        <p><span class="method get">GET</span> <code>/api/v1/auth/status</code></p>
        <p>检查API服务运行状态</p>
        <p>示例响应:</p>
        <pre>{
  "status": "ok",
  "message": "API服务运行正常",
  "version": "1.0.0"
}</pre>
    </div>
    
    <div class="endpoint">
        <p><span class="method post">POST</span> <code>/api/v1/auth/register</code></p>
        <p>用户注册</p>
        <p>请求体:</p>
        <pre>{
  "phone": "13812345678",
  "password": "yourpassword",
  "username": "用户名",
  "email": "user@example.com",
  "full_name": "真实姓名"
}</pre>
    </div>
    
    <div class="endpoint">
        <p><span class="method post">POST</span> <code>/api/v1/auth/login</code></p>
        <p>用户登录</p>
        <p>请求体:</p>
        <pre>{
  "phone": "13812345678",
  "password": "yourpassword"
}</pre>
    </div>

    <h2>测试账户</h2>
    <p>手机号: 13800000000</p>
    <p>密码: admin123</p>
    
    <p style="margin-top: 50px; font-size: 12px; color: #999; text-align: center;">
        &copy; 2025 教育洞察AI系统
    </p>
</body>
</html>
'''

# 内存中用户数据（实际应用中请使用数据库）
users = {
    '13800000000': {
        'phone': '13800000000',
        'password_hash': bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        'username': 'admin',
        'email': 'admin@eduinsight.com',
        'role': 'admin',
        'full_name': '系统管理员',
        'is_active': True,
        'avatar': None,
        'created_at': datetime.now().isoformat(),
        'last_login_at': None
    }
}

# 主页
@app.route('/')
def index():
    return render_template_string(INDEX_TEMPLATE)

# API文档
@app.route('/api')
def api_docs():
    endpoints = [
        {"path": "/", "method": "GET", "description": "主页"},
        {"path": "/hello", "method": "GET", "description": "Hello World API"},
        {"path": "/health", "method": "GET", "description": "健康检查"},
        {"path": "/api", "method": "GET", "description": "API文档"}
    ]
    return jsonify({
        "api": "教育洞察API",
        "version": "1.0.0",
        "endpoints": endpoints
    })

# Hello World
@app.route('/hello')
def hello():
    return jsonify({
        'status': 'ok',
        'message': '你好，世界！'
    })

# 健康检查
@app.route('/health')
def health():
    return jsonify({
        'status': 'up',
        'version': '1.0.0'
    })

# 图标
@app.route('/favicon.ico')
def favicon():
    return '', 204

# API路由
@app.route('/api/v1/auth/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'ok',
        'message': 'API服务运行正常',
        'version': '1.0.0'
    })

@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400
    
    phone = data.get('phone')
    password = data.get('password')
    
    if not phone or not password:
        return jsonify({'error': '手机号和密码为必填项'}), 400
    
    # 检查手机号是否已存在
    if phone in users:
        return jsonify({'error': '该手机号已被注册'}), 409
    
    # 创建新用户
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    users[phone] = {
        'phone': phone,
        'password_hash': password_hash,
        'username': data.get('username'),
        'email': data.get('email'),
        'role': data.get('role', 'student'),
        'full_name': data.get('full_name'),
        'is_active': True,
        'avatar': None,
        'created_at': datetime.now().isoformat(),
        'last_login_at': None
    }
    
    return jsonify({
        'message': '注册成功',
        'user_id': phone
    }), 201

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400
    
    phone = data.get('phone')
    password = data.get('password')
    
    if not phone or not password:
        return jsonify({'error': '手机号和密码为必填项'}), 400
    
    # 尝试从内存字典中获取用户
    user = users.get(phone)
    
    if user:
        # 使用bcrypt验证密码 - 内存用户
        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({'error': '手机号或密码错误'}), 401
            
        # 检查用户状态
        if not user.get('is_active', True):
            return jsonify({'error': '账号已被禁用'}), 403
        
        # 更新最后登录时间
        user['last_login_at'] = datetime.now().isoformat()
        
        # 创建访问令牌
        access_token = create_access_token(
            identity=phone,
            additional_claims={
                'phone': phone,
                'role': user.get('role', 'student')
            }
        )
        
        # 用户信息（不包含密码哈希）
        user_info = {k: v for k, v in user.items() if k != 'password_hash'}
    else:
        # 尝试从数据库获取用户
        try:
            from app.models.user import User
            db_user = User.query.filter_by(phone=phone).first()
            
            if not db_user:
                return jsonify({'error': '手机号或密码错误'}), 401
                
            # 使用werkzeug验证密码 - 数据库用户
            if not db_user.check_password(password):
                return jsonify({'error': '手机号或密码错误'}), 401
                
            # 检查用户状态
            if not db_user.is_active:
                return jsonify({'error': '账号已被禁用'}), 403
                
            # 更新最后登录时间
            db_user.last_login_at = datetime.now()
            from app import db
            db.session.commit()
            
            # 创建访问令牌
            access_token = create_access_token(
                identity=db_user.id,
                additional_claims={
                    'phone': db_user.phone,
                    'role': db_user.role
                }
            )
            
            # 转换用户信息为字典
            user_info = db_user.to_dict()
            
        except Exception as e:
            app.logger.error(f"数据库用户认证失败: {str(e)}")
            return jsonify({'error': '认证失败', 'message': str(e)}), 500
    
    return jsonify({
        'access_token': access_token,
        'user': user_info
    }), 200

@app.route('/api/v1/teachers', methods=['GET'])
def get_teachers():
    """获取教师列表"""
    logger.info("收到获取教师列表请求")
    try:
        teachers = Teacher.query.all()
        logger.debug(f"获取到 {len(teachers)} 个教师记录")
        return jsonify([teacher.to_dict() for teacher in teachers])
    except Exception as e:
        logger.error(f"获取教师列表失败: {str(e)}")
        return jsonify({"error": "获取教师列表失败"}), 500

@app.route('/api/v1/teachers', methods=['POST'])
def create_teacher():
    """创建教师"""
    logger.info("收到创建教师请求")
    try:
        data = request.get_json()
        logger.debug(f"请求数据: {data}")
        
        teacher = Teacher(
            teacher_id=data['teacher_id'],
            name=data['name'],
            gender=data['gender'],
            title=data['title'],
            department=data['department'],
            phone=data['phone'],
            email=data['email'],
            office=data.get('office'),
            research_area=data.get('research_area')
        )
        
        db.session.add(teacher)
        db.session.commit()
        
        return jsonify(teacher.to_dict()), 201
    except Exception as e:
        logger.error(f"创建教师失败: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "创建教师失败"}), 500

@app.route('/api/v1/teachers/<int:id>', methods=['PUT'])
def update_teacher(id):
    """更新教师信息"""
    logger.info(f"收到更新教师请求，ID: {id}")
    try:
        teacher = Teacher.query.get(id)
        if not teacher:
            return jsonify({"error": "教师不存在"}), 404
            
        data = request.get_json()
        logger.debug(f"请求数据: {data}")
        
        for key, value in data.items():
            if hasattr(teacher, key):
                setattr(teacher, key, value)
        
        db.session.commit()
        return jsonify(teacher.to_dict())
    except Exception as e:
        logger.error(f"更新教师失败: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "更新教师失败"}), 500

@app.route('/api/v1/teachers/<int:id>', methods=['DELETE'])
def delete_teacher(id):
    """删除教师"""
    logger.info(f"收到删除教师请求，ID: {id}")
    try:
        teacher = Teacher.query.get(id)
        if not teacher:
            return jsonify({"error": "教师不存在"}), 404
            
        db.session.delete(teacher)
        db.session.commit()
        return jsonify({"message": "删除成功"})
    except Exception as e:
        logger.error(f"删除教师失败: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "删除教师失败"}), 500

@app.route('/api/v1/students', methods=['GET'])
def get_students():
    """获取学生列表"""
    logger.info("收到获取学生列表请求")
    try:
        students = Student.query.all()
        logger.debug(f"获取到 {len(students)} 个学生记录")
        return jsonify([student.to_dict() for student in students])
    except Exception as e:
        logger.error(f"获取学生列表失败: {str(e)}")
        return jsonify({"error": "获取学生列表失败"}), 500

@app.route('/api/v1/students', methods=['POST'])
def create_student():
    """创建学生"""
    logger.info("收到创建学生请求")
    try:
        data = request.get_json()
        logger.debug(f"请求数据: {data}")
        
        student = Student(
            student_id=data['student_id'],
            name=data['name'],
            gender=data['gender'],
            grade=data['grade'],
            class_name=data['class_name'],
            phone=data['phone'],
            parent_name=data['parent']['name'],
            parent_phone=data['parent']['phone'],
            parent_address=data['parent'].get('address')
        )
        
        db.session.add(student)
        db.session.commit()
        
        return jsonify(student.to_dict()), 201
    except Exception as e:
        logger.error(f"创建学生失败: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "创建学生失败"}), 500

@app.route('/api/v1/students/<int:id>', methods=['PUT'])
def update_student(id):
    """更新学生信息"""
    logger.info(f"收到更新学生请求，ID: {id}")
    try:
        student = Student.query.get(id)
        if not student:
            return jsonify({"error": "学生不存在"}), 404
            
        data = request.get_json()
        logger.debug(f"请求数据: {data}")
        
        # 更新基本信息
        for key in ['student_id', 'name', 'gender', 'grade', 'class_name', 'phone']:
            if key in data:
                setattr(student, key, data[key])
        
        # 更新家长信息
        if 'parent' in data:
            parent = data['parent']
            if 'name' in parent:
                student.parent_name = parent['name']
            if 'phone' in parent:
                student.parent_phone = parent['phone']
            if 'address' in parent:
                student.parent_address = parent['address']
        
        db.session.commit()
        return jsonify(student.to_dict())
    except Exception as e:
        logger.error(f"更新学生失败: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "更新学生失败"}), 500

@app.route('/api/v1/students/<int:id>', methods=['DELETE'])
def delete_student(id):
    """删除学生"""
    logger.info(f"收到删除学生请求，ID: {id}")
    try:
        student = Student.query.get(id)
        if not student:
            return jsonify({"error": "学生不存在"}), 404
            
        db.session.delete(student)
        db.session.commit()
        return jsonify({"message": "删除成功"})
    except Exception as e:
        logger.error(f"删除学生失败: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "删除学生失败"}), 500

# 入口点
if __name__ == "__main__":
    try:
        # 固定使用端口6060
        port = PORT
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            sock.bind(('127.0.0.1', port))
            sock.close()
        except OSError:
            logger.error(f"错误: 端口 {port} 已被占用，请先停止占用该端口的服务")
            print(f"错误: 端口 {port} 已被占用，请先停止占用该端口的服务")
            sys.exit(1)
            
        logger.info(f"启动服务器在 http://127.0.0.1:{port}")
        app.run(
            host='127.0.0.1', 
            port=port, 
            debug=True, 
            use_reloader=False,  # 禁用重加载器
            threaded=True
        )
    except Exception as e:
        logger.error(f"启动服务器失败: {str(e)}")
        print(f"错误: {str(e)}")
        sys.exit(1) 