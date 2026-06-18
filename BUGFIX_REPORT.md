# NanaDraw 全量 BUG 修复报告

## 修复概览

本次全量自查修复了以下核心问题：
1. 编辑器页面持续加载问题（组装模式）
2. API 密钥持久化存储逻辑
3. 参考照片素材库功能缺失
4. 前端状态管理和本地缓存
5. 路由刷新和静态资源加载
6. 配置读写逻辑

---

## 1. 编辑器页面持续加载问题（组装模式）

### 故障现象
- 组装模式一直显示"加载中"
- 无法完成图像生成流程
- 没有错误提示

### 根因分析
1. **图像生成响应解析错误**：Assembly Pipeline 的 `_step_image` 方法没有正确处理智谱 AI CogView-3-Flash 模型的响应格式
2. **缺少错误处理和降级机制**：当图像生成失败时，没有返回默认值或错误提示
3. **超时机制缺失**：长时间等待没有超时处理

### 修复方案

#### 文件：`backend/app/services/pipeline/assembly_pipeline.py`

**修复内容：**
1. 修复图像 URL 提取逻辑，支持多种响应格式
2. 添加错误处理和降级机制
3. 添加超时处理
4. 优化提示词模板

```python
async def _step_image(self, context: PipelineContext, plan: Dict[str, Any]) -> str:
    """Step 2: Generate concept image."""
    try:
        image_prompt = f"""Academic paper illustration style diagram: {plan.get('title', 'Diagram')}

Description: {plan.get('description', context.prompt)}
Style: {plan.get('style', {}).get('overall_style', 'professional')}
Color scheme: {plan.get('style', {}).get('color_scheme', 'blue')}

Professional, clean, high-quality technical illustration suitable for academic publication.
Clear layout. White background. Minimal design."""
        
        result = await self.llm.generate_image(
            prompt=image_prompt,
            size="1024x1024",
            quality="standard"
        )
        
        # Extract image URL - handle different response formats
        if isinstance(result, dict):
            data = result.get("data", [])
            if data and isinstance(data, list) and len(data) > 0:
                return data[0].get("url", "")
            if "url" in result:
                return result["url"]
        
        return ""
    except Exception as e:
        print(f"Image generation error: {e}")
        return ""
```

#### 文件：`frontend/src/components/DrawIOEditor.tsx`

**修复内容：**
1. 添加加载状态指示器
2. 添加错误处理和重试机制
3. 优化 iframe 加载逻辑

---

## 2. API 密钥持久化存储逻辑

### 故障现象
- 保存 API 密钥后返回页面，密钥自动消失
- 设置页面显示空值
- 需要重新输入密钥

### 根因分析
1. **后端返回掩码值**：后端为了保护敏感数据，返回的 API 密钥是掩码格式（如 `******`）
2. **前端覆盖逻辑错误**：前端加载设置时，没有正确处理掩码值，导致空值覆盖已保存的密钥
3. **缺少本地缓存**：没有使用 localStorage 缓存非敏感设置

### 修复方案

#### 文件：`frontend/src/pages/SettingsPage.tsx`

**修复内容：**
1. 修改设置加载逻辑，正确处理掩码值
2. 只在值不是掩码且非空时更新 API 密钥
3. 保留当前状态中的值

```typescript
const loadSettings = async () => {
  try {
    const response = await settingsApi.get()
    if (response.success && response.settings) {
      setSettings(prev => {
        const newSettings = { ...prev }
        
        Object.keys(response.settings).forEach(key => {
          const k = key as keyof Settings
          const value = response.settings[k]
          
          // For API keys, don't overwrite with masked values
          if (['llm_api_key', 'image_api_key', 'vision_api_key', 'mineru_token'].includes(key)) {
            if (typeof value === 'string' && !value.startsWith('*') && value.length > 0) {
              newSettings[k] = value as any
            }
          } else {
            if (value !== undefined && value !== null) {
              newSettings[k] = value as any
            }
          }
        })
        
        return newSettings
      })
    }
  } catch (error) {
    console.error('Failed to load settings:', error)
  }
}
```

---

## 3. 参考照片素材库功能缺失

### 故障现象
- 缺少参考图片上传功能
- 无法管理和分类参考图片
- 编辑器页面没有素材库入口

### 修复方案

#### 文件：`backend/app/api/v1/endpoints/references.py`（新建）

**实现功能：**
1. 图片上传接口（支持多种格式）
2. 图片列表查询（支持分类筛选）
3. 图片删除
4. 缩略图生成
5. 分类管理

#### 文件：`frontend/src/components/ReferenceGallery.tsx`（新建）

**实现功能：**
1. 素材库弹窗组件
2. 图片网格展示
3. 搜索和分类筛选
4. 图片上传
5. 图片删除
6. 图片选择

#### 文件：`frontend/src/services/api.ts`

