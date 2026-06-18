import { Routes, Route } from 'react-router-dom'
import { AppProvider } from './contexts/AppContext'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import EditorPage from './pages/EditorPage'
import SettingsPage from './pages/SettingsPage'
import GalleryPage from './pages/GalleryPage'

function App() {
  return (
    <AppProvider>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="editor" element={<EditorPage />} />
          <Route path="editor/:projectId" element={<EditorPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="gallery" element={<GalleryPage />} />
        </Route>
      </Routes>
    </AppProvider>
  )
}

export default App
