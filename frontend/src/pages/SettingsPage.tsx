import { useEffect, useState } from 'react'
import { Save, Key, Bot, Database, Trash2, LogOut, Eye, EyeOff } from 'lucide-react'
import { settingsApi } from '../services/api'
import type { Settings } from '../types'

// Storage key for API keys (encrypted/obfuscated in real app)
const API_KEY_STORAGE_KEY = 'labcanvas_api_keys'

interface ApiKeys {
  llm_api_key: string
  image_api_key: string
  vision_api_key: string
  mineru_token: string
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>({
    llm_api_key: '',
    llm_base_url: 'https://open.bigmodel.cn/api/paas/v4',
    llm_model: 'glm-4-flash',
    llm_image_model: 'cogview-3-flash',
    llm_component_model: 'glm-4-flash',
    image_api_key: '',
    vision_api_key: '',
    image_base_url: 'https://open.bigmodel.cn/api/paas/v4',
    vision_base_url: 'https://open.bigmodel.cn/api/paas/v4',
    api_format: 'zhipu',
    nanasoul_prompt: '',
    mineru_token: '',
    theme: 'light',
    language: 'zh',
  })
  const [loading, setLoading] = useState(false)
  const [saved, setSaved] = useState(false)
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({
    llm_api_key: false,
    image_api_key: false,
    vision_api_key: false,
    mineru_token: false,
  })

  // Load settings on mount
  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      // Migrate old nanadraw storage key to labcanvas
      const oldStoredKeys = localStorage.getItem('nanadraw_api_keys')
      if (oldStoredKeys && !localStorage.getItem(API_KEY_STORAGE_KEY)) {
        localStorage.setItem(API_KEY_STORAGE_KEY, oldStoredKeys)
        localStorage.removeItem('nanadraw_api_keys')
        console.log('Migrated API keys from nanadraw to labcanvas storage')
      }

      // First load from localStorage for API keys
      const storedKeys = localStorage.getItem(API_KEY_STORAGE_KEY)
      let localKeys: Partial<ApiKeys> = {}
      if (storedKeys) {
        try {
          localKeys = JSON.parse(storedKeys)
        } catch {
          console.warn('Failed to parse stored API keys')
        }
      }

