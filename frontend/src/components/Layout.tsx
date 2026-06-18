import { Outlet, Link, useLocation } from 'react-router-dom'
import { useState } from 'react'
import { 
  Home, 
  Settings, 
  Image, 
  FolderOpen, 
  Menu,
  X,
  Sparkles,
  Wand2,
  Palette,
  Rocket
} from 'lucide-react'
import { useApp } from '../contexts/AppContext'
import VersionUpdateModal from './VersionUpdateModal'

export default function Layout() {
  const location = useLocation()
  const { sidebarOpen, setSidebarOpen } = useApp()
  const [versionModalOpen, setVersionModalOpen] = useState(false)

  const navItems = [
    { path: '/', icon: Home, label: '首页' },
    { path: '/editor', icon: Wand2, label: '创作' },
    { path: '/gallery', icon: Image, label: '素材库' },
    { path: '/settings', icon: Settings, label: '设置' },
  ]

  return (
    <div className="flex h-screen bg-gray-50">
      <VersionUpdateModal isOpen={versionModalOpen} onClose={() => setVersionModalOpen(false)} />

      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? 'w-64' : 'w-0'
        } bg-white border-r border-gray-200 flex flex-col transition-all duration-300 overflow-hidden`}
      >
        {/* Logo */}
        <div className="p-4 border-b border-gray-200">
          <Link to="/" className="flex items-center gap-2 text-primary-600">
            <Sparkles className="w-8 h-8" />
            <span className="text-xl font-bold">LabCanvas</span>
          </Link>
          <p className="text-xs text-gray-500 mt-1">AI驱动的学术绘图工具</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path || 
              (item.path !== '/' && location.pathname.startsWith(item.path))
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`sidebar-item ${isActive ? 'active' : ''}`}
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </Link>
            )
          })}

          {/* Version update entry */}
          <button
            onClick={() => setVersionModalOpen(true)}
            className="sidebar-item w-full text-left mt-2"
          >
            <Rocket className="w-5 h-5" />
            <span>版本更新</span>
            <span className="ml-auto px-1.5 py-0.5 rounded text-[10px] font-bold bg-primary-100 text-primary-600">
              v1.2.0
            </span>
          </button>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 space-y-2">
          <button
            onClick={() => setVersionModalOpen(true)}
            className="flex items-center gap-2 text-xs text-gray-500 hover:text-primary-600 transition-colors w-full"
          >
            <Rocket className="w-3.5 h-3.5" />
            <span>LabCanvas v1.2.0</span>
          </button>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Palette className="w-4 h-4" />
            <span>Powered by 智谱AI</span>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-14 bg-white border-b border-gray-200 flex items-center px-4">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          
          <div className="ml-4 flex items-center gap-2 text-gray-600">
            <FolderOpen className="w-4 h-4" />
            <span className="text-sm">
              {location.pathname === '/' ? '首页' : 
               location.pathname.startsWith('/editor') ? '编辑器' :
               location.pathname === '/gallery' ? '素材库' :
               location.pathname === '/settings' ? '设置' : ''}
            </span>
          </div>
        </header>

        {/* Page content */}
        <div className="flex-1 overflow-auto">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
