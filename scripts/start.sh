#!/bin/bash

# NanaDraw Startup Script for Linux/Mac

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}       NanaDraw 启动脚本${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Function to cleanup processes on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止服务...${NC}"
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}✓ 服务已停止${NC}"
    exit 0
}

trap cleanup EXIT INT TERM

# Check Python
echo -e "${CYAN}检查 Python 环境...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo -e "${RED}✗ 未找到 Python，请安装 Python 3.9+${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON --version 2>&1)
echo -e "${GREEN}✓ $PYTHON_VERSION${NC}"

# Check Node.js
echo -e "${CYAN}检查 Node.js 环境...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ 未找到 Node.js，请安装 Node.js 18+${NC}"
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js $NODE_VERSION${NC}"

echo ""

# Setup backend
echo -e "${CYAN}设置后端环境...${NC}"
cd "$ROOT_DIR/backend"

# Create virtual environment if not exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}创建虚拟环境...${NC}"
    $PYTHON -m venv .venv
fi

# Activate virtual environment
echo -e "${YELLOW}激活虚拟环境...${NC}"
source .venv/bin/activate

# Install dependencies
echo -e "${YELLOW}安装后端依赖...${NC}"
pip install -q -r requirements.txt

# Create necessary directories
mkdir -p data/projects static/gallery static/bioicons/svgs

echo -e "${GREEN}✓ 后端环境准备完成${NC}"
echo ""

# Setup frontend
echo -e "${CYAN}设置前端环境...${NC}"
cd "$ROOT_DIR/frontend"

# Check node_modules
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}安装前端依赖...${NC}"
    npm install
fi

echo -e "${GREEN}✓ 前端环境准备完成${NC}"
echo ""

# Start backend
echo -e "${CYAN}启动后端服务...${NC}"
cd "$ROOT_DIR/backend"
export PYTHONPATH="$ROOT_DIR/backend"
$PYTHON -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload &
BACKEND_PID=$!

# Wait for backend to start
echo -e "${YELLOW}等待后端启动...${NC}"
sleep 3

# Check if backend is running
if curl -s http://localhost:8001/api/v1/models > /dev/null; then
    echo -e "${GREEN}✓ 后端服务已启动 (http://localhost:8001)${NC}"
else
    echo -e "${YELLOW}⚠ 后端可能还在启动中，请稍候...${NC}"
fi

echo ""

# Start frontend
echo -e "${CYAN}启动前端服务...${NC}"
cd "$ROOT_DIR/frontend"

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}  NanaDraw 正在运行！${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${CYAN}  前端地址: http://localhost:3001${NC}"
echo -e "${CYAN}  后端地址: http://localhost:8001${NC}"
echo -e "${CYAN}  API 文档: http://localhost:8001/docs${NC}"
echo ""
echo -e "${YELLOW}  按 Ctrl+C 停止服务${NC}"
echo ""

# Start frontend (this will block)
npm run dev
