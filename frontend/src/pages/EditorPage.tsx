import { useState, useRef, useEffect } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import {
  Send,
  Image as ImageIcon,
  Wand2,
  FileCode,
  Puzzle,
  Download,
  Save,
  Loader2,
  Upload,
  Library,
  CheckCircle2,
  XCircle,
  Circle,
  Ban,
} from 'lucide-react'
import { generateApi, projectsApi } from '../services/api'
import { useApp } from '../contexts/AppContext'
import type { GenerationMode, GenerationStep } from '../types'
import DrawIOEditor from '../components/DrawIOEditor'
import ReferenceGallery from '../components/ReferenceGallery'

export default function EditorPage() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const {
    isGenerating,
    setIsGenerating,
    generationProgress,
    setGenerationProgress,
    generationSteps,
    setGenerationSteps,
    abortController,
    setAbortController,
    generationMode,
    setGenerationMode,
  } = useApp()

  const [prompt, setPrompt] = useState('')
  const [referenceImage, setReferenceImage] = useState<string | null>(null)
  const [generatedXml, setGeneratedXml] = useState<string | null>(null)
  const [generatedImage, setGeneratedImage] = useState<string | null>(null)
  const [projectName, setProjectName] = useState('未命名项目')
  const [isGalleryOpen, setIsGalleryOpen] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const editorRef = useRef<any>(null)

  // Load project if editing existing
  useEffect(() => {
    if (projectId) {
      projectsApi.get(projectId).then(response => {
        if (response.success && response.project) {
          setProjectName(response.project.name)
          if (response.project.diagram_data?.xml) {
            setGeneratedXml(response.project.diagram_data.xml)
          }
        }
      })
    }
  }, [projectId])

  // Handle reference image passed from GalleryPage
  useEffect(() => {
    const state = location.state as { selectedReferenceImage?: string; referenceImageName?: string } | null
    if (state?.selectedReferenceImage) {
      setReferenceImage(state.selectedReferenceImage)
      // Clear state after reading to avoid re-applying on refresh
      navigate(location.pathname, { replace: true, state: {} })
    }
  }, [location.state, location.pathname, navigate])

  const modes: { id: GenerationMode; label: string; icon: any; description: string }[] = [
    { 
      id: 'auto', 
      label: '自动', 
      icon: Wand2,
      description: 'AI自动选择最佳生成方式'
    },
    { 
      id: 'draft', 
      label: '草稿', 
      icon: FileCode,
      description: '生成可编辑的流程图草图'
    },
    { 
      id: 'generate', 
      label: '生成', 
      icon: ImageIcon,
      description: '直接生成高保真图像'
    },
    { 
      id: 'assembly', 
      label: '组装', 
      icon: Puzzle,
      description: '结构化组装高质量图表'
    },
  ]

  // Step definitions for each generation mode
  const MODE_STEPS: Record<string, { id: string; label: string }[]> = {
    auto: [
      { id: 'analyzing', label: '分析需求并选择最佳生成模式' },
      { id: 'mode_selected', label: '确认生成模式' },
    ],
    draft: [
      { id: 'analyzing', label: '分析需求' },
      { id: 'plan', label: '生成结构计划' },
      { id: 'xml', label: '生成 draw.io XML 流程图' },
      { id: 'complete', label: '完成生成' },
    ],
    generate: [
      { id: 'planning', label: '分析需求并优化提示词' },
      { id: 'generating', label: '生成高保真图像' },
      { id: 'enhancing', label: '图像后处理增强' },
      { id: 'quality_check', label: '光影质量校验' },
      { id: 'complete', label: '完成生成' },
    ],
    assembly: [
      { id: 'analyzing', label: '分析需求' },
      { id: 'plan', label: '生成设计方案' },
      { id: 'image', label: '生成概念预览图' },
      { id: 'blueprint', label: '创建结构蓝图' },
      { id: 'components', label: '生成组件元素' },
      { id: 'assembly', label: '组装最终图表' },
      { id: 'complete', label: '完成生成' },
    ],
  }

  const initializeSteps = (mode: GenerationMode): GenerationStep[] => {
    const defs = MODE_STEPS[mode] || MODE_STEPS.auto
    return defs.map((s, i) => ({
      id: s.id,
      label: s.label,
      status: (i === 0 ? 'running' : 'pending') as GenerationStep['status'],
      message: i === 0 ? '正在处理...' : undefined,
    }))
  }

  const updateStepStatus = (
    steps: GenerationStep[],
    stepId: string,
    status: GenerationStep['status'],
    message?: string
  ): GenerationStep[] => {
    let found = false
    const updated = steps.map((s) => {
      if (s.id === stepId) {
        found = true
        return { ...s, status, message: message || s.message }
      }
      return s
    })
    // If step not found, append it
    if (!found) {
      updated.push({ id: stepId, label: message || stepId, status, message })
    }
    return updated
  }

  const parseSSEStream = async (
    reader: ReadableStreamDefaultReader<Uint8Array>,
    onChunk: (data: any) => void
  ) => {
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        const trimmed = line.trim()
        if (trimmed.startsWith('data:')) {
          const jsonStr = trimmed.slice(5).trim()
          if (jsonStr === '[DONE]') continue
          try {
            const data = JSON.parse(jsonStr)
            onChunk(data)
          } catch {
            // ignore malformed json
          }
        }
      }
    }
  }

  const handleGenerate = async () => {
    if (!prompt.trim() || isGenerating) return

    setIsGenerating(true)
    setGenerationProgress('正在分析需求...')
    setGeneratedXml(null)
    setGeneratedImage(null)

    const steps = initializeSteps(generationMode)
    setGenerationSteps(steps)

    const controller = new AbortController()
    setAbortController(controller)

    let currentSteps = steps
    let finalData: any = null
    let hasError = false

    try {
      const response = await generateApi.generateStream(
        {
          prompt: prompt.trim(),
          mode: generationMode,
          reference_image: referenceImage || undefined,
          language: 'zh',
        },
        controller.signal
      )

      if (!response.ok || !response.body) {
        throw new Error(`请求失败: ${response.status}`)
      }

      await parseSSEStream(response.body.getReader(), (data) => {
        // Update steps based on step id or name
        const stepId = data.step ?? data.name ?? ''
        const message = data.message || data.detail || ''

        if (stepId) {
          // Auto mode: when mode is selected, append sub-mode steps
          if (String(stepId) === 'mode_selected' && data.mode && data.mode !== 'auto') {
            currentSteps = updateStepStatus(currentSteps, 'mode_selected', 'complete', message)
            const subDefs = MODE_STEPS[data.mode]
            if (subDefs) {
              const subSteps = subDefs.slice(1).map((s, i) => ({
                id: s.id,
                label: s.label,
                status: (i === 0 ? 'running' : 'pending') as GenerationStep['status'],
                message: i === 0 ? message || '正在处理...' : undefined,
              }))
              currentSteps = [...currentSteps, ...subSteps]
            }
            setGenerationSteps([...currentSteps])
          } else if (String(stepId) === 'quality_report') {
            // 光影质量校验报告 - 直接标记为完成并展示分数
            const score = data.score ?? 0
            const passed = data.passed ?? false
            const detail = `总分 ${score} 分${passed ? '，已通过' : '，未达标'}`
            currentSteps = updateStepStatus(currentSteps, 'quality_check', 'complete', detail)
            currentSteps = updateStepStatus(currentSteps, String(stepId), 'complete', detail)
            setGenerationSteps([...currentSteps])
          } else if (String(stepId).startsWith('iteration')) {
            // 迭代优化步骤
            const round = data.round ?? 1
            const iterLabel = `第 ${round} 轮迭代优化`
            currentSteps = updateStepStatus(currentSteps, String(stepId), 'running', iterLabel)
            setGenerationSteps([...currentSteps])
          } else if (data.status === 'complete') {
            currentSteps = updateStepStatus(currentSteps, String(stepId), 'complete', message)
            setGenerationSteps([...currentSteps])
          } else if (data.status === 'error' || data.step === 'error') {
            hasError = true
            currentSteps = updateStepStatus(currentSteps, String(stepId), 'error', message || '处理出错')
            setGenerationSteps([...currentSteps])
          } else {
            currentSteps = updateStepStatus(currentSteps, String(stepId), 'running', message)
            setGenerationSteps([...currentSteps])
          }
        }

        if (data.step === 'complete' || data.step === 'finished') {
          finalData = data
        }

        // Update legacy progress text for compatibility
        if (message) {
          setGenerationProgress(message)
        }
      })

      if (hasError) {
        setGenerationProgress(currentSteps.find((s) => s.status === 'error')?.message || '生成失败')
      } else {
        // Mark all pending/running steps as complete
        currentSteps = currentSteps.map((s) =>
          s.status === 'pending' || s.status === 'running' ? { ...s, status: 'complete' as const } : s
        )
        setGenerationSteps([...currentSteps])
        setGenerationProgress('生成完成！')
      }

      if (finalData?.xml) {
        setGeneratedXml(finalData.xml)
      }
      if (finalData?.image_url) {
        setGeneratedImage(finalData.image_url)
      }
      // Also check nested data for assembly/generate modes
      if (finalData?.data?.xml) {
        setGeneratedXml(finalData.data.xml)
      }
      if (finalData?.data?.image_url) {
        setGeneratedImage(finalData.data.image_url)
      }
    } catch (error) {
      if ((error as Error).name === 'AbortError') {
        setGenerationProgress('生成已取消')
        setGenerationSteps(
          currentSteps.map((s) => (s.status === 'running' ? { ...s, status: 'error' as const, message: '已取消' } : s))
        )
      } else {
        setGenerationProgress(error instanceof Error ? error.message : '生成失败')
        setGenerationSteps(
          currentSteps.map((s) => (s.status === 'running' ? { ...s, status: 'error' as const, message: error instanceof Error ? error.message : '失败' } : s))
        )
      }
    } finally {
      setIsGenerating(false)
      setAbortController(null)
    }
  }

  const handleStopGenerate = () => {
    if (abortController) {
      abortController.abort()
    }
    setIsGenerating(false)
    setGenerationProgress('生成已停止')
    setAbortController(null)
  }

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (event) => {
        const base64 = event.target?.result as string
        // Remove data URL prefix
        const base64Data = base64.split(',')[1]
        setReferenceImage(base64Data)
      }
      reader.readAsDataURL(file)
    }
  }

  const downloadFile = (dataUrlOrBlob: string | Blob, filename: string) => {
    const url = typeof dataUrlOrBlob === 'string' ? dataUrlOrBlob : URL.createObjectURL(dataUrlOrBlob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.style.display = 'none'
    document.body.appendChild(a)
    a.click()
    setTimeout(() => {
      document.body.removeChild(a)
      if (typeof dataUrlOrBlob !== 'string') {
        URL.revokeObjectURL(url)
      }
    }, 100)
  }

  const exportFromDrawio = (format: 'png' | 'svg'): Promise<string> => {
    return new Promise((resolve, reject) => {
      if (!editorRef.current?.contentWindow) {
        reject(new Error('编辑器未加载'))
        return
      }

      const handleMessage = (event: MessageEvent) => {
        if (event.data && typeof event.data === 'string') {
          try {
            const msg = JSON.parse(event.data)
            if (msg.event === 'export') {
              window.removeEventListener('message', handleMessage)
              if (msg.data) {
                resolve(msg.data)
              } else {
                reject(new Error('导出数据为空'))
              }
            }
          } catch {
            // Ignore non-JSON messages
          }
        }
      }

      window.addEventListener('message', handleMessage)

      try {
        editorRef.current.contentWindow.postMessage(
          JSON.stringify({
            action: 'export',
            format,
            border: 10,
            crop: true,
            shadow: true,
          }),
          '*'
        )
      } catch (e) {
        window.removeEventListener('message', handleMessage)
        reject(e)
      }

      setTimeout(() => {
        window.removeEventListener('message', handleMessage)
        reject(new Error('导出超时'))
      }, 15000)
    })
  }

  const handleSave = async () => {
    // 优先保存生成的图片到本地相册/下载目录
    if (generatedImage) {
      downloadFile(generatedImage, `${projectName}.png`)
      return
    }

    // 如果没有图片，尝试从 draw.io 导出 PNG
    try {
      const dataUrl = await exportFromDrawio('png')
      downloadFile(dataUrl, `${projectName}.png`)
    } catch (error) {
      alert('保存失败：' + (error instanceof Error ? error.message : '编辑器未就绪，请等待加载完成'))
    }
  }

  const handleExport = async (format: 'png' | 'svg' | 'xml') => {
    const xml = editorRef.current?.getXml?.() || generatedXml
    if (!xml) {
      alert('暂无内容可导出')
      return
    }

    if (format === 'xml') {
      const blob = new Blob([xml], { type: 'application/xml' })
      downloadFile(blob, `${projectName}.drawio`)
      return
    }

    try {
      const dataUrl = await exportFromDrawio(format)
      downloadFile(dataUrl, `${projectName}.${format}`)
    } catch (error) {
      alert('导出失败：' + (error instanceof Error ? error.message : '编辑器未就绪，请等待加载完成'))
    }
  }

  return (
    <div className="flex flex-col md:flex-row md:h-full min-h-full">
      {/* Input panel: mobile scrollable, desktop left sidebar */}
      <div className="md:h-full md:w-80 lg:w-96 bg-white border-b md:border-b-0 md:border-r border-gray-200 flex flex-col shrink-0">
        {/* Header */}
        <div className="p-3 md:p-4 border-b border-gray-200 shrink-0">
          <input
            type="text"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            className="text-base md:text-lg font-semibold text-gray-900 bg-transparent border-none focus:outline-none focus:ring-0 w-full"
            placeholder="项目名称"
          />
        </div>

        {/* Mode selector */}
        <div className="p-3 md:p-4 border-b border-gray-200 shrink-0">
          <label className="text-sm font-medium text-gray-700 mb-2 block">
            生成模式
          </label>
          <div className="grid grid-cols-2 gap-2">
            {modes.map((mode) => {
              const Icon = mode.icon
              return (
                <button
                  key={mode.id}
                  onClick={() => setGenerationMode(mode.id)}
                  className={`p-2 md:p-3 rounded-lg border text-left transition-colors ${
                    generationMode === mode.id
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  title={mode.description}
                >
                  <Icon className="w-4 h-4 mb-1" />
                  <span className="text-xs md:text-sm font-medium">{mode.label}</span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Prompt area */}
        <div className="flex-1 md:flex-1 md:min-h-0 md:overflow-y-auto p-3 md:p-4">
          <label className="text-sm font-medium text-gray-700 mb-2 block">
            描述您的需求
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="例如：生成一个机器学习训练流程图，包含数据预处理、模型训练、评估和部署四个阶段..."
            className="w-full h-36 md:h-40 p-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm md:text-base"
          />

          {/* Reference image */}
          <div className="mt-3 md:mt-4">
            <label className="text-sm font-medium text-gray-700 mb-2 block">
              参考图片（可选）
            </label>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImageUpload}
              accept="image/*"
              className="hidden"
            />
            {referenceImage ? (
              <div className="relative">
                <img
                  src={`data:image/png;base64,${referenceImage}`}
                  alt="Reference"
                  className="w-full h-24 md:h-32 object-cover rounded-lg"
                />
                <button
                  onClick={() => setReferenceImage(null)}
                  className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600"
                >
                  ×
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="h-14 md:h-20 border-2 border-dashed border-gray-300 rounded-lg flex flex-col items-center justify-center text-gray-500 hover:border-primary-500 hover:text-primary-600 transition-colors"
                >
                  <Upload className="w-4 h-4 md:w-5 md:h-5 mb-0.5 md:mb-1" />
                  <span className="text-xs md:text-sm">上传</span>
                </button>
                <button
                  onClick={() => setIsGalleryOpen(true)}
                  className="h-14 md:h-20 border border-gray-300 rounded-lg flex flex-col items-center justify-center gap-1 text-gray-600 hover:border-primary-500 hover:text-primary-600 transition-colors"
                >
                  <Library className="w-4 h-4 md:w-5 md:h-5" />
                  <span className="text-xs md:text-sm">素材库</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Generate button & Progress */}
        <div className="p-3 md:p-4 border-t border-gray-200 shrink-0">
          {/* Visual task list */}
          {isGenerating && generationSteps.length > 0 && (
            <div className="mb-3 bg-gray-50 rounded-lg p-2 border border-gray-200">
              <div className="text-xs font-medium text-gray-500 mb-1.5 uppercase tracking-wide">
                处理进度
              </div>
              <div className="space-y-1 max-h-20 md:max-h-36 overflow-y-auto">
                {generationSteps.map((step, idx) => {
                  const statusIcon =
                    step.status === 'complete' ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-green-500 shrink-0 mt-0.5" />
                    ) : step.status === 'error' ? (
                      <XCircle className="w-3.5 h-3.5 text-red-500 shrink-0 mt-0.5" />
                    ) : step.status === 'running' ? (
                      <Loader2 className="w-3.5 h-3.5 text-primary-600 animate-spin shrink-0 mt-0.5" />
                    ) : (
                      <Circle className="w-3.5 h-3.5 text-gray-300 shrink-0 mt-0.5" />
                    )
                  const statusClass =
                    step.status === 'complete'
                      ? 'text-gray-700'
                      : step.status === 'error'
                      ? 'text-red-600'
                      : step.status === 'running'
                      ? 'text-primary-700 font-medium'
                      : 'text-gray-400'
                  return (
                    <div key={step.id + idx} className="flex items-start gap-1.5">
                      {statusIcon}
                      <div className="flex-1 min-w-0">
                        <div className={`text-xs leading-5 ${statusClass}`}>{step.label}</div>
                        {step.message && step.status === 'running' && (
                          <div className="text-[11px] text-gray-500 truncate">{step.message}</div>
                        )}
                        {step.status === 'error' && step.message && (
                          <div className="text-[11px] text-red-500">{step.message}</div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Legacy progress text for non-stream fallback */}
          {!isGenerating && generationProgress && (
            <div className="mb-3 text-sm text-gray-600">
              {generationProgress}
            </div>
          )}

          <div className="flex gap-2">
            <button
              onClick={handleGenerate}
              disabled={!prompt.trim() || isGenerating}
              className="flex-1 btn-primary flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  生成中...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  生成
                </>
              )}
            </button>
            {isGenerating && (
              <button
                onClick={handleStopGenerate}
                className="px-3 md:px-4 btn-secondary flex items-center gap-1 md:gap-2 text-red-600 border-red-200 hover:bg-red-50 hover:border-red-300"
                title="停止生成并退出任务"
              >
                <Ban className="w-4 h-4" />
                <span className="hidden sm:inline">停止</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Canvas area: mobile fixed height, desktop right side */}
      <div className="h-[60vh] md:h-full md:flex-1 flex flex-col bg-gray-100 min-h-0">
        {/* Toolbar */}
        <div className="h-12 bg-white border-b border-gray-200 flex items-center justify-between px-3 md:px-4 shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">编辑器</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleSave}
              className="btn-secondary flex items-center gap-1 md:gap-2 text-xs md:text-sm px-2 md:px-3"
            >
              <Save className="w-4 h-4" />
              <span className="hidden sm:inline">保存</span>
            </button>
            <div className="relative group">
              <button className="btn-primary flex items-center gap-1 md:gap-2 text-xs md:text-sm px-2 md:px-3">
                <Download className="w-4 h-4" />
                <span className="hidden sm:inline">导出</span>
              </button>
              <div className="absolute right-0 top-full mt-1 w-28 md:w-32 bg-white rounded-lg shadow-lg border border-gray-200 hidden group-hover:block z-10">
                <button
                  onClick={() => handleExport('xml')}
                  className="w-full px-3 md:px-4 py-2 text-left text-xs md:text-sm hover:bg-gray-50 first:rounded-t-lg"
                >
                  导出 XML
                </button>
                <button
                  onClick={() => handleExport('png')}
                  className="w-full px-3 md:px-4 py-2 text-left text-xs md:text-sm hover:bg-gray-50"
                >
                  导出 PNG
                </button>
                <button
                  onClick={() => handleExport('svg')}
                  className="w-full px-3 md:px-4 py-2 text-left text-xs md:text-sm hover:bg-gray-50 last:rounded-b-lg"
                >
                  导出 SVG
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Editor */}
        <div className="flex-1 overflow-hidden">
          <DrawIOEditor
            ref={editorRef}
            xml={generatedXml}
            imageUrl={generatedImage}
            isGenerating={isGenerating}
          />
        </div>
      </div>

      {/* Reference Gallery Modal */}
      <ReferenceGallery
        isOpen={isGalleryOpen}
        onClose={() => setIsGalleryOpen(false)}
        onSelect={(imageUrl) => {
          // Fetch image and convert to base64
          fetch(imageUrl)
            .then(res => res.blob())
            .then(blob => {
              const reader = new FileReader()
              reader.onloadend = () => {
                const base64 = (reader.result as string).split(',')[1]
                setReferenceImage(base64)
                setIsGalleryOpen(false)
              }
              reader.readAsDataURL(blob)
            })
            .catch(err => {
              console.error('Failed to load image:', err)
              alert('加载图片失败')
            })
        }}
      />
    </div>
  )
}
