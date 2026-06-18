import { useEffect, useState } from 'react'
import { Search, Image as ImageIcon, Folder, X, Copy, ExternalLink, ZoomIn } from 'lucide-react'
import { galleryApi, bioiconsApi } from '../services/api'
import type { GalleryImage, BioIcon } from '../types'
import { useNavigate } from 'react-router-dom'

export default function GalleryPage() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<'gallery' | 'icons'>('gallery')
  const [galleryImages, setGalleryImages] = useState<GalleryImage[]>([])
  const [bioIcons, setBioIcons] = useState<BioIcon[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [previewImage, setPreviewImage] = useState<GalleryImage | null>(null)

  useEffect(() => {
    loadGallery()
    loadBioIcons()
    loadCategories()
  }, [])

  const loadGallery = async () => {
    try {
      const response = await galleryApi.list()
      const images = Array.isArray(response) ? response : (response.images || [])
      setGalleryImages(images)
    } catch (error) {
      console.error('Failed to load gallery:', error)
    }
  }

  const loadBioIcons = async () => {
    try {
      const response = await bioiconsApi.list()
      if (response.success) {
        setBioIcons(response.icons)
      }
    } catch (error) {
      console.error('Failed to load bioicons:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadCategories = async () => {
    try {
      const response = await bioiconsApi.getCategories()
      if (response.success) {
        setCategories(response.categories)
      }
    } catch (error) {
      console.error('Failed to load categories:', error)
    }
  }

  const filteredIcons = bioIcons.filter(icon => {
    const matchesCategory = selectedCategory === 'all' || icon.category === selectedCategory
    const matchesSearch = !searchQuery ||
      icon.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      icon.category.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesCategory && matchesSearch
  })

  const handleIconClick = (icon: BioIcon) => {
    navigator.clipboard.writeText(window.location.origin + icon.url)
    alert(`图标 ${icon.name} 已复制到剪贴板`)
  }

  const handleCopyImageUrl = (image: GalleryImage, e: React.MouseEvent) => {
    e.stopPropagation()
    const url = (image as any).image_url || (image as any).url || ''
    navigator.clipboard.writeText(window.location.origin + url)
    alert(`图片链接已复制到剪贴板`)
  }

  const handleUseInCreation = (image: GalleryImage, e: React.MouseEvent) => {
    e.stopPropagation()
    const url = (image as any).image_url || (image as any).url || ''
    // Navigate to editor with selected reference image
    navigate('/editor', { state: { selectedReferenceImage: url, referenceImageName: image.name } })
  }

  const handleOpenPreview = (image: GalleryImage, e: React.MouseEvent) => {
    e.stopPropagation()
    setPreviewImage(image)
  }

  const getImageUrl = (image: GalleryImage) => {
    const raw = (image as any).image_url || (image as any).thumbnail_url || (image as any).url || ''
    return raw + (raw.includes('?') ? '&' : '?') + 'v=2'
  }

  return (
    <div className="p-6 h-full">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">素材库</h1>
        <p className="text-gray-600">浏览和使用可用的图标和图片素材</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 mb-6 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('gallery')}
          className={`pb-2 px-1 font-medium transition-colors ${
            activeTab === 'gallery'
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <div className="flex items-center gap-2">
            <ImageIcon className="w-4 h-4" />
            参考图片
          </div>
        </button>
        <button
          onClick={() => setActiveTab('icons')}
          className={`pb-2 px-1 font-medium transition-colors ${
            activeTab === 'icons'
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <div className="flex items-center gap-2">
            <Folder className="w-4 h-4" />
            SVG 图标
          </div>
        </button>
      </div>

      {/* Search and filters */}
      <div className="mb-6 flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={activeTab === 'gallery' ? '搜索图片...' : '搜索图标...'}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        {activeTab === 'icons' && (
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="all">全部分类</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        )}
      </div>

      {/* Content */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">
          加载中...
        </div>
      ) : activeTab === 'gallery' ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {galleryImages.length === 0 ? (
            <div className="col-span-full text-center py-12 text-gray-500">
              <ImageIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>暂无参考图片</p>
              <p className="text-sm">将图片放入 static/gallery 目录即可添加</p>
            </div>
          ) : (
            galleryImages.map((image) => (
              <div
                key={image.id}
                className="card overflow-hidden hover:shadow-md transition-shadow group relative"
              >
                <div className="aspect-square bg-gray-100 relative cursor-pointer"
                  onClick={(e) => handleOpenPreview(image, e)}
                >
                  <img
                    src={getImageUrl(image)}
                    alt={image.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                    onError={(e) => {
                      console.error('Failed to load image:', getImageUrl(image))
                      e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"%3E%3Crect width="100" height="100" fill="%23f3f4f6"/%3E%3Ctext x="50" y="50" text-anchor="middle" dy=".3em" fill="%239ca3af" font-size="12"%3E加载失败%3C/text%3E%3C/svg%3E'
                    }}
                  />
                  {/* Hover overlay with actions */}
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                    <button
                      onClick={(e) => handleOpenPreview(image, e)}
                      className="p-2 bg-white rounded-full hover:bg-gray-100 transition-colors"
                      title="预览"
                    >
                      <ZoomIn className="w-4 h-4 text-gray-700" />
                    </button>
                    <button
                      onClick={(e) => handleUseInCreation(image, e)}
                      className="p-2 bg-primary-600 rounded-full hover:bg-primary-700 transition-colors"
                      title="用于创作"
                    >
                      <ExternalLink className="w-4 h-4 text-white" />
                    </button>
                    <button
                      onClick={(e) => handleCopyImageUrl(image, e)}
                      className="p-2 bg-white rounded-full hover:bg-gray-100 transition-colors"
                      title="复制链接"
                    >
                      <Copy className="w-4 h-4 text-gray-700" />
                    </button>
                  </div>
                </div>
                <div className="p-3">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {image.name}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {(image as any).category || '参考图片'}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {filteredIcons.length === 0 ? (
            <div className="col-span-full text-center py-12 text-gray-500">
              <Folder className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>未找到图标</p>
            </div>
          ) : (
            filteredIcons.map((icon) => (
              <div
                key={icon.id}
                onClick={() => handleIconClick(icon)}
                className="card p-4 cursor-pointer hover:shadow-md transition-shadow group"
              >
                <div className="aspect-square flex items-center justify-center bg-gray-50 rounded-lg mb-2">
                  <img
                    src={icon.url}
                    alt={icon.name}
                    className="w-12 h-12 object-contain"
                  />
                </div>
                <p className="text-xs text-center text-gray-600 truncate">
                  {icon.name}
                </p>
                <p className="text-xs text-center text-gray-400">
                  {icon.category}
                </p>
              </div>
            ))
          )}
        </div>
      )}

      {/* Preview Modal */}
      {previewImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          onClick={() => setPreviewImage(null)}
        >
          <div
            className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold text-gray-900 truncate pr-4">
                {previewImage.name}
              </h3>
              <button
                onClick={() => setPreviewImage(null)}
                className="p-1 hover:bg-gray-100 rounded-full transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4 flex items-center justify-center bg-gray-50">
              <img
                src={getImageUrl(previewImage)}
                alt={previewImage.name}
                className="max-w-full max-h-[60vh] object-contain shadow-lg"
              />
            </div>
            <div className="p-4 border-t flex gap-3 justify-end">
              <button
                onClick={() => {
                  const url = (previewImage as any).image_url || (previewImage as any).url || ''
                  navigator.clipboard.writeText(window.location.origin + url)
                  alert('图片链接已复制到剪贴板')
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
              >
                <Copy className="w-4 h-4" />
                复制链接
              </button>
              <button
                onClick={() => {
                  const url = (previewImage as any).image_url || (previewImage as any).url || ''
                  navigate('/editor', { state: { selectedReferenceImage: url, referenceImageName: previewImage.name } })
                }}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2"
              >
                <ExternalLink className="w-4 h-4" />
                用于创作
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
