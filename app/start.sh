#!/bin/bash

# 设置日志文件
LOG_FILE="../logs/backend.log"
mkdir -p ../logs

# 记录启动时间
echo "=== 后端启动日志 $(date) ===" >> "$LOG_FILE"

# 确保当前目录是app目录
if [ ! -f "./server.py" ]; then
  echo "错误: 请在app目录下运行此脚本" | tee -a "$LOG_FILE"
  exit 1
fi

# 检查conda是否安装
if ! command -v conda &> /dev/null; then
  echo "错误: 未安装conda，请先安装conda" | tee -a "$LOG_FILE"
  exit 1
fi

# 记录Python和conda版本
echo "Python 版本: $(python -V 2>&1)" >> "$LOG_FILE"
echo "Conda 版本: $(conda -V 2>&1)" >> "$LOG_FILE"

# 检查并创建conda环境
ENV_NAME="eduinsight"
if ! conda env list | grep -q "^$ENV_NAME "; then
  echo "创建conda环境: $ENV_NAME..." | tee -a "$LOG_FILE"
  conda create -n $ENV_NAME python=3.11 -y 2>&1 | tee -a "$LOG_FILE"
fi

# 激活conda环境
echo "激活conda环境: $ENV_NAME..." | tee -a "$LOG_FILE"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate $ENV_NAME

# 安装依赖
echo "安装Python依赖..." | tee -a "$LOG_FILE"
pip install flask flask-jwt-extended flask-cors bcrypt requests 2>&1 | tee -a "$LOG_FILE"

# 记录已安装的包
echo "已安装的Python包:" >> "$LOG_FILE"
pip list >> "$LOG_FILE"

# 设置固定端口
PORT=6060

# 检查端口是否可用
if lsof -i:$PORT -t >/dev/null 2>&1; then
  echo "错误: 端口 $PORT 已被占用，请先停止占用该端口的服务" | tee -a "$LOG_FILE"
  exit 1
fi

echo "启动后端服务在端口 $PORT..." | tee -a "$LOG_FILE"
python server.py 2>&1 | tee -a "$LOG_FILE" 