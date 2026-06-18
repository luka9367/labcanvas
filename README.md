# NanaDraw

AI 驱动的学术绘图工具，将论文中的方法描述转换为可编辑的流程图。

## 功能特性

- **多种生成模式**：草稿模式、生成模式、组装模式、自动模式
- **AI 驱动**：使用智谱 AI (GLM-4-Flash, CogView-3-Flash) 免费模型
- **可编辑图表**：集成 draw.io 编辑器，支持完全自定义
- **素材库**：内置科学图标库和参考图片库
- **项目管理**：保存和管理多个绘图项目

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+
- Windows / Linux / macOS

### 安装

**Windows:**
```powershell
# 克隆或解压项目后，运行安装脚本
.\scripts\install.ps1
```

**Linux/Mac:**
```bash
# 克隆或解压项目后，运行安装脚本
chmod +x scripts/install.sh
./scripts/install.sh
```

### 启动

**Windows:**
```powershell
.\scripts\start.ps1
# 或双击 start.bat
```

**Linux/Mac:**
```bash
./start.sh
# 或
./scripts/start.sh
```

启动后访问：
- 前端界面：http://localhost:3001
- 后端 API：http://localhost:8001
- API 文档：http://localhost:8001/docs

### 配置 API Key

1. 访问 http://localhost:3001/settings
2. 填入您的智谱 AI API Key
3. 点击保存

获取智谱 AI API Key：[bigmodel.cn](https://bigmodel.cn)

## 使用指南

### 1. 创建新项目

- 点击"新建项目"或进入编辑器页面
- 输入项目名称
- 选择生成模式

### 2. 选择生成模式

- **自动模式**：AI 自动选择最佳生成方式
- **草稿模式**：生成可编辑的流程图草图，适合快速构思
- **生成模式**：直接生成高保真图像，适合灵感探索
- **组装模式**：结构化组装高质量图表，适合正式发表

### 3. 输入描述

在输入框中描述您想要的图表，例如：

```
生成一个机器学习训练流程图，包含：
1. 数据预处理（数据清洗、特征工程）
2. 模型训练（神经网络训练）
3. 模型评估（准确率、召回率）
4. 模型部署（API服务）
```

### 4. 编辑和导出

- 使用 draw.io 编辑器修改生成的图表
- 支持导出为 PNG、SVG、XML 格式

## 项目结构

```
nanadraw/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/         # API 端点
│   │   ├── core/        # 核心配置
│   │   ├── schemas/     # 数据模型
│   │   └── services/    # 业务逻辑
│   │       └── pipeline/# 生成管道
│   ├── data/            # 数据存储
│   ├── static/          # 静态资源
│   └── requirements.txt # Python 依赖
├── frontend/            # React 前端
│   ├── src/
│   │   ├── components/  # 组件
│   │   ├── pages/       # 页面
│   │   ├── services/    # API 服务
│   │   └── types/       # TypeScript 类型
│   └── package.json     # Node 依赖
└── scripts/             # 启动脚本
```

## 技术栈

- **后端**：FastAPI + Python 3.9+
- **前端**：React + TypeScript + Tailwind CSS + Vite
- **编辑器**：draw.io (diagrams.net)
- **AI 模型**：智谱 AI (GLM-4-Flash, CogView-3-Flash)

## API 说明

### 生成接口

```bash
POST /api/v1/generate
{
  "prompt": "生成一个神经网络架构图",
  "mode": "draft",
  "language": "zh"
}
```

### 项目管理

```bash
GET    /api/v1/projects          # 列出项目
POST   /api/v1/projects          # 创建项目
GET    /api/v1/projects/{id}     # 获取项目
PUT    /api/v1/projects/{id}     # 更新项目
DELETE /api/v1/projects/{id}     # 删除项目
```

### 设置管理

```bash
GET  /api/v1/settings            # 获取设置
POST /api/v1/settings            # 更新设置
```

## 开发

### 后端开发

```bash
cd backend
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uvicorn app.main:app --reload --port 8001
```

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

## 许可证

MIT License

## 致谢

- [draw.io](https://www.diagrams.net/) - 强大的图表编辑器
- [智谱 AI](https://bigmodel.cn/) - 提供大模型能力
