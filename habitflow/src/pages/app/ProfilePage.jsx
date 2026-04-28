import { useState } from 'react'
import { useStore } from '../../store'
import { useNavigate } from 'react-router-dom'
import { useToast } from '../../components/ui/Toast'
import { social } from '../../utils/api'
import http from '../../utils/api'

export default function ProfilePage() {
  const { user, setUser, logout } = useStore()
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({ display_name: user?.display_name || '', bio: user?.bio || '', is_profile_public: user?.is_profile_public ?? true })
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const toast = useToast()

  const save = async () => {
    setLoading(true)
    try {
      await http.patch('/profile', form)
      setUser({ ...user, ...form })
      setEditing(false)
      toast('Profile updated', 'success')
    } catch (e) { toast('Error saving', 'error') }
    finally { setLoading(false) }
  }

  const doLogout = () => { logout(); navigate('/login') }

  const COLORS = ['#6ee7b7','#60a5fa','#a78bfa','#fb7185','#fbbf24','#34d399','#f97316','#e879f9']

  const setColor = async (c) => {
    await http.patch('/profile', { avatar_color: c })
    setUser({ ...user, avatar_color: c })
  }

  return (
    <div className="page">
      <div style={{ padding:'20px 20px 0' }}>
        <h1 style={{ fontFamily:'var(--font-display)', fontSize:24, fontWeight:800, marginBottom:20 }}>Profile</h1>

        {/* Avatar + name */}
        <div className="card" style={{ marginBottom:12, textAlign:'center', padding:24 }}>
          <div style={{ width:72, height:72, borderRadius:'50%', background: user?.avatar_color || '#6ee7b7',
                        display:'flex', alignItems:'center', justifyContent:'center',
                        fontFamily:'var(--font-display)', fontSize:28, fontWeight:800, color:'white',
                        margin:'0 auto 12px' }}>
            {(user?.display_name||'?').slice(0,2).toUpperCase()}
          </div>
          <div style={{ fontFamily:'var(--font-display)', fontSize:20, fontWeight:800 }}>{user?.display_name}</div>
          <div style={{ color:'var(--text2)', fontSize:13 }}>@{user?.username}</div>
          {user?.bio && <div style={{ color:'var(--text2)', fontSize:13, marginTop:6 }}>{user.bio}</div>}

          {/* Color picker */}
          <div style={{ display:'flex', justifyContent:'center', gap:8, marginTop:12 }}>
            {COLORS.map(c => (
              <div key={c} onClick={() => setColor(c)}
                style={{ width:20, height:20, borderRadius:'50%', background:c, cursor:'pointer',
                         border: user?.avatar_color === c ? '2px solid var(--text)' : '2px solid transparent' }} />
            ))}
          </div>
        </div>

        {/* Stats row */}
        <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:10, marginBottom:12 }}>
          {[
            { label:'Streak', val:`${user?.current_streak||0}🔥` },
            { label:'Total', val:user?.total_completions||0 },
            { label:'Best', val:`${user?.longest_streak||0}d` },
          ].map(s => (
            <div key={s.label} className="card" style={{ textAlign:'center' }}>
              <div style={{ fontFamily:'var(--font-display)', fontSize:18, fontWeight:800 }}>{s.val}</div>
              <div style={{ fontSize:11, color:'var(--text2)' }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Edit form */}
        {editing ? (
          <div className="card" style={{ marginBottom:12 }}>
            <div className="modal-title" style={{ fontSize:16 }}>Edit profile</div>
            <div className="input-group">
              <label className="input-label">Display Name</label>
              <input className="input" value={form.display_name} onChange={e => setForm(p => ({ ...p, display_name: e.target.value }))} />
            </div>
            <div className="input-group">
              <label className="input-label">Bio</label>
              <textarea className="input" rows={3} placeholder="Tell the community about yourself..."
                value={form.bio} onChange={e => setForm(p => ({ ...p, bio: e.target.value }))} />
            </div>
            <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:14 }}>
              <input type="checkbox" id="pub" checked={form.is_profile_public}
                onChange={e => setForm(p => ({ ...p, is_profile_public: e.target.checked }))} />
              <label htmlFor="pub" style={{ fontSize:13, cursor:'pointer' }}>Public profile</label>
            </div>
            <div style={{ display:'flex', gap:8 }}>
              <button className="btn btn-primary btn-sm" onClick={save} disabled={loading}>Save</button>
              <button className="btn btn-ghost btn-sm" onClick={() => setEditing(false)}>Cancel</button>
            </div>
          </div>
        ) : (
          <button className="btn btn-ghost btn-full" style={{ marginBottom:12 }} onClick={() => setEditing(true)}>
            Edit profile
          </button>
        )}

        {/* Account */}
        <div className="card" style={{ marginBottom:12 }}>
          <div style={{ fontSize:11, color:'var(--text3)', marginBottom:8, fontFamily:'var(--font-mono)', textTransform:'uppercase', letterSpacing:'0.5px' }}>Account</div>
          <div style={{ fontSize:13, color:'var(--text2)', marginBottom:4 }}>📧 {user?.email}</div>
          <div style={{ fontSize:11, color:'var(--text3)', fontFamily:'var(--font-mono)' }}>
            NudgeOps ID: {user?.nudgeops_user_id?.slice(0,16)}...
          </div>
        </div>

        {/* NudgeOps badge */}
        <div className="card" style={{ marginBottom:12, background:'var(--accent-bg)', borderColor:'rgba(45,106,79,0.2)' }}>
          <div style={{ fontSize:13, color:'var(--accent)', fontWeight:600, marginBottom:4 }}>✦ Powered by NudgeOps</div>
          <div style={{ fontSize:12, color:'var(--text2)' }}>
            Your nudges are personalized using a contextual Thompson Sampling bandit that learns your response patterns over time.
          </div>
        </div>

        <button className="btn btn-danger btn-full" onClick={doLogout}>Sign out</button>
      </div>
    </div>
  )
}
