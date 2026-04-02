import { useEffect, useState } from 'react'
import { users as usersApi, bandit, features } from '../utils/api'
import { UserPlus, ChevronRight, Brain } from 'lucide-react'

const SEGMENT_BADGE = {
  high_engagement: 'badge-green', moderate_engagement: 'badge-blue',
  low_engagement: 'badge-gray', at_risk_churn: 'badge-red',
  new_user: 'badge-purple', returning: 'badge-yellow',
}

export default function UsersPage() {
  const [userList, setUserList] = useState([])
  const [selected, setSelected] = useState(null)
  const [banditState, setBanditState] = useState(null)
  const [userFeatures, setUserFeatures] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ external_id: '', display_name: '', email: '' })
  const [nudgeResult, setNudgeResult] = useState(null)

  useEffect(() => {
    usersApi.list({ limit: 50 }).then(setUserList).catch(console.error).finally(() => setLoading(false))
  }, [])

  const selectUser = async (user) => {
    setSelected(user)
    setNudgeResult(null)
    const [bs, uf] = await Promise.all([
      bandit.getState(user.id).catch(() => []),
      features.getForUser(user.id).catch(() => null),
    ])
    setBanditState(bs)
    setUserFeatures(uf)
  }

  const createUser = async (e) => {
    e.preventDefault()
    try {
      const u = await usersApi.create(form)
      setUserList(prev => [u, ...prev])
      setShowCreate(false)
      setForm({ external_id: '', display_name: '', email: '' })
    } catch (err) { alert(JSON.stringify(err)) }
  }

  const getNudge = async () => {
    if (!selected) return
    try {
      const r = await bandit.getNudge({ user_id: selected.id })
      setNudgeResult(r)
    } catch (err) { alert(JSON.stringify(err)) }
  }

  const sendFeedback = async (signal) => {
    if (!nudgeResult) return
    await bandit.submitFeedback({ log_id: nudgeResult.log_id, user_id: selected.id, feedback_signal: signal })
    const bs = await bandit.getState(selected.id).catch(() => [])
    setBanditState(bs)
    setNudgeResult(null)
  }

  if (loading) return <div className="loading">Loading users...</div>

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-title">Users</div>
          <div className="page-subtitle">{userList.length} registered users</div>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate(v => !v)}>
          <UserPlus size={14} /> Add User
        </button>
      </div>

      {showCreate && (
        <div className="card" style={{marginBottom:20}}>
          <div className="section-title">Create User</div>
          <form onSubmit={createUser}>
            <div className="grid-3">
              <div className="form-group">
                <label>External ID *</label>
                <input required value={form.external_id} onChange={e => setForm(p=>({...p,external_id:e.target.value}))} placeholder="usr_abc123" />
              </div>
              <div className="form-group">
                <label>Display Name</label>
                <input value={form.display_name} onChange={e => setForm(p=>({...p,display_name:e.target.value}))} placeholder="Jane Doe" />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input value={form.email} onChange={e => setForm(p=>({...p,email:e.target.value}))} placeholder="jane@example.com" />
              </div>
            </div>
            <div style={{display:'flex',gap:8}}>
              <button type="submit" className="btn btn-primary btn-sm">Create</button>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setShowCreate(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="grid-2">
        <div className="card" style={{padding:0}}>
          <table>
            <thead><tr><th>User</th><th>Segment</th><th>Status</th><th></th></tr></thead>
            <tbody>
              {userList.map(u => (
                <tr key={u.id} onClick={() => selectUser(u)}
                    style={{cursor:'pointer', background: selected?.id === u.id ? 'rgba(124,106,247,0.08)' : ''}}>
                  <td>
                    <div style={{fontWeight:600,fontSize:13}}>{u.display_name || u.external_id}</div>
                    <div style={{fontFamily:'var(--font-mono)',fontSize:10,color:'var(--text-2)'}}>{u.id.slice(0,12)}…</div>
                  </td>
                  <td><span className={`badge ${SEGMENT_BADGE[u.segment] || 'badge-gray'}`}>{u.segment.replace(/_/g,' ')}</span></td>
                  <td><span className={`badge ${u.is_active ? 'badge-green' : 'badge-red'}`}>{u.is_active ? 'active' : 'inactive'}</span></td>
                  <td><ChevronRight size={14} color="var(--text-2)" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div>
          {selected ? (
            <div style={{display:'flex',flexDirection:'column',gap:16}}>
              <div className="card">
                <div className="section-title">User Details</div>
                <div style={{fontFamily:'var(--font-mono)',fontSize:18,fontWeight:700,marginBottom:4}}>{selected.display_name || selected.external_id}</div>
                <div style={{fontSize:11,color:'var(--text-2)',marginBottom:16}}>{selected.id}</div>
                <div className="grid-2" style={{gap:12}}>
                  {[['Email', selected.email || '—'],['Segment', selected.segment],['Timezone', selected.timezone],['Created', new Date(selected.created_at).toLocaleDateString()]].map(([k,v]) => (
                    <div key={k}><div style={{fontSize:11,color:'var(--text-2)',marginBottom:2}}>{k}</div><div style={{fontSize:13}}>{v}</div></div>
                  ))}
                </div>
              </div>

              <div className="card">
                <div className="section-title">Nudge Playground</div>
                <button className="btn btn-primary btn-sm" onClick={getNudge}>
                  <Brain size={13}/> Get Best Nudge
                </button>
                {nudgeResult && (
                  <div style={{marginTop:12,padding:12,background:'rgba(124,106,247,0.08)',borderRadius:8,border:'1px solid rgba(124,106,247,0.2)'}}>
                    <div style={{fontSize:11,color:'var(--accent-2)',marginBottom:6,fontWeight:600}}>{nudgeResult.intervention_type.replace(/_/g,' ').toUpperCase()} · {nudgeResult.selection_reason}</div>
                    <div style={{fontSize:14,marginBottom:12}}>{nudgeResult.message}</div>
                    <div style={{display:'flex',gap:6,flexWrap:'wrap'}}>
                      {['completed','engaged','ignored','dismissed','negative'].map(s => (
                        <button key={s} className="btn btn-ghost btn-sm" onClick={() => sendFeedback(s)}>{s}</button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {banditState && banditState.length > 0 && (
                <div className="card" style={{padding:0}}>
                  <div style={{padding:'14px 16px'}}><div className="section-title" style={{marginBottom:0}}>Bandit Arm States</div></div>
                  <table>
                    <thead><tr><th>Intervention</th><th>Pulls</th><th>Mean Reward</th><th>Est. P(success)</th></tr></thead>
                    <tbody>
                      {[...banditState].sort((a,b) => b.estimated_success_prob - a.estimated_success_prob).map(s => (
                        <tr key={s.intervention_type}>
                          <td style={{fontSize:12}}>{s.intervention_type.replace(/_/g,' ')}</td>
                          <td style={{fontFamily:'var(--font-mono)'}}>{s.n_pulls}</td>
                          <td style={{fontFamily:'var(--font-mono)',color: s.mean_reward > 0 ? 'var(--green)' : s.mean_reward < 0 ? 'var(--red)' : 'var(--text-2)'}}>{s.mean_reward?.toFixed(3)}</td>
                          <td>
                            <div style={{display:'flex',alignItems:'center',gap:8}}>
                              <div style={{flex:1,height:4,background:'var(--bg-3)',borderRadius:2}}>
                                <div style={{width:`${s.estimated_success_prob*100}%`,height:'100%',background:'var(--accent)',borderRadius:2}} />
                              </div>
                              <span style={{fontFamily:'var(--font-mono)',fontSize:11,width:38}}>{(s.estimated_success_prob*100).toFixed(0)}%</span>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ) : (
            <div className="card" style={{height:'100%',display:'flex',alignItems:'center',justifyContent:'center',color:'var(--text-2)',fontSize:13}}>
              ← Select a user to view details
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
