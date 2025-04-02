-- MySQL数据库初始化脚本
-- 为eduInsight项目创建必要的表

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phone VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(120) UNIQUE,
    username VARCHAR(50) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'student',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    full_name VARCHAR(50),
    avatar VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login_at DATETIME,
    INDEX idx_phone (phone),
    INDEX idx_email (email),
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入初始管理员用户，密码为 admin123
INSERT INTO users (phone, email, username, password_hash, role, full_name)
VALUES ('13800000000', 'admin@eduinsight.com', 'admin', 
        '$2b$12$XBBqFBfQQFLRxIl7wy/VtuYtuEftIecVZj1/J3KcMPl2UasCqblBK', 
        'admin', '系统管理员');

-- 创建教师表
CREATE TABLE IF NOT EXISTS teachers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id VARCHAR(50) NOT NULL UNIQUE COMMENT '工号',
    name VARCHAR(50) NOT NULL COMMENT '姓名',
    gender CHAR(1) NOT NULL COMMENT '性别',
    title VARCHAR(50) NOT NULL COMMENT '职称',
    department VARCHAR(100) NOT NULL COMMENT '所属部门',
    phone VARCHAR(20) NOT NULL COMMENT '联系电话',
    email VARCHAR(120) NOT NULL COMMENT '邮箱',
    office VARCHAR(50) COMMENT '办公室',
    research_area TEXT COMMENT '研究方向',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_teacher_id (teacher_id),
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建学生表
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(50) NOT NULL UNIQUE COMMENT '学号',
    name VARCHAR(50) NOT NULL COMMENT '姓名',
    gender CHAR(1) NOT NULL COMMENT '性别',
    grade VARCHAR(20) NOT NULL COMMENT '年级',
    class_name VARCHAR(50) NOT NULL COMMENT '班级',
    phone VARCHAR(20) NOT NULL COMMENT '联系电话',
    parent_name VARCHAR(50) NOT NULL COMMENT '家长姓名',
    parent_phone VARCHAR(20) NOT NULL COMMENT '家长电话',
    parent_address VARCHAR(200) COMMENT '家庭住址',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_student_id (student_id),
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建课程表
CREATE TABLE IF NOT EXISTS courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '课程名称',
    code VARCHAR(50) UNIQUE COMMENT '课程代码',
    description TEXT COMMENT '课程描述',
    teacher_id INT COMMENT '主讲教师ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 学生-课程关联表
CREATE TABLE IF NOT EXISTS student_courses (
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    enrollment_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态: active, completed, dropped',
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 学习记录表
CREATE TABLE IF NOT EXISTS learning_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    content_type VARCHAR(50) NOT NULL COMMENT '内容类型: video, quiz, reading, exercise, etc.',
    content_id INT NOT NULL COMMENT '内容ID，对应到具体内容',
    start_time DATETIME NOT NULL COMMENT '开始时间',
    end_time DATETIME COMMENT '结束时间',
    duration INT COMMENT '持续时间(秒)',
    progress FLOAT DEFAULT 0 COMMENT '进度(0-100%)',
    score FLOAT COMMENT '分数(如适用)',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    INDEX idx_student_course (student_id, course_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 系统日志表
CREATE TABLE IF NOT EXISTS system_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(100) NOT NULL COMMENT '操作类型',
    description TEXT COMMENT '详细描述',
    ip_address VARCHAR(50) COMMENT 'IP地址',
    user_agent TEXT COMMENT '用户代理信息',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci; 