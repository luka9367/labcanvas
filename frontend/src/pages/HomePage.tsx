import { Link } from 'react-router-dom'
import { Plus, Sparkles, Zap, Layers } from 'lucide-react'

export default function HomePage() {
  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto">
      {/* Hero section */}
      <div className="mb-6 md:mb-8">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
          欢迎使用 LabCanvas
        </h1>
        <p className="text-sm md:text-base text-gray-600">
          将学术论文中的方法描述转换为可编辑的流程图
        </p>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4 mb-6 md:mb-8">
        <Link
          to="/editor"
          className="card p-4 md:p-6 hover:shadow-md transition-shadow group"
        >
          <div className="flex items-start justify-between">
            <div>
              <div className="w-9 h-9 md:w-10 md:h-10 bg-primary-100 rounded-lg flex items-center justify-center mb-3 md:mb-4">
                <Plus className="w-4 h-4 md:w-5 md:h-5 text-primary-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-1">新建项目</h3>
              <p className="text-xs md:text-sm text-gray-500">开始创建新的流程图</p>
            </div>
          </div>
        </Link>

        <div className="card p-4 md:p-6">
          <div className="w-9 h-9 md:w-10 md:h-10 bg-green-100 rounded-lg flex items-center justify-center mb-3 md:mb-4">
            <Zap className="w-4 h-4 md:w-5 md:h-5 text-green-600" />
          </div>
          <h3 className="font-semibold text-gray-900 mb-1">AI 驱动</h3>
          <p className="text-xs md:text-sm text-gray-500">使用智谱AI大模型生成高质量图表</p>
        </div>

        <div className="card p-4 md:p-6">
          <div className="w-9 h-9 md:w-10 md:h-10 bg-purple-100 rounded-lg flex items-center justify-center mb-3 md:mb-4">
            <Layers className="w-4 h-4 md:w-5 md:h-5 text-purple-600" />
          </div>
          <h3 className="font-semibold text-gray-900 mb-1">多种模式</h3>
          <p className="text-xs md:text-sm text-gray-500">草稿、生成、组装三种模式</p>
        </div>
      </div>

      {/* Features */}
      <div className="card p-4 md:p-6">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-5 h-5 text-primary-600" />
          <h2 className="text-lg font-semibold text-gray-900">快速开始</h2>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          点击"新建项目"进入创作模式，输入论文方法描述，AI 将自动生成可编辑的学术流程图。
        </p>
        <Link to="/editor" className="btn-primary inline-flex items-center gap-2 text-sm md:text-base">
          <Plus className="w-4 h-4" />
          立即创建
        </Link>
      </div>
    </div>
  )
}
