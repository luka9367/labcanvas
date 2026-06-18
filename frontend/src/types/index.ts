export interface Project {
  id: string
  name: string
  description?: string
  created_at: string
  updated_at: string
  thumbnail?: string
  diagram_data?: any
}

export interface Settings {
  llm_api_key: string
  llm_base_url: string
  llm_model: string
  llm_image_model: string
  llm_component_model: string
  image_api_key: string
  vision_api_key: string
  image_base_url: string
  vision_base_url: string
  api_format: string
  nanasoul_prompt: string
  mineru_token: string
  theme: string
  language: string
}

export type GenerationMode = 'auto' | 'draft' | 'generate' | 'assembly'

export interface GenerateRequest {
  prompt: string
  mode: GenerationMode
  reference_image?: string
  style_reference?: string
  language: string
}

export interface GenerateResponse {
  success: boolean
  message: string
  data?: {
    xml?: string
    image_url?: string
    mode?: string
    [key: string]: any
  }
}

export interface GalleryImage {
  id: string
  name: string
  url: string
  format: string
}

export interface BioIcon {
  id: string
  name: string
  category: string
  url: string
  svg?: string
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export interface GenerationStep {
  id: string
  label: string
  status: 'pending' | 'running' | 'complete' | 'error'
  message?: string
  detail?: string
}
