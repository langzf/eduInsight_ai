#!/bin/bash

# 设置日志目录
LOG_DIR="logs"
MAIN_LOG="$LOG_DIR/startup.log"
mkdir -p $LOG_DIR

# 记录启动时间
echo "=== 教育洞察AI系统启动日志 $(date) ===" | tee -a "$MAIN_LOG"
echo "此脚本将同时启动后端服务和前端应用" | tee -a "$MAIN_LOG"
echo "" | tee -a "$MAIN_LOG"

# 确保已安装 conda
if ! command -v conda &> /dev/null; then
  echo "错误: 未安装 conda，请先安装 conda" | tee -a "$MAIN_LOG"
  exit 1
fi

# 确保已安装 node
if ! command -v node &> /dev/null; then
  echo "错误: 未安装 Node.js，请先安装 Node.js" | tee -a "$MAIN_LOG"
  exit 1
fi

# 记录环境信息
echo "系统环境信息:" >> "$MAIN_LOG"
echo "操作系统: $(uname -a)" >> "$MAIN_LOG"
echo "Node.js版本: $(node -v)" >> "$MAIN_LOG"
echo "npm版本: $(npm -v)" >> "$MAIN_LOG"
echo "Python版本: $(python -V 2>&1)" >> "$MAIN_LOG"
echo "Conda版本: $(conda -V 2>&1)" >> "$MAIN_LOG"
echo "" >> "$MAIN_LOG"

# 检查web/.env文件
if [ ! -f "web/.env" ]; then
  echo "创建 web/.env 文件..." | tee -a "$MAIN_LOG"
  echo "REACT_APP_API_URL=http://localhost:6060" > web/.env
else
  # 更新已存在的.env文件
  echo "更新 web/.env 文件..." | tee -a "$MAIN_LOG"
  echo "REACT_APP_API_URL=http://localhost:6060" > web/.env
fi

# 启动后端服务
echo "【1/2】启动后端服务..." | tee -a "$MAIN_LOG"
cd app
./start.sh &
BACKEND_PID=$!
cd ..

# 等待后端启动
echo "等待后端服务启动..." | tee -a "$MAIN_LOG"
sleep 3

# 检查后端服务是否成功启动
if curl -s http://localhost:6060/api/v1/auth/status > /dev/null; then
  echo "后端服务已成功启动" | tee -a "$MAIN_LOG"
else
  echo "警告: 后端服务可能未成功启动，请检查日志 $LOG_DIR/backend.log" | tee -a "$MAIN_LOG"
fi

# 启动前端服务
echo "" | tee -a "$MAIN_LOG"
echo "【2/2】启动前端服务..." | tee -a "$MAIN_LOG"
cd web
./start.sh &
FRONTEND_PID=$!
cd ..

echo "" | tee -a "$MAIN_LOG"
echo "服务已启动!" | tee -a "$MAIN_LOG"
echo "- 后端进程ID: $BACKEND_PID" | tee -a "$MAIN_LOG"
echo "- 前端进程ID: $FRONTEND_PID" | tee -a "$MAIN_LOG"
echo "" | tee -a "$MAIN_LOG"
echo "可以通过以下地址访问:" | tee -a "$MAIN_LOG"
echo "- 前端界面: http://localhost:5050" | tee -a "$MAIN_LOG"
echo "- 后端API: http://localhost:6060/api/v1" | tee -a "$MAIN_LOG"
echo "- API文档: http://localhost:6060" | tee -a "$MAIN_LOG"
echo "" | tee -a "$MAIN_LOG"
echo "日志文件位置:" | tee -a "$MAIN_LOG"
echo "- 主日志: $MAIN_LOG" | tee -a "$MAIN_LOG"
echo "- 后端日志: $LOG_DIR/backend.log" | tee -a "$MAIN_LOG"
echo "- 前端日志: $LOG_DIR/frontend.log" | tee -a "$MAIN_LOG"
echo "" | tee -a "$MAIN_LOG"
echo "测试账户:" | tee -a "$MAIN_LOG"
echo "- 手机号: 13800000000" | tee -a "$MAIN_LOG"
echo "- 密码: admin123" | tee -a "$MAIN_LOG"
echo "" | tee -a "$MAIN_LOG"
echo "按 Ctrl+C 停止所有服务..." | tee -a "$MAIN_LOG"

# 处理停止信号
trap "kill $BACKEND_PID $FRONTEND_PID; echo ''; echo '所有服务已停止' | tee -a '$MAIN_LOG'; exit" INT TERM

# 保持脚本运行
wait 