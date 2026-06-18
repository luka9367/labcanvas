import { useState, useEffect, useCallback } from 'react'
import { X, Upload, Image as ImageIcon, Trash2, Search, Loader2, AlertCircle, BookOpen } from 'lucide-react'
import { referencesApi, galleryApi } from '../services/api'

interface ReferenceImage {
  id: string
  name: string
  category: string
  thumbnail_url: string
  full_url: string
  created_at: string
  is_default?: boolean
  title?: string
  authors?: string[]
  year?: string
  conference?: string
  tags?: string[]
}

interface ReferenceGalleryProps {
  isOpen: boolean
  onClose: () => void
  onSelect: (imageUrl: string) => void
}

type TabType = 'gallery' | 'uploaded'

export default function ReferenceGallery({ isOpen, onClose, onSelect }: ReferenceGalleryProps) {
  const [activeTab, setActiveTab] = useState<TabType>('gallery')
  const [images, setImages] = useState<ReferenceImage[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)

  const loadGalleryImages = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      console.log('Loading gallery images...')
      const response = await galleryApi.list(selectedCategory || undefined)
      console.log('Gallery response:', response)
      
      // Transform gallery items to ReferenceImage format
      // Add cache-bust query param to force browser reload after image update
      const cacheBust = '?v=2'
      const transformedImages = response.map((item: any) => ({
        id: item.id,
        name: item.name || item.title,
        title: item.title,
        category: item.category,
        thumbnail_url: item.thumbnail_url + cacheBust,
        full_url: item.image_url + cacheBust,
        created_at: '',
        is_default: true,
        authors: item.authors,
        year: item.year,
        conference: item.conference,
        tags: item.tags,
      }))
      
      setImages(transformedImages)
    } catch (error) {
      console.error('Failed to load gallery images:', error)
      setError(error instanceof Error ? error.message : '加载失败')
    } finally {
      setIsLoading(false)
    }
  }, [selectedCategory])

  const loadUploadedImages = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      console.log('Loading uploaded images...')
      const response = await referencesApi.list(selectedCategory || undefined)
      console.log('References response:', response)
      if (response.success) {
        setImages(response.images || [])
        setCategories(response.categories || [])
      } else {
        setError('加载失败：服务器返回错误')
      }
    } catch (error) {
      console.error('Failed to load uploaded images:', error)
      setError(error instanceof Error ? error.message : '加载失败')
    } finally {
      setIsLoading(false)
    }
  }, [selectedCategory])

  const loadCategories = useCallback(async () => {
    try {
      if (activeTab === 'gallery') {
        const cats = await galleryApi.getCategories()
        setCategories(cats)
      } else {
        const response = await referencesApi.getCategories()
        if (response.success) {
          setCategories(response.categories)
        }
      }
    } catch (error) {
      console.error('Failed to load categories:', error)
    }
  }, [activeTab])

  useEffect(() => {
    if (isOpen) {
      loadCategories()
      if (activeTab === 'gallery') {
        loadGalleryImages()
      } else {
        loadUploadedImages()
      }
    }
  }, [isOpen, activeTab, selectedCategory, loadGalleryImages, loadUploadedImages, loadCategories])

  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) {
      loadGalleryImages()
      return
    }
    
    setIsLoading(true)
    setError(null)
    try {
      console.log('Searching gallery...')
      const response = await galleryApi.search(searchQuery, 20)
      console.log('Search response:', response)
      
      const cacheBust = '?v=2'
      const transformedImages = response.map((item: any) => ({
        id: item.id,
        name: item.name || item.title,
        title: item.title,
        category: item.category,
        thumbnail_url: item.thumbnail_url + cacheBust,
        full_url: item.image_url + cacheBust,
        created_at: '',
        is_default: true,
        authors: item.authors,
        year: item.year,
        conference: item.conference,
        tags: item.tags,
      }))
      
      setImages(transformedImages)
    } catch (error) {
      console.error('Failed to search gallery:', error)
      setError(error instanceof Error ? error.message : '搜索失败')
    } finally {
      setIsLoading(false)
    }
  }, [searchQuery, loadGalleryImages])

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (activeTab === 'gallery' && searchQuery) {
        handleSearch()
      }
    }, 500)
    return () => clearTimeout(timeoutId)
  }, [searchQuery, activeTab, handleSearch])

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.type.startsWith('image/')) {
      setUploadError('请选择图片文件')
      return
    }

    if (file.size > 10 * 1024 * 1024) {
      setUploadError('图片大小不能超过 10MB')
      return
    }

    setIsUploading(true)
    setUploadError(null)

    try {
      console.log('Uploading file:', file.name)
      const response = await referencesApi.upload(file, file.name.replace(/\.[^/.]+$/, ''), 'custom')
      console.log('Upload response:', response)
      if (response.success) {
        setActiveTab('uploaded')
        await loadUploadedImages()
      } else {
        setUploadError(response.message || '上传失败')
      }
    } catch (error) {
      console.error('Failed to upload image:', error)
      setUploadError(error instanceof Error ? error.message : '上传失败')
    } finally {
      setIsUploading(false)
      e.target.value = ''
    }
  }

  const handleDelete = async (id: string, isDefault?: boolean) => {
    if (isDefault) {
      alert('官方参考图片不能删除')
      return
    }
    if (!confirm('确定要删除这张图片吗？')) return

    try {
      await referencesApi.delete(id)
      await loadUploadedImages()
    } catch (error) {
      console.error('Failed to delete image:', error)
      alert('删除失败：' + (error instanceof Error ? error.message : '未知错误'))
    }
  }

  const filteredImages = activeTab === 'uploaded' && !searchQuery
    ? images.filter(img => img.name.toLowerCase().includes(searchQuery.toLowerCase()))
    : images

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-5xl max-h-[85vh] flex flex-col m-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-semibold text-gray-900">参考图片素材库</h2>
            {/* Tabs */}
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setActiveTab('gallery')}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'gallery'
                    ? 'bg-white text-primary-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <span className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4" />
                  官方图库
                </span>
              </button>
              <button
                onClick={() => setActiveTab('uploaded')}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'uploaded'
                    ? 'bg-white text-primary-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <span className="flex items-center gap-2">
                  <ImageIcon className="w-4 h-4" />
                  我的上传
                </span>
              </button>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Toolbar */}
        <div className="flex items-center gap-4 px-6 py-3 border-b bg-gray-50">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={activeTab === 'gallery' ? "搜索论文、作者、标签..." : "搜索图片..."}
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {/* Category filter */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">所有分类</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>

          {/* Upload button - only show in uploaded tab */}
          {activeTab === 'uploaded' && (
            <label className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 cursor-pointer transition-colors disabled:opacity-50">
              <Upload className="w-4 h-4" />
              <span>{isUploading ? '上传中...' : '上传'}</span>
              <input
                type="file"
                accept="image/*"
                onChange={handleFileUpload}
                className="hidden"
                disabled={isUploading}
              />
            </label>
          )}
        </div>

        {/* Error messages */}
        {(error || uploadError) && (
          <div className="px-6 py-2 bg-red-50 border-b">
            <div className="flex items-center gap-2 text-red-600 text-sm">
              <AlertCircle className="w-4 h-4" />
              <span>{error || uploadError}</span>
            </div>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary-600 mb-4" />
              <p className="text-gray-500">加载中...</p>
            </div>
          ) : filteredImages.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-400">
              <ImageIcon className="w-12 h-12 mb-4" />
              <p>暂无图片</p>
              {activeTab === 'uploaded' ? (
                <p className="text-sm mt-1">点击上方上传按钮添加参考图片</p>
              ) : (
                <p className="text-sm mt-1">尝试其他搜索关键词</p>
              )}
              {error && (
                <button
                  onClick={activeTab === 'gallery' ? loadGalleryImages : loadUploadedImages}
                  className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                >
                  重试
                </button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {filteredImages.map((image) => (
                <div
                  key={image.id}
                  className="group relative aspect-[4/3] rounded-lg overflow-hidden border hover:border-primary-500 transition-colors cursor-pointer bg-gray-100"
                  onClick={() => onSelect(image.full_url)}
                >
                  <img
                    src={image.thumbnail_url}
                    alt={image.name}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      console.error('Failed to load image:', image.thumbnail_url)
                      e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"%3E%3Crect width="100" height="100" fill="%23f3f4f6"/%3E%3Ctext x="50" y="50" text-anchor="middle" dy=".3em" fill="%239ca3af" font-size="12"%3E加载失败%3C/text%3E%3C/svg%3E'
                    }}
                  />
                  
                  {/* Overlay */}
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
                    <span className="text-white text-sm font-medium">选择</span>
                  </div>
                  
                  {/* Delete button - only for uploaded images */}
                  {activeTab === 'uploaded' && !image.is_default && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDelete(image.id, image.is_default)
                      }}
                      className="absolute top-2 right-2 p-1.5 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  )}
                  
                  {/* Info overlay for gallery items */}
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-3">
                    <p className="text-white text-xs font-medium line-clamp-2">{image.name}</p>
                    {image.year && image.conference && (
                      <p className="text-white/70 text-xs mt-1">{image.year} · {image.conference}</p>
                    )}
                    {image.tags && image.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1">
                        {image.tags.slice(0, 3).map((tag, idx) => (
                          <span key={idx} className="text-[10px] px-1.5 py-0.5 bg-white/20 text-white rounded">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t bg-gray-50 text-sm text-gray-500 flex justify-between">
          <span>共 {filteredImages.length} 张图片</span>
          {activeTab === 'gallery' && <span>官方图库 · 256 张学术论文插图</span>}
        </div>
      </div>
    </div>
  )
}
