import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Folder, Clock, ArrowRight, Sparkles, Zap, Layers } from 'lucide-react'
import { projectsApi } from '../services/api'
import type { Project } from '../types'
import { useApp } from '../contexts/AppContext'

export default function HomePage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const { setRefreshProjects } = useApp()

  const loadProjects = async () => {
    try {
      const response = await projectsApi.list()
      if (response.success) {
        setProjects(response.projects)
      }
    } catch (error) {
      console.error('Failed to load projects:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProjects()
    setRefreshProjects(loadProjects)
  }, [setRefreshProjects])

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

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
            <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-primary-600 transition-colors" />
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

      {/* Recent projects */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Clock className="w-5 h-5" />
            最近项目
          </h2>
          <Link
            to="/editor"
            className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
          >
            查看全部
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-500">
            加载中...
          </div>
        ) : projects.length === 0 ? (
          <div className="card p-8 md:p-12 text-center">
            <div className="w-14 h-14 md:w-16 md:h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Folder className="w-7 h-7 md:w-8 md:h-8 text-gray-400" />
            </div>
            <h3 className="text-base md:text-lg font-medium text-gray-900 mb-2">还没有项目</h3>
            <p className="text-sm text-gray-500 mb-4">创建您的第一个流程图项目</p>
            <Link to="/editor" className="btn-primary inline-flex items-center gap-2 text-sm md:text-base">
              <Plus className="w-4 h-4" />
              新建项目
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 md:gap-4">
            {projects.slice(0, 6).map((project) => (
              <Link
                key={project.id}
                to={`/editor/${project.id}`}
                className="card p-3 md:p-4 hover:shadow-md transition-shadow group"
              >
                <div className="aspect-video bg-gray-100 rounded-lg mb-3 overflow-hidden">
                  {project.thumbnail ? (
                    <img
                      src={project.thumbnail}
                      alt={project.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <Sparkles className="w-8 h-8 text-gray-300" />
                    </div>
                  )}
                </div>
                <h3 className="font-medium text-gray-900 mb-1 truncate">
                  {project.name}
                </h3>
                <p className="text-xs text-gray-500">
                  更新于 {formatDate(project.updated_at)}
                </p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
