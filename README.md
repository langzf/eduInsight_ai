# 教育洞察AI系统

## 项目结构

```
eduInsight_ai/
│
├── app/                  # 后端服务代码
│   ├── api/              # API接口
│   ├── core/             # 核心功能
│   ├── models/           # 数据模型
│   ├── services/         # 业务逻辑
│   ├── utils/            # 工具函数
│   ├── __init__.py       # Flask应用初始化
│   ├── config.py         # 后端配置
│   ├── run.py            # 后端启动入口
│   └── start.sh          # 后端启动脚本
│
├── web/                  # 前端代码
│   ├── public/           # 静态资源
│   ├── src/              # 源代码
│   │   ├── components/   # 组件
│   │   ├── pages/        # 页面
│   │   ├── redux/        # 状态管理
│   │   └── ...
│   ├── package.json      # 前端依赖管理
│   └── start.sh          # 前端启动脚本
│
├── model_service/        # 模型服务
│   └── ...
│
├── start.sh              # 总启动脚本
└── README.md             # 项目说明
```

## 环境设置与启动

### 一、使用启动脚本（推荐）

推荐使用提供的启动脚本，它会自动处理环境配置和依赖安装。

```bash
# 1. 确保已安装Conda和Node.js

# 2. 启动整个系统（后端+前端）
./start.sh

# 或者单独启动后端
cd app
./start.sh

# 或者单独启动前端
cd web
./start.sh
```

使用启动脚本的优势：
- 自动创建和激活Conda环境
- 自动安装所需依赖
- 自动检查端口占用并选择可用端口
- 创建必要的配置文件

### 二、手动启动（高级用户）

如果您需要更多控制，可以按以下步骤手动启动：

#### 1. 创建并激活Conda环境

```bash
# 创建conda环境
conda create -n eduinsight python=3.11 -y

# 激活环境
conda activate eduinsight

# 安装后端依赖
pip install flask flask-jwt-extended flask-cors bcrypt requests
```

#### 2. 启动后端服务

```bash
# 确保已激活conda环境
conda activate eduinsight

# 进入项目根目录
cd /path/to/eduInsight_ai

# 启动后端服务
python app/server.py 8091
```

后端服务将在 http://localhost:6060 上运行。如果端口被占用，脚本会自动选择一个可用端口。

#### 3. 配置前端环境

确保`web/.env`文件存在并包含正确的API地址：

```
REACT_APP_API_URL=http://localhost:6060/api/v1
```

#### 4. 启动前端服务

```bash
# 进入前端目录
cd web

# 安装依赖
npm install --legacy-peer-deps

# 启动服务
npm start
```

## 登录与注册

系统提供以下功能：

1. **状态检查**: `/api/v1/auth/status` - 检查API服务是否正常运行
2. **用户注册**: `/api/v1/auth/register` - 新用户注册
3. **用户登录**: `/api/v1/auth/login` - 用户登录获取访问令牌

### 测试账户

首次运行时，系统会自动创建测试账户（如配置中启用）：

- **手机号**: 13800138000
- **密码**: password123

或者您可以通过注册页面创建新账户。

## 系统功能

- **用户管理**: 注册、登录、个人信息管理
- **学习资源**: 课程浏览、学习材料访问
- **学习跟踪**: 进度记录、学习统计
- **个性化推荐**: 基于用户学习记录的课程推荐

## 故障排除

如遇到启动问题，请尝试以下解决方案：

1. **端口占用**：
   - 尝试使用不同的端口启动后端：`python app/run.py 8000`
   - 检查端口占用情况：`lsof -i :8091`（Linux/Mac）或 `netstat -ano | findstr 8091`（Windows）

2. **依赖问题**：
   - 确保已安装所有必要依赖：`pip install -r app/requirements.txt`
   - 前端依赖安装问题：使用`--legacy-peer-deps`选项

3. **环境问题**：
   - 确保使用正确的conda环境：`conda activate eduinsight`
   - 检查Python版本：`python --version`（应为Python 3.11+）

4. **API连接问题**：
   - 确认`web/.env`文件中的API URL配置正确
   - 使用curl或浏览器测试API状态：`curl http://localhost:6060/api/v1/auth/status`

5. **数据库问题**：
   - 检查数据库配置是否正确
   - 尝试重新初始化数据库：`python app/create_db.py`

## 开发者文档

更多开发细节请参阅项目内文档或联系项目管理员。