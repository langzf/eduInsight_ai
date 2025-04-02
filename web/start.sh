#!/bin/bash

# 设置日志文件
LOG_FILE="../logs/frontend.log"
MAIN_LOG="../logs/main.log"
mkdir -p ../logs

# 添加日志头部
echo "=== 前端服务启动日志 $(date) ===" > "$LOG_FILE"

# 检查当前目录是否包含package.json
if [ ! -f "package.json" ]; then
  echo "错误: 必须在前端根目录 (web/) 下运行此脚本" | tee -a "$LOG_FILE"
  exit 1
fi

# 检查Node.js是否已安装
if ! command -v node &> /dev/null; then
  echo "错误: 未安装Node.js" | tee -a "$LOG_FILE"
  exit 1
fi

# 检查环境变量文件
echo "REACT_APP_API_URL=http://localhost:6060" > .env
echo "环境变量已设置: REACT_APP_API_URL=http://localhost:6060" | tee -a "$LOG_FILE"

# 记录Node.js和npm版本
echo "Node.js版本: $(node -v)" | tee -a "$LOG_FILE"
echo "npm版本: $(npm -v)" | tee -a "$LOG_FILE"

# 清理和重新安装依赖
echo "清理并重新安装依赖..." | tee -a "$LOG_FILE"
rm -rf node_modules package-lock.json .cache
npm install --legacy-peer-deps 2>&1 | tee -a "$LOG_FILE"

if [ $? -ne 0 ]; then
  echo "错误: npm依赖安装失败，请查看日志文件了解详情" | tee -a "$LOG_FILE"
  exit 1
fi

# 设置固定端口并启动前端服务
PORT=5050
echo "启动前端服务在端口: $PORT..." | tee -a "$LOG_FILE"
PORT=$PORT npm start 2>&1 | tee -a "$LOG_FILE" 