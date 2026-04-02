import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { Activity, Users, Zap, FlaskConical, Shield, BookOpen, Layers, Menu, X } from 'lucide-react'
import { useState } from 'react'
import Dashboard from './pages/Dashboard'
import UsersPage from './pages/UsersPage'
import InterventionsPage from './pages/InterventionsPage'
import ExperimentsPage from './pages/ExperimentsPage'
import PoliciesPage from './pages/PoliciesPage'
import MonitoringPage from './pages/MonitoringPage'
import AuditPage from './pages/AuditPage'

const NAV = [
  { to: '/', icon: Activity, label: 'Dashboard' },
  { to: '/users', icon: Users, label: 'Users' },
  { to: '/interventions', icon: Zap, label: 'Interventions' },
  { to: '/experiments', icon: FlaskConical, label: 'A/B Tests' },
  { to: '/policies', icon: Layers, label: 'Policies' },
  { to: '/monitoring', icon: Shield, label: 'Monitoring' },
  { to: '/audit', icon: BookOpen, label: 'Audit Log' },
]

function Sidebar({ open, onClose }) {
  return (
    <>
      {open && <div onClick={onClose} style={{position:'fixed',inset:0,background:'rgba(0,0,0,0.5)',zIndex:99}} />}
      <aside style={{
        position: 'fixed', left: 0, top: 0, bottom: 0, width: 220,
        background: 'var(--bg-2)', borderRight: '1px solid var(--border)',
        display: 'flex', flexDirection: 'column', zIndex: 100,
        transform: open ? 'translateX(0)' : 'translateX(-100%)',
        transition: 'transform 0.2s',
      }}>
        <div style={{padding:'24px 20px 16px', borderBottom:'1px solid var(--border)'}}>
          <div style={{fontFamily:'var(--font-mono)',fontSize:16,fontWeight:700,color:'var(--accent-2)',letterSpacing:'-0.5px'}}>
            ⬡ NudgeOps
          </div>
          <div style={{fontSize:11,color:'var(--text-2)',marginTop:4,letterSpacing:'0.5px'}}>MLOps Platform v1.0</div>
        </div>
        <nav style={{flex:1,padding:'12px 10px',overflowY:'auto'}}>
          {NAV.map(({to, icon: Icon, label}) => (
            <NavLink key={to} to={to} end={to==='/'} onClick={onClose}
              style={({isActive}) => ({
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '9px 12px', borderRadius: 8, marginBottom: 2,
                color: isActive ? 'var(--accent-2)' : 'var(--text-2)',
                background: isActive ? 'rgba(124,106,247,0.12)' : 'transparent',
                fontWeight: isActive ? 600 : 400, fontSize: 13,
                textDecoration: 'none', transition: 'all 0.12s',
              })}>
              <Icon size={15} /> {label}
            </NavLink>
          ))}
        </nav>
        <div style={{padding:'16px 20px',borderTop:'1px solid var(--border)',fontSize:11,color:'var(--text-2)'}}>
          SQLite · Redis · FastAPI
        </div>
      </aside>
    </>
  )
}

function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  return (
    <div style={{display:'flex',minHeight:'100vh'}}>
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div style={{marginLeft: sidebarOpen ? 220 : 0, flex:1, transition:'margin-left 0.2s', minWidth:0}}>
        <header style={{
          height:52, background:'var(--bg-2)', borderBottom:'1px solid var(--border)',
          display:'flex', alignItems:'center', padding:'0 24px', gap:12,
          position:'sticky', top:0, zIndex:50,
        }}>
          <button onClick={() => setSidebarOpen(v => !v)}
            style={{background:'none',border:'none',color:'var(--text-2)',cursor:'pointer',padding:4}}>
            {sidebarOpen ? <X size={18}/> : <Menu size={18}/>}
          </button>
          <span style={{fontFamily:'var(--font-mono)',fontSize:12,color:'var(--text-2)'}}>
            api: localhost:8000 · docs: /docs
          </span>
        </header>
        <main>{children}</main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/users" element={<UsersPage />} />
          <Route path="/interventions" element={<InterventionsPage />} />
          <Route path="/experiments" element={<ExperimentsPage />} />
          <Route path="/policies" element={<PoliciesPage />} />
          <Route path="/monitoring" element={<MonitoringPage />} />
          <Route path="/audit" element={<AuditPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
