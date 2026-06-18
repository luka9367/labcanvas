import { useEffect, useRef, forwardRef, useImperativeHandle, useState } from 'react'
import { Loader2, AlertCircle } from 'lucide-react'

interface DrawIOEditorProps {
  xml?: string | null
  imageUrl?: string | null
  isGenerating?: boolean
}

const DrawIOEditor = forwardRef<any, DrawIOEditorProps>(({ xml, imageUrl, isGenerating }, ref) => {
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const currentXmlRef = useRef<string>(xml || '')
  const [isEditorLoading, setIsEditorLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isReady, setIsReady] = useState(false)

  // Update currentXml when xml prop changes
  useEffect(() => {
    if (xml) {
      currentXmlRef.current = xml
      if (isReady) {
        loadXml(xml)
      }
    }
  }, [xml, isReady])

  // Load image if provided
  useEffect(() => {
    if (imageUrl) {
      // For image mode, we might want to display it differently
      // For now, we'll just keep it in the ref
    }
  }, [imageUrl])

  const loadXml = (xmlData: string) => {
    if (!iframeRef.current?.contentWindow) {
      console.warn('Iframe not ready, cannot load XML')
      return
    }
    
    if (!xmlData) {
      console.warn('No XML data to load')
      return
    }
    
    try {
      // Send message to draw.io to load XML
      iframeRef.current.contentWindow.postMessage(
        JSON.stringify({
          action: 'load',
          xml: xmlData,
          autosave: 1,
        }),
        '*'
      )
    } catch (e) {
      console.error('Error loading XML:', e)
      setError('加载图表失败')
    }
  }

  const getXml = () => {
    return new Promise<string>((resolve) => {
      if (!iframeRef.current?.contentWindow) {
        resolve(currentXmlRef.current)
        return
      }

      const handleMessage = (event: MessageEvent) => {
        if (event.data && typeof event.data === 'string') {
          try {
            const msg = JSON.parse(event.data)
            if (msg.event === 'export') {
              window.removeEventListener('message', handleMessage)
              resolve(msg.data || currentXmlRef.current)
            }
          } catch {
            // Ignore non-JSON messages
          }
        }
      }

      window.addEventListener('message', handleMessage)
      
      // Request export
      try {
        iframeRef.current.contentWindow.postMessage(
          JSON.stringify({
            action: 'export',
            format: 'xml',
          }),
          '*'
        )
      } catch (e) {
        console.error('Error requesting export:', e)
        window.removeEventListener('message', handleMessage)
        resolve(currentXmlRef.current)
      }

      // Timeout fallback
      setTimeout(() => {
        window.removeEventListener('message', handleMessage)
        resolve(currentXmlRef.current)
      }, 2000)
    })
  }

  // Expose methods to parent
  useImperativeHandle(ref, () => ({
    getXml: async () => {
      const xml = await getXml()
      currentXmlRef.current = xml
      return xml
    },
    loadXml,
  }))

  // Handle messages from draw.io
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data && typeof event.data === 'string') {
        try {
          const msg = JSON.parse(event.data)
          
          switch (msg.event) {
            case 'init':
              // Editor is ready, load initial XML if any
              setIsReady(true)
              setIsEditorLoading(false)
              if (currentXmlRef.current) {
                loadXml(currentXmlRef.current)
              }
              break
            case 'autosave':
              // Auto-save event
              if (msg.xml) {
                currentXmlRef.current = msg.xml
              }
              break
            case 'save':
              // Save event
              if (msg.xml) {
                currentXmlRef.current = msg.xml
              }
              break
            case 'export':
              // Export completed
              if (msg.data) {
                currentXmlRef.current = msg.data
              }
              break
            case 'error':
              console.error('Draw.io error:', msg)
              setError(msg.message || '编辑器错误')
              break
          }
        } catch {
          // Ignore non-JSON messages
        }
      }
    }

    window.addEventListener('message', handleMessage)
    return () => window.removeEventListener('message', handleMessage)
  }, [])

  // Handle iframe load error
  const handleIframeError = () => {
    setError('编辑器加载失败，请检查网络连接')
    setIsEditorLoading(false)
  }

  // Construct draw.io URL with parameters
  const drawioUrl = `https://embed.diagrams.net/?embed=1&proto=json&spin=1&libraries=1&ui=min`

  return (
    <div className="w-full h-full relative bg-gray-50">
      {/* Editor initialization loading - only shows when iframe is loading */}
      {isEditorLoading && !isGenerating && (
        <div className="absolute inset-0 flex flex-col items-center justify-center z-10">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600 mb-4" />
          <p className="text-gray-600">正在初始化编辑器...</p>
        </div>
      )}
      
      {/* Generation loading - only shows when generating */}
      {isGenerating && (
        <div className="absolute inset-0 bg-white/90 flex flex-col items-center justify-center z-20">
          <Loader2 className="w-10 h-10 animate-spin text-primary-600 mb-4" />
          <p className="text-gray-700 font-medium">正在生成图表...</p>
          <p className="text-gray-500 text-sm mt-2">请稍候，AI 正在为您创作</p>
        </div>
      )}
      
      {/* Error overlay */}
      {error && (
        <div className="absolute inset-0 bg-white flex flex-col items-center justify-center z-30">
          <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
          <p className="text-red-600 mb-2">加载失败</p>
          <p className="text-gray-500 text-sm">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            重试
          </button>
        </div>
      )}
      
      {/* Empty state - when no content and not generating */}
      {!isEditorLoading && !isGenerating && !xml && !imageUrl && !error && (
        <div className="absolute inset-0 flex flex-col items-center justify-center z-0">
          <div className="text-center">
            <div className="w-20 h-20 bg-gray-200 rounded-full flex items-center justify-center mb-4 mx-auto">
              <svg className="w-10 h-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">准备就绪</h3>
            <p className="text-gray-500 max-w-sm">
              在左侧输入您的需求，选择生成模式，然后点击"生成"按钮开始创作
            </p>
          </div>
        </div>
      )}
      
      {/* Image display mode */}
      {imageUrl && !xml && !isGenerating && (
        <div className="w-full h-full flex items-center justify-center bg-gray-50">
          <img 
            src={imageUrl} 
            alt="Generated" 
            className="max-w-full max-h-full object-contain shadow-lg rounded-lg"
            onError={() => setError('无法加载生成的图片')}
          />
        </div>
      )}
      
      {/* Draw.io editor iframe */}
      <iframe
        ref={iframeRef}
        src={drawioUrl}
        className={`drawio-iframe w-full h-full border-0 ${(isGenerating || (!xml && !imageUrl && !isEditorLoading)) ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}
        title="Draw.io Editor"
        sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-downloads"
        onError={handleIframeError}
      />
    </div>
  )
})

DrawIOEditor.displayName = 'DrawIOEditor'

export default DrawIOEditor
