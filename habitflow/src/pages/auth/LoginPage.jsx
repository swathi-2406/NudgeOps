import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { auth } from '../../utils/api'
import { useStore } from '../../store'
import { useToast } from '../../components/ui/Toast'

export default function LoginPage() {
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const { setUser, setToken } = useStore()
  const navigate = useNavigate()
  const toast = useToast()

  const submit = async e => {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await auth.login(form)
      setToken(res.token)
      setUser(res.user)
      navigate('/')
    } catch (err) {
      toast(err.detail || 'Login failed', 'error')
    } finally { setLoading(false) }
  }

  return (
    <div style={{ minHeight:'100vh', display:'flex', alignItems:'center', justifyContent:'center', padding:24, background:'var(--bg)' }}>
      <div style={{ width:'100%', maxWidth:360 }}>
        <div style={{ textAlign:'center', marginBottom:32 }}>
          <div style={{ fontSize:48, marginBottom:8 }}>🌱</div>
          <h1 style={{ fontFamily:'var(--font-display)', fontSize:28, fontWeight:800 }}>HabitFlow</h1>
          <p style={{ color:'var(--text2)', marginTop:4 }}>Build habits that stick</p>
        </div>
        <div className="card" style={{ padding:24 }}>
          <form onSubmit={submit}>
            <div className="input-group">
              <label className="input-label">Email</label>
              <input className="input" type="email" required placeholder="you@example.com"
                value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))} />
            </div>
            <div className="input-group">
              <label className="input-label">Password</label>
              <input className="input" type="password" required placeholder="••••••••"
                value={form.password} onChange={e => setForm(p => ({ ...p, password: e.target.value }))} />
            </div>
            <button className="btn btn-primary btn-full" type="submit" disabled={loading}>
              {loading ? <span className="spinner"/> : 'Sign in'}
            </button>
          </form>
          <p style={{ textAlign:'center', marginTop:16, fontSize:13, color:'var(--text2)' }}>
            No account? <Link to="/signup" style={{ color:'var(--accent)', fontWeight:600 }}>Sign up</Link>
          </p>
        </div>
        <p style={{ textAlign:'center', marginTop:16, fontSize:11, color:'var(--text3)' }}>
          Powered by NudgeOps · AI-personalized nudges
        </p>
      </div>
    </div>
  )
}
