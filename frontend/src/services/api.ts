const API_BASE = '/api/v1'

const DEFAULT_TIMEOUT = 30000 // 30 seconds
const MAX_RETRIES = 2
const RETRY_DELAY = 1000 // 1 second

async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

async function fetchWithTimeout(
  url: string,
  options?: RequestInit & { timeout?: number }
): Promise<Response> {
  const timeout = options?.timeout || DEFAULT_TIMEOUT
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    })
    return response
  } finally {
    clearTimeout(timeoutId)
  }
}

async function fetchApi(url: string, options?: RequestInit & { timeout?: number; retries?: number }) {
  const isFormData = options?.body instanceof FormData
  const retries = options?.retries ?? MAX_RETRIES
  let lastError: Error | null = null

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetchWithTimeout(`${API_BASE}${url}`, {
        ...options,
        headers: isFormData
          ? options?.headers
          : {
              'Content-Type': 'application/json',
              ...options?.headers,
            },
      })

      if (!response.ok) {
        // Handle network-level errors with retry
        if (response.status >= 500 && attempt < retries) {
          const errorData = await response.json().catch(() => ({ message: `HTTP ${response.status}` }))
          lastError = new Error(errorData.message || `HTTP ${response.status}`)
          await sleep(RETRY_DELAY * (attempt + 1))
          continue
        }
        const error = await response.json().catch(() => ({ message: 'Unknown error' }))
        throw new Error(error.message || `HTTP ${response.status}`)
      }

      return response.json()
    } catch (error) {
      // Handle abort/timeout errors
      if (error instanceof DOMException && error.name === 'AbortError') {
        lastError = new Error('请求超时，请检查网络连接')
      } else if (error instanceof TypeError && error.message.includes('fetch')) {
        lastError = new Error('网络连接失败，请检查后端服务是否运行')
      } else {
        lastError = error instanceof Error ? error : new Error(String(error))
      }

      // Retry on network errors
      if (attempt < retries && (
        lastError.message.includes('超时') ||
        lastError.message.includes('网络') ||
        lastError.message.includes('服务暂时不可用')
      )) {
        await sleep(RETRY_DELAY * (attempt + 1))
        continue
      }

      throw lastError
    }
  }

  throw lastError || new Error('请求失败')
}

// Settings API
export const settingsApi = {
  get: () => fetchApi('/settings', { timeout: 10000 }),
  update: (data: Partial<Settings>) => fetchApi('/settings', {
    method: 'POST',
    body: JSON.stringify(data),
    timeout: 15000,
  }),
  getModels: () => fetchApi('/settings/models', { timeout: 10000 }),
}

// Generate API
export const generateApi = {
  generate: (data: GenerateRequest) => fetchApi('/generate', {
    method: 'POST',
    body: JSON.stringify(data),
    timeout: 300000, // 5 minutes for generation
  }),
  generateStream: (data: GenerateRequest, signal?: AbortSignal) => {
    return fetch(`${API_BASE}/generate/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      signal,
    })
  },
}

// Projects API
export const projectsApi = {
  list: () => fetchApi('/projects', { timeout: 10000 }),
  get: (id: string) => fetchApi(`/projects/${id}`, { timeout: 10000 }),
  create: (data: { name: string; description?: string }) => fetchApi('/projects', {
    method: 'POST',
    body: JSON.stringify(data),
    timeout: 15000,
  }),
  update: (id: string, data: any) => fetchApi(`/projects/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
    timeout: 15000,
  }),
  delete: (id: string) => fetchApi(`/projects/${id}`, {
    method: 'DELETE',
    timeout: 15000,
  }),
}

// BioIcons API
export const bioiconsApi = {
  list: (params?: { category?: string; search?: string }) => {
    const query = new URLSearchParams(params as Record<string, string>).toString()
    return fetchApi(`/bioicons?${query}`, { timeout: 10000 })
  },
  getCategories: () => fetchApi('/bioicons/categories', { timeout: 10000 }),
  get: (id: string) => fetchApi(`/bioicons/${id}`, { timeout: 10000 }),
}

// Assistant API
export const assistantApi = {
  chat: (messages: ChatMessage[], stream = false) => fetchApi('/assistant/chat', {
    method: 'POST',
    body: JSON.stringify({ messages, stream }),
    timeout: 60000,
  }),
  executeCommand: (command: string, canvasState?: any) => fetchApi('/assistant/canvas-command', {
    method: 'POST',
    body: JSON.stringify({ command, canvas_state: canvasState }),
    timeout: 60000,
  }),
}

// Elements API
export const elementsApi = {
  generate: (data: { prompt: string; element_type: string; size?: string; style?: string }) =>
    fetchApi('/elements/generate', {
      method: 'POST',
      body: JSON.stringify(data),
      timeout: 120000,
    }),
}

// Models API
export const modelsApi = {
  list: () => fetchApi('/models', { timeout: 10000 }),
  getProviders: () => fetchApi('/models/providers', { timeout: 10000 }),
}

// References API (for user-uploaded reference images)
export const referencesApi = {
  list: (category?: string) => {
    const query = category ? `?category=${encodeURIComponent(category)}` : ''
    return fetchApi(`/references${query}`, { timeout: 10000 })
  },
  upload: (file: File, name: string, category: string) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('name', name)
    formData.append('category', category)
    return fetchApi('/references/upload', {
      method: 'POST',
      body: formData,
      timeout: 60000,
    })
  },
  delete: (id: string) => fetchApi(`/references/${id}`, { method: 'DELETE', timeout: 15000 }),
  getCategories: () => fetchApi('/references/categories', { timeout: 10000 }),
}

// Gallery API (for official style reference images)
export const galleryApi = {
  list: (category?: string) => {
    const query = category ? `?category=${encodeURIComponent(category)}` : ''
    return fetchApi(`/gallery${query}`, { timeout: 10000 })
  },
  search: (q: string, top_k: number = 10) => fetchApi(`/gallery/search?q=${encodeURIComponent(q)}&top_k=${top_k}`, { timeout: 10000 }),
  getById: (id: string) => fetchApi(`/gallery/${id}`, { timeout: 10000 }),
  getCategories: () => fetchApi('/gallery/categories', { timeout: 10000 }),
}

// Import types
import type { Settings, GenerateRequest, ChatMessage } from '../types'