      // Then fetch from server
      const response = await settingsApi.get()
      if (response.success && response.settings) {
        setSettings(prev => {
          const newSettings = { ...prev }
          
          Object.keys(response.settings).forEach(key => {
            const k = key as keyof Settings
            const value = response.settings[k]
            
            if (['llm_api_key', 'image_api_key', 'vision_api_key', 'mineru_token'].includes(key)) {
              // Priority: 1. localStorage, 2. server value (if not masked), 3. keep current
              const localValue = localKeys[key as keyof ApiKeys]
              if (localValue && localValue.length > 0) {
                // Use localStorage value
                newSettings[k] = localValue as any
              } else if (typeof value === 'string' && value.length > 0 && !value.startsWith('*')) {
                // Use server value if not masked
                newSettings[k] = value as any
                // Also save to localStorage
                localKeys[key as keyof ApiKeys] = value
              }
            } else {
              // For other fields, always update from server
              if (value !== undefined && value !== null) {
                newSettings[k] = value as any
              }
            }
          })
          
          return newSettings
        })

        // Save keys to localStorage
        if (Object.keys(localKeys).length > 0) {
          localStorage.setItem(API_KEY_STORAGE_KEY, JSON.stringify(localKeys))
        }
      }
    } catch (error) {
      console.error('Failed to load settings:', error)
    }
  }

  const handleSave = async () => {
    setLoading(true)
    try {
      await settingsApi.update(settings)
      
      // Save API keys to localStorage for persistence
      const keysToStore: ApiKeys = {
        llm_api_key: settings.llm_api_key || '',
        image_api_key: settings.image_api_key || '',
        vision_api_key: settings.vision_api_key || '',
        mineru_token: settings.mineru_token || '',
      }
      localStorage.setItem(API_KEY_STORAGE_KEY, JSON.stringify(keysToStore))
      
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (error) {
      alert('保存失败：' + (error instanceof Error ? error.message : '未知错误'))
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (field: keyof Settings, value: string) => {
    setSettings(prev => ({ ...prev, [field]: value }))
  }

  const handleClearKey = (field: keyof ApiKeys) => {
    if (!confirm(`确定要清除 ${getKeyLabel(field)} 吗？`)) return
    
    setSettings(prev => ({ ...prev, [field]: '' }))
    
    // Also clear from localStorage
    const storedKeys = localStorage.getItem(API_KEY_STORAGE_KEY)
    if (storedKeys) {
      try {
        const keys = JSON.parse(storedKeys)
        delete keys[field]
        localStorage.setItem(API_KEY_STORAGE_KEY, JSON.stringify(keys))
      } catch {
        console.warn('Failed to update stored API keys')
      }
    }
  }

  const handleClearAllKeys = () => {
    if (!confirm('确定要清除所有 API 密钥吗？这将退出登录状态。')) return
    
    setSettings(prev => ({
      ...prev,
      llm_api_key: '',
      image_api_key: '',
      vision_api_key: '',
      mineru_token: '',
    }))
    
    // Clear from localStorage
    localStorage.removeItem(API_KEY_STORAGE_KEY)
    
    // Also clear from server
    settingsApi.update({
      llm_api_key: '',
      image_api_key: '',
      vision_api_key: '',
      mineru_token: '',
    }).catch(console.error)
    
    alert('所有 API 密钥已清除')
  }

  const toggleShowKey = (field: string) => {
    setShowKeys(prev => ({ ...prev, [field]: !prev[field] }))
  }

  const getKeyLabel = (field: string): string => {
    const labels: Record<string, string> = {
      llm_api_key: '智谱 AI API Key',
      image_api_key: '图像生成 API Key',
      vision_api_key: '视觉分析 API Key',
      mineru_token: 'MinerU Token',
    }
    return labels[field] || field
  }

  const formatKeyDisplay = (key: string): string => {
    if (!key || key.length === 0) return ''
    if (key.length <= 8) return '*'.repeat(key.length)
    return key.slice(0, 8) + '****'
  }

  return (
    <div className="p-4 md:p-6 max-w-4xl mx-auto">
      <div className="mb-4 md:mb-6">
        <h1 className="text-xl md:text-2xl font-bold text-gray-900">设置</h1>
        <p className="text-sm md:text-base text-gray-600">配置 API 密钥和模型参数</p>
      </div>

      <div className="space-y-4 md:space-y-6">
        {/* API Keys Section */}
        <div className="card p-4 md:p-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <div className="flex items-center gap-2">
              <Key className="w-5 h-5 text-primary-600" />
              <h2 className="text-base md:text-lg font-semibold">API 密钥</h2>
            </div>
            <button
              onClick={handleClearAllKeys}
              className="flex items-center justify-center gap-2 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
              退出登录 / 清除所有密钥
            </button>
          </div>
          
          <div className="space-y-4">
            {/* LLM API Key */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                智谱 AI API Key
              </label>
              <div className="relative">
                <input
                  type={showKeys.llm_api_key ? 'text' : 'password'}
                  value={settings.llm_api_key}
                  onChange={(e) => handleChange('llm_api_key', e.target.value)}
                  placeholder={settings.llm_api_key ? formatKeyDisplay(settings.llm_api_key) : "请输入您的智谱 AI API Key"}
                  className="input pr-20"
                />
                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                  {settings.llm_api_key && (
                    <button
                      onClick={() => handleClearKey('llm_api_key')}
                      className="p-1.5 text-red-500 hover:bg-red-50 rounded"
                      title="清除密钥"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                  <button
                    onClick={() => toggleShowKey('llm_api_key')}
                    className="p-1.5 text-gray-500 hover:bg-gray-100 rounded"
                    title={showKeys.llm_api_key ? '隐藏' : '显示'}
                  >
                    {showKeys.llm_api_key ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                获取地址：<a href="https://bigmodel.cn" target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">bigmodel.cn</a>
                {settings.llm_api_key && (
                  <span className="ml-2 text-green-600">✓ 已保存</span>
                )}
              </p>
            </div>

            {/* Image API Key */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                图像生成 API Key（可选，默认使用文本模型 Key）
              </label>
              <div className="relative">
                <input
                  type={showKeys.image_api_key ? 'text' : 'password'}
                  value={settings.image_api_key}
                  onChange={(e) => handleChange('image_api_key', e.target.value)}
                  placeholder={settings.image_api_key ? formatKeyDisplay(settings.image_api_key) : "可选"}
                  className="input pr-20"
                />
                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                  {settings.image_api_key && (
                    <button
                      onClick={() => handleClearKey('image_api_key')}
                      className="p-1.5 text-red-500 hover:bg-red-50 rounded"
                      title="清除密钥"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                  <button
                    onClick={() => toggleShowKey('image_api_key')}
                    className="p-1.5 text-gray-500 hover:bg-gray-100 rounded"
                    title={showKeys.image_api_key ? '隐藏' : '显示'}
                  >
                    {showKeys.image_api_key ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              {settings.image_api_key && (
                <p className="text-xs text-green-600 mt-1">✓ 已保存</p>
              )}
            </div>

            {/* Vision API Key */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                视觉分析 API Key（可选，默认使用文本模型 Key）
              </label>
              <div className="relative">
                <input
                  type={showKeys.vision_api_key ? 'text' : 'password'}
                  value={settings.vision_api_key}
                  onChange={(e) => handleChange('vision_api_key', e.target.value)}
                  placeholder={settings.vision_api_key ? formatKeyDisplay(settings.vision_api_key) : "可选"}
                  className="input pr-20"
                />
                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                  {settings.vision_api_key && (
                    <button
                      onClick={() => handleClearKey('vision_api_key')}
                      className="p-1.5 text-red-500 hover:bg-red-50 rounded"
                      title="清除密钥"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                  <button
                    onClick={() => toggleShowKey('vision_api_key')}
                    className="p-1.5 text-gray-500 hover:bg-gray-100 rounded"
                    title={showKeys.vision_api_key ? '隐藏' : '显示'}
                  >
                    {showKeys.vision_api_key ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              {settings.vision_api_key && (
                <p className="text-xs text-green-600 mt-1">✓ 已保存</p>
              )}
            </div>
          </div>
        </div>

        {/* Model Settings */}
        <div className="card p-4 md:p-6">
          <div className="flex items-center gap-2 mb-4">
            <Bot className="w-5 h-5 text-primary-600" />
            <h2 className="text-base md:text-lg font-semibold">模型设置</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                文本模型
              </label>
              <select
                value={settings.llm_model}
                onChange={(e) => handleChange('llm_model', e.target.value)}
                className="input"
              >
                <option value="glm-4-flash">GLM-4-Flash（免费）</option>
                <option value="glm-4">GLM-4</option>
                <option value="glm-4v-flash">GLM-4V-Flash（视觉）</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                图像生成模型
              </label>
              <select
                value={settings.llm_image_model}
                onChange={(e) => handleChange('llm_image_model', e.target.value)}
                className="input"
              >
                <option value="cogview-3-flash">CogView-3-Flash（免费）</option>
                <option value="cogview-3">CogView-3</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                组件生成模型
              </label>
              <select
                value={settings.llm_component_model}
                onChange={(e) => handleChange('llm_component_model', e.target.value)}
                className="input"
              >
                <option value="glm-4-flash">GLM-4-Flash（免费）</option>
                <option value="glm-4">GLM-4</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                API 格式
              </label>
              <select
                value={settings.api_format}
                onChange={(e) => handleChange('api_format', e.target.value)}
                className="input"
              >
                <option value="zhipu">智谱 AI</option>
                <option value="openai">OpenAI 兼容</option>
              </select>
            </div>
          </div>
        </div>

        {/* Advanced Settings */}
        <div className="card p-4 md:p-6">
          <div className="flex items-center gap-2 mb-4">
            <Database className="w-5 h-5 text-primary-600" />
            <h2 className="text-base md:text-lg font-semibold">高级设置</h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                文本模型 Base URL
              </label>
              <input
                type="text"
                value={settings.llm_base_url}
                onChange={(e) => handleChange('llm_base_url', e.target.value)}
                className="input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                图像模型 Base URL
              </label>
              <input
                type="text"
                value={settings.image_base_url}
                onChange={(e) => handleChange('image_base_url', e.target.value)}
                className="input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                视觉模型 Base URL
              </label>
              <input
                type="text"
                value={settings.vision_base_url}
                onChange={(e) => handleChange('vision_base_url', e.target.value)}
                className="input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                MinerU Token（PDF 解析）
              </label>
              <div className="relative">
                <input
                  type={showKeys.mineru_token ? 'text' : 'password'}
                  value={settings.mineru_token}
                  onChange={(e) => handleChange('mineru_token', e.target.value)}
                  placeholder={settings.mineru_token ? formatKeyDisplay(settings.mineru_token) : "可选"}
                  className="input pr-20"
                />
                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                  {settings.mineru_token && (
                    <button
                      onClick={() => handleClearKey('mineru_token')}
                      className="p-1.5 text-red-500 hover:bg-red-50 rounded"
                      title="清除 Token"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                  <button
                    onClick={() => toggleShowKey('mineru_token')}
                    className="p-1.5 text-gray-500 hover:bg-gray-100 rounded"
                    title={showKeys.mineru_token ? '隐藏' : '显示'}
                  >
                    {showKeys.mineru_token ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              {settings.mineru_token && (
                <p className="text-xs text-green-600 mt-1">✓ 已保存</p>
              )}
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-end gap-3">
          {saved && (
            <span className="text-green-600 text-sm text-center sm:text-right">保存成功！</span>
          )}
          <button
            onClick={handleSave}
            disabled={loading}
            className="btn-primary flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                保存中...
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                保存设置
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
