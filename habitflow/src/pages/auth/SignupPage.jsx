import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { auth } from '../../utils/api'
import { useStore } from '../../store'
import { useToast } from '../../components/ui/Toast'

export default function SignupPage() {
  const [form, setForm] = useState({ username:'', email:'', password:'', display_name:'' })
  const [loading, setLoading] = useState(false)
  const { setUser, setToken } = useStore()
  const navigate = useNavigate()
  const toast = useToast()

  const submit = async e => {
    e.preventDefault()
    if (form.password.length < 6) { toast('Password must be 6+ characters', 'error'); return }
    setLoading(true)
    try {
      const res = await auth.signup(form)
      setToken(res.token)
      setUser(res.user)
      toast('Welcome to HabitFlow! 🌱', 'success')
      navigate('/')
    } catch (err) {
      toast(err.detail || 'Signup failed', 'error')
    } finally { setLoading(false) }
  }

  const f = (k) => e => setForm(p => ({ ...p, [k]: e.target.value }))

  return (
    <div style={{ minHeight:'100vh', display:'flex', alignItems:'center', justifyContent:'center', padding:24, background:'var(--bg)' }}>
      <div style={{ width:'100%', maxWidth:360 }}>
        <div style={{ textAlign:'center', marginBottom:28 }}>
          <div style={{ fontSize:48, marginBottom:8 }}>🌱</div>
          <h1 style={{ fontFamily:'var(--font-display)', fontSize:28, fontWeight:800 }}>Join HabitFlow</h1>
          <p style={{ color:'var(--text2)', marginTop:4 }}>Start your habit journey today</p>
        </div>
        <div className="card" style={{ padding:24 }}>
          <form onSubmit={submit}>
            <div className="input-group">
              <label className="input-label">Display Name</label>
              <input className="input" required placeholder="Alex Chen" value={form.display_name} onChange={f('display_name')} />
            </div>
            <div className="input-group">
              <label className="input-label">Username</label>
              <input className="input" required placeholder="alexchen" value={form.username} onChange={f('username')}
                pattern="[a-zA-Z0-9_]+" title="Letters, numbers, underscores only" />
            </div>
            <div className="input-group">
              <label className="input-label">Email</label>
              <input className="input" type="email" required placeholder="you@example.com" value={form.email} onChange={f('email')} />
            </div>
            <div className="input-group">
              <label className="input-label">Password</label>
              <input className="input" type="password" required placeholder="Min 6 characters" value={form.password} onChange={f('password')} />
            </div>
            <button className="btn btn-primary btn-full" type="submit" disabled={loading}>
              {loading ? <span className="spinner"/> : 'Create account'}
            </button>
          </form>
          <p style={{ textAlign:'center', marginTop:16, fontSize:13, color:'var(--text2)' }}>
            Already have an account? <Link to="/login" style={{ color:'var(--accent)', fontWeight:600 }}>Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