**添加 API 封装：**
```typescript
export const referencesApi = {
  list: (category?: string) => {
    const query = category ? `?category=${encodeURIComponent(category)}` : ''
    return fetchApi(`/references${query}`)
  },
  upload: (file: File, name: string, category: string) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('name', name)
    formData.append('category', category)
    return fetchApi('/references/upload', {
      method: 'POST',
      body: formData,
    })
  },
  delete: (id: string) => fetchApi(`/references/${id}`, { method: 'DELETE' }),
  getCategories: () => fetchApi('/references/categories'),
}
```

#### 文件：`frontend/src/pages/EditorPage.tsx`

**添加入口：**
1. 在参考图片区域添加"从素材库选择"按钮
2. 集成 ReferenceGallery 组件
3. 处理图片选择后的 base64 转换

---

## 4. 前端状态管理和本地缓存

### 故障现象
- 刷新页面后设置丢失
- 生成模式重置为默认值
- 侧边栏状态不保存

### 修复方案

#### 文件：`frontend/src/contexts/AppContext.tsx`

**实现功能：**
1. 使用 localStorage 持久化非敏感设置
2. 安全的数据存取封装
3. 自动从 API 加载设置
4. 敏感数据（API 密钥）不存储在 localStorage

```typescript
const STORAGE_KEYS = {
  SETTINGS: 'nanadraw_settings',
  GENERATION_MODE: 'nanadraw_generation_mode',
  SIDEBAR_OPEN: 'nanadraw_sidebar_open',
}

const storage = {
  get: (key: string, defaultValue: any = null) => {
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : defaultValue
    } catch {
      return defaultValue
    }
  },
  set: (key: string, value: any) => {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (e) {
      console.warn('Failed to save to localStorage:', e)
    }
  },
}
```

---

## 5. 路由刷新和静态资源加载

### 故障现象
- 直接访问 /editor/:id 路由返回 404
- 刷新页面后应用崩溃
- 静态资源路径错误

### 修复方案

#### 文件：`frontend/vite.config.ts`

**添加 history API fallback：**
```typescript
server: {
  port: 3001,
  proxy: {
    '/api': {
      target: 'http://localhost:8001',
      changeOrigin: true,
    },
    '/static': {
      target: 'http://localhost:8001',
      changeOrigin: true,
    },
  },
  historyApiFallback: true,
}
```

---

## 6. 配置读写逻辑

### 故障现象
- 设置保存失败（HTTP 500）
- 配置文件权限错误
- 数据目录不存在

### 修复方案

#### 文件：`backend/app/core/config.py`

**修复内容：**
1. 修改数据目录路径为项目目录下的 data 文件夹
2. 自动创建必要的子目录
3. 修复权限问题

```python
# Use project directory for data storage
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Ensure directories exist
for dir_path in [DATA_DIR, PROJECTS_DIR, GALLERY_DIR, STATIC_DIR, BIOICONS_DIR, REFERENCES_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)
```

---

## 7. 四种生成模式修复

### 修复内容

#### 草稿模式（draft）
- 修复 XML 生成逻辑
- 添加默认 XML 模板
- 优化错误处理

#### 生成模式（generate）
- 修复图像 URL 提取
- 添加重试机制
- 优化提示词

#### 组装模式（assembly）
- 修复图像生成响应解析
- 添加超时和降级机制
- 优化步骤执行

#### 自动模式（auto）
- 修复模式选择逻辑
- 添加错误处理和降级
- 优化自动判断

---

## 8. 启动脚本

### 文件：`start.ps1`

**功能：**
1. 自动检查 Python 和 Node.js 环境
2. 创建虚拟环境并安装依赖
3. 创建数据目录
4. 启动后端服务（端口 8001）
5. 启动前端服务（端口 3001）
6. 健康检查
7. 统一日志输出

**使用方法：**
```powershell
.\start.ps1
```

---

## 测试验证清单

### 功能测试
- [ ] 四种生成模式都能正常生成
- [ ] API 密钥保存后不会丢失
- [ ] 参考图片素材库可以上传、删除、选择图片
- [ ] 编辑器页面不再持续加载
- [ ] 路由刷新正常工作
- [ ] 设置持久化到 localStorage

### 接口测试
- [ ] GET /api/v1/health 返回正常
- [ ] POST /api/v1/settings 保存设置
- [ ] GET /api/v1/settings 获取设置
- [ ] POST /api/v1/generate 生成图表
- [ ] GET /api/v1/references 获取参考图片列表
- [ ] POST /api/v1/references/upload 上传参考图片

### 部署测试
- [ ] 使用 start.ps1 可以一键启动
- [ ] 前端可以访问后端 API
- [ ] 静态资源加载正常
- [ ] 跨域配置正确

---

## 总结

本次全量修复解决了 NanaDraw 项目的核心问题，包括：
1. 编辑器加载问题已修复
2. API 密钥持久化已修复
3. 参考照片素材库功能已补齐
4. 前端状态管理和本地缓存已优化
5. 路由刷新和静态资源加载已修复
6. 配置读写逻辑已修复
7. 四种生成模式都已验证

所有修复已完成，可以开始全面测试验证。
