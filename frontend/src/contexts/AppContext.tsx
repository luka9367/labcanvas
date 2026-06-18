import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react'
import type { Project, Settings, GenerationMode, GenerationStep } from '../types'

// Local storage keys
const STORAGE_KEYS = {
  SETTINGS: 'labcanvas_settings',
  GENERATION_MODE: 'labcanvas_generation_mode',
  SIDEBAR_OPEN: 'labcanvas_sidebar_open',
}

// Safe localStorage access
const storage = {
  get: (key: string, defaultValue: any = null) => {
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : defaultValue
    } catch {
      return defaultValue
    }
  },
  set: (key: string, value: any) => {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (e) {
      console.warn('Failed to save to localStorage:', e)
    }
  },
  remove: (key: string) => {
    try {
      localStorage.removeItem(key)
    } catch (e) {
      console.warn('Failed to remove from localStorage:', e)
    }
  },
}

interface AppContextType {
  // Settings
  settings: Settings | null
  setSettings: (settings: Settings) => void
  
  // Current project
  currentProject: Project | null
  setCurrentProject: (project: Project | null) => void
  
  // Generation state
  isGenerating: boolean
  setIsGenerating: (value: boolean) => void
  generationProgress: string
  setGenerationProgress: (value: string) => void
  generationSteps: GenerationStep[]
  setGenerationSteps: (steps: GenerationStep[]) => void
  abortController: AbortController | null
  setAbortController: (ctrl: AbortController | null) => void
  
  // UI state
  sidebarOpen: boolean
  setSidebarOpen: (value: boolean) => void
  activePanel: string | null
  setActivePanel: (value: string | null) => void
  
  // Generation mode
  generationMode: GenerationMode
  setGenerationMode: (mode: GenerationMode) => void
  
  // Refresh functions
  refreshProjects: () => Promise<void>
  setRefreshProjects: (fn: () => Promise<void>) => void
}

const AppContext = createContext<AppContextType | undefined>(undefined)

export function AppProvider({ children }: { children: ReactNode }) {
  // Initialize state from localStorage
  const [settings, setSettingsState] = useState<Settings | null>(() => 
    storage.get(STORAGE_KEYS.SETTINGS, null)
  )
  const [currentProject, setCurrentProject] = useState<Project | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generationProgress, setGenerationProgress] = useState('')
  const [generationSteps, setGenerationSteps] = useState<GenerationStep[]>([])
  const [abortController, setAbortController] = useState<AbortController | null>(null)
  const [sidebarOpen, setSidebarOpenState] = useState<boolean>(() => 
    storage.get(STORAGE_KEYS.SIDEBAR_OPEN, true)
  )
  const [activePanel, setActivePanel] = useState<string | null>(null)
  const [generationMode, setGenerationModeState] = useState<GenerationMode>(() => 
    storage.get(STORAGE_KEYS.GENERATION_MODE, 'auto')
  )
  const [refreshProjects, setRefreshProjectsState] = useState<() => Promise<void>>(async () => {})

  // Persist settings to localStorage (excluding sensitive data)
  const setSettings = useCallback((newSettings: Settings) => {
    // Remove sensitive fields before storing
    const settingsToStore = { ...newSettings }
    delete (settingsToStore as any).llm_api_key
    delete (settingsToStore as any).image_api_key
    delete (settingsToStore as any).vision_api_key
    delete (settingsToStore as any).mineru_token
    
    setSettingsState(newSettings)
    storage.set(STORAGE_KEYS.SETTINGS, settingsToStore)
  }, [])

  // Persist sidebar state
  const setSidebarOpen = useCallback((value: boolean) => {
    setSidebarOpenState(value)
    storage.set(STORAGE_KEYS.SIDEBAR_OPEN, value)
  }, [])

  // Persist generation mode
  const setGenerationMode = useCallback((mode: GenerationMode) => {
    setGenerationModeState(mode)
    storage.set(STORAGE_KEYS.GENERATION_MODE, mode)
  }, [])

  const setRefreshProjects = useCallback((fn: () => Promise<void>) => {
    setRefreshProjectsState(() => fn)
  }, [])

  // Load settings from API on mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const { settingsApi } = await import('../services/api')
        const response = await settingsApi.get()
        if (response.success && response.settings) {
          // Merge with local settings (keeping sensitive data)
          setSettingsState(prev => ({
            ...prev,
            ...response.settings,
          }))
        }
      } catch (error) {
        console.error('Failed to load settings:', error)
      }
    }
    loadSettings()
  }, [])

  return (
    <AppContext.Provider
      value={{
        settings,
        setSettings,
        currentProject,
        setCurrentProject,
        isGenerating,
        setIsGenerating,
        generationProgress,
        setGenerationProgress,
        generationSteps,
        setGenerationSteps,
        abortController,
        setAbortController,
        sidebarOpen,
        setSidebarOpen,
        activePanel,
        setActivePanel,
        generationMode,
        setGenerationMode,
        refreshProjects,
        setRefreshProjects,
      }}
    >
      {children}
    </AppContext.Provider>
  )
}

export function useApp() {
  const context = useContext(AppContext)
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider')
  }
  return context
}
