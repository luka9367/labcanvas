#!/bin/bash

# NanaDraw Installation Script for Linux/Mac

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}     NanaDraw 安装脚本${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

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

# Create directories
echo -e "${CYAN}创建项目目录...${NC}"
mkdir -p "$ROOT_DIR/backend/data/projects"
mkdir -p "$ROOT_DIR/backend/static/gallery"
mkdir -p "$ROOT_DIR/backend/static/bioicons/svgs"
echo -e "${GREEN}✓ 目录创建完成${NC}"
echo ""

# Setup backend
echo -e "${CYAN}安装后端依赖...${NC}"
cd "$ROOT_DIR/backend"

# Create virtual environment
echo -e "${YELLOW}创建 Python 虚拟环境...${NC}"
$PYTHON -m venv .venv

# Activate and install
echo -e "${YELLOW}安装依赖包...${NC}"
source .venv/bin/activate
pip install -r requirements.txt

echo -e "${GREEN}✓ 后端安装完成${NC}"
echo ""

# Setup frontend
echo -e "${CYAN}安装前端依赖...${NC}"
cd "$ROOT_DIR/frontend"

echo -e "${YELLOW}这可能需要几分钟...${NC}"
npm install

echo -e "${GREEN}✓ 前端安装完成${NC}"
echo ""

# Create startup script
echo -e "${CYAN}创建启动脚本...${NC}"
cat > "$ROOT_DIR/start.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
./scripts/start.sh
EOF
chmod +x "$ROOT_DIR/start.sh"

echo -e "${GREEN}✓ 安装完成！${NC}"
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}  安装成功！${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${CYAN}启动方式:${NC}"
echo -e "${YELLOW}  ./start.sh${NC}"
echo ""
echo -e "${CYAN}首次使用请配置 API Key:${NC}"
echo -e "${YELLOW}  访问 http://localhost:3001/settings${NC}"
echo -e "${YELLOW}  填入您的智谱 AI API Key${NC}"
echo ""
