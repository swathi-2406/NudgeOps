import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useStore } from './store'
import { ToastProvider } from './components/ui/Toast'
import LoginPage from './pages/auth/LoginPage'
import SignupPage from './pages/auth/SignupPage'
import HomePage from './pages/app/HomePage'
import StatsPage from './pages/app/StatsPage'
import NudgePage from './pages/app/NudgePage'
import SocialPage from './pages/app/SocialPage'
import ProfilePage from './pages/app/ProfilePage'
import HabitDetailPage from './pages/app/HabitDetailPage'

function ProtectedLayout() {
  const { user } = useStore()
  if (!user) return <Navigate to="/login" replace />
  return <AppLayout />
}

function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const path = location.pathname

  const tabs = [
    { path: '/',       icon: '🏠', label: 'Home' },
    { path: '/nudge',  icon: '✦',  label: 'Nudge' },
    { path: '/stats',  icon: '📊', label: 'Stats' },
    { path: '/social', icon: '👥', label: 'Social' },
    { path: '/profile',icon: '👤', label: 'Me' },
  ]

  return (
    <div className="app-shell">
      <Routes>
        <Route path="/"              element={<HomePage />} />
        <Route path="/nudge"         element={<NudgePage />} />
        <Route path="/stats"         element={<StatsPage />} />
        <Route path="/social"        element={<SocialPage />} />
        <Route path="/profile"       element={<ProfilePage />} />
        <Route path="/habit/:id"     element={<HabitDetailPage />} />
      </Routes>
      <nav className="bottom-nav">
        {tabs.map(t => (
          <button key={t.path} className={`nav-item ${path === t.path ? 'active' : ''}`}
            onClick={() => navigate(t.path)}>
            <span style={{ fontSize:20 }}>{t.icon}</span>
            {t.label}
          </button>
        ))}
      </nav>
    </div>
  )
}

export default function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <div className="app-shell">
          <Routes>
            <Route path="/login"  element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/*"      element={<ProtectedLayout />} />
          </Routes>
        </div>
      </BrowserRouter>
    </ToastProvider>
  )
}
