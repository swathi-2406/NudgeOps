import { useEffect, useState } from 'react'
import { policies as policiesApi } from '../utils/api'
import { Plus, ChevronUp, RotateCcw, BarChart2 } from 'lucide-react'

const STATUS_BADGE = { active:'badge-green', draft:'badge-gray', retired:'badge-red', rolled_back:'badge-red', shadow:'badge-blue' }

export default function PoliciesPage() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [evalResult, setEvalResult] = useState(null)
  const [evalId, setEvalId] = useState(null)
  const [form, setForm] = useState({ name:'', version:'1.0.0', description:'', bandit_strategy:'thompson_sampling' })

  const load = () => policiesApi.list().then(setItems).catch(console.error).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const create = async (e) => {
    e.preventDefault()
    await policiesApi.create(form)
    setShowCreate(false)
    load()
  }

  const promote = async (id) => {
    if (!confirm('Promote this policy to active? The current active policy will be retired.')) return
    await policiesApi.promote(id)
    load()
  }

  const rollback = async (id) => {
    if (!confirm('Roll back this policy?')) return
    await policiesApi.rollback(id)
    load()
  }

  const evaluate = async (id) => {
    setEvalId(id)
    const r = await policiesApi.evaluate(id).catch(e => ({ error: e.detail }))
    setEvalResult(r)
  }

  if (loading) return <div className="loading">Loading policies...</div>

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-title">Policy Registry</div>
          <div className="page-subtitle">Version-controlled intervention assignment policies</div>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate(v=>!v)}><Plus size={14}/> New Policy</button>
      </div>

      {showCreate && (
        <div className="card" style={{marginBottom:20}}>
          <div className="section-title">Create Policy</div>
          <form onSubmit={create}>
            <div className="grid-2">
              <div className="form-group">
                <label>Name *</label>
                <input required value={form.name} onChange={e=>setForm(p=>({...p,name:e.target.value}))} placeholder="my_policy" />
              </div>
              <div className="form-group">
                <label>Version *</label>
                <input required value={form.version} onChange={e=>setForm(p=>({...p,version:e.target.value}))} placeholder="1.0.0" />
              </div>
              <div className="form-group">
                <label>Bandit Strategy</label>
                <select value={form.bandit_strategy} onChange={e=>setForm(p=>({...p,bandit_strategy:e.target.value}))}>
                  <option value="thompson_sampling">Thompson Sampling</option>
                  <option value="epsilon_greedy">Epsilon Greedy</option>
                  <option value="ucb">UCB</option>
                  <option value="contextual_linucb">Contextual LinUCB</option>
                </select>
              </div>
              <div className="form-group">
                <label>Description</label>
                <input value={form.description} onChange={e=>setForm(p=>({...p,description:e.target.value}))} placeholder="Optional description" />
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
            <thead><tr><th>Policy</th><th>Strategy</th><th>Status</th><th>Actions</th></tr></thead>
            <tbody>
              {items.map(p => (
                <tr key={p.id}>
                  <td>
                    <div style={{fontWeight:600}}>{p.name}</div>
                    <div style={{fontFamily:'var(--font-mono)',fontSize:10,color:'var(--text-2)'}}>v{p.version}</div>
                  </td>
                  <td style={{fontFamily:'var(--font-mono)',fontSize:11,color:'var(--accent-2)'}}>{p.bandit_strategy}</td>
                  <td><span className={`badge ${STATUS_BADGE[p.status]||'badge-gray'}`}>{p.status}</span></td>
                  <td>
                    <div style={{display:'flex',gap:4}}>
                      {p.status === 'draft' && (
                        <button className="btn btn-ghost btn-sm" onClick={() => promote(p.id)}><ChevronUp size={12}/> Promote</button>
                      )}
                      {p.status === 'active' && (
                        <button className="btn btn-danger btn-sm" onClick={() => rollback(p.id)}><RotateCcw size={12}/> Rollback</button>
                      )}
                      <button className="btn btn-ghost btn-sm" onClick={() => evaluate(p.id)}><BarChart2 size={12}/></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {evalResult && (
          <div className="card">
            <div className="section-title">Evaluation Results</div>
            {evalResult.error ? (
              <div className="error-msg">{evalResult.error}</div>
            ) : (
              <div style={{display:'flex',flexDirection:'column',gap:12}}>
                <div className="grid-2" style={{gap:10}}>
                  {[
                    ['Health Score', evalResult.health_score?.toFixed(1) + '/100', evalResult.health_score > 60 ? 'var(--green)' : 'var(--red)'],
                    ['Completion Rate', (evalResult.completion_rate * 100)?.toFixed(1) + '%'],
                    ['Engagement Rate', (evalResult.engagement_rate * 100)?.toFixed(1) + '%'],
                    ['Mean Reward', evalResult.mean_reward?.toFixed(3)],
                    ['Dismiss Rate', (evalResult.dismiss_rate * 100)?.toFixed(1) + '%'],
                    ['Negative Rate', (evalResult.negative_rate * 100)?.toFixed(1) + '%'],
                  ].map(([label, value, color]) => (
                    <div key={label} style={{padding:'10px 12px',background:'var(--bg-3)',borderRadius:8}}>
                      <div style={{fontSize:11,color:'var(--text-2)',marginBottom:4}}>{label}</div>
                      <div style={{fontFamily:'var(--font-mono)',fontSize:16,fontWeight:700,color: color || 'var(--text)'}}>{value || '—'}</div>
                    </div>
                  ))}
                </div>
                <div style={{fontSize:11,color:'var(--text-2)'}}>
                  {evalResult.total_deliveries} deliveries · {evalResult.window_days}d window
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
