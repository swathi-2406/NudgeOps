import { useEffect, useState } from 'react'
import { experiments as expApi, policies as policiesApi } from '../utils/api'
import { FlaskConical, Play, CheckSquare, TrendingUp } from 'lucide-react'

const STATUS_BADGE = { created:'badge-gray', running:'badge-blue', concluded:'badge-green', paused:'badge-yellow', aborted:'badge-red' }
const WINNER_COLOR = { treatment:'var(--green)', control:'var(--blue)', inconclusive:'var(--yellow)' }

export default function ExperimentsPage() {
  const [items, setItems] = useState([])
  const [policies, setPolicies] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [results, setResults] = useState({})
  const [form, setForm] = useState({
    name:'', description:'', control_policy_id:'', treatment_policy_id:'',
    traffic_split:0.5, hypothesis:'', primary_metric:'completion_rate', min_sample_size:30,
  })

  const load = async () => {
    const [e, p] = await Promise.all([expApi.list(), policiesApi.list()])
    setItems(e)
    setPolicies(p)
    setLoading(false)
  }
  useEffect(() => { load() }, [])

  const create = async (e) => {
    e.preventDefault()
    await expApi.create({...form, traffic_split:parseFloat(form.traffic_split), min_sample_size:parseInt(form.min_sample_size)})
    setShowCreate(false)
    load()
  }

  const start = async (id) => { await expApi.start(id); load() }
  const conclude = async (id) => {
    const r = await expApi.conclude(id).catch(e=>e)
    setResults(prev => ({...prev, [id]: r}))
    load()
  }

  const viewResults = async (id) => {
    const r = await expApi.results(id)
    setResults(prev => ({...prev, [id]: r}))
  }

  if (loading) return <div className="loading">Loading experiments...</div>

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-title">A/B Experiments</div>
          <div className="page-subtitle">Statistical testing framework for policy comparison</div>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate(v=>!v)}><FlaskConical size={14}/> New Experiment</button>
      </div>

      {showCreate && (
        <div className="card" style={{marginBottom:20}}>
          <div className="section-title">Create Experiment</div>
          <form onSubmit={create}>
            <div className="grid-2">
              <div className="form-group">
                <label>Name *</label>
                <input required value={form.name} onChange={e=>setForm(p=>({...p,name:e.target.value}))} placeholder="thompson_vs_ucb_test" />
              </div>
              <div className="form-group">
                <label>Hypothesis</label>
                <input value={form.hypothesis} onChange={e=>setForm(p=>({...p,hypothesis:e.target.value}))} placeholder="Thompson sampling will outperform UCB by 10%" />
              </div>
              <div className="form-group">
                <label>Control Policy *</label>
                <select required value={form.control_policy_id} onChange={e=>setForm(p=>({...p,control_policy_id:e.target.value}))}>
                  <option value="">— select —</option>
                  {policies.map(p => <option key={p.id} value={p.id}>{p.name} v{p.version}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Treatment Policy *</label>
                <select required value={form.treatment_policy_id} onChange={e=>setForm(p=>({...p,treatment_policy_id:e.target.value}))}>
                  <option value="">— select —</option>
                  {policies.map(p => <option key={p.id} value={p.id}>{p.name} v{p.version}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Traffic Split (treatment fraction)</label>
                <input type="number" min="0.1" max="0.9" step="0.05" value={form.traffic_split}
                       onChange={e=>setForm(p=>({...p,traffic_split:e.target.value}))} />
              </div>
              <div className="form-group">
                <label>Min Sample Size</label>
                <input type="number" value={form.min_sample_size} onChange={e=>setForm(p=>({...p,min_sample_size:e.target.value}))} />
              </div>
            </div>
            <div style={{display:'flex',gap:8}}>
              <button type="submit" className="btn btn-primary btn-sm">Create</button>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setShowCreate(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div style={{display:'flex',flexDirection:'column',gap:16}}>
        {items.map(exp => (
          <div key={exp.id} className="card">
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:12}}>
              <div>
                <div style={{fontWeight:700,fontSize:15}}>{exp.name}</div>
                <div style={{fontSize:11,fontFamily:'var(--font-mono)',color:'var(--text-2)',marginTop:2}}>{exp.id.slice(0,16)}…</div>
              </div>
              <div style={{display:'flex',gap:8,alignItems:'center'}}>
                <span className={`badge ${STATUS_BADGE[exp.status]||'badge-gray'}`}>{exp.status}</span>
                {exp.winner && <span style={{fontFamily:'var(--font-mono)',fontSize:12,fontWeight:700,color:WINNER_COLOR[exp.winner]||'var(--text-2)'}}>winner: {exp.winner}</span>}
              </div>
            </div>

            <div className="grid-4" style={{marginBottom:12}}>
              {[['Traffic Split', `${Math.round(exp.traffic_split*100)}% treatment`],
                ['Metric', exp.primary_metric],
                ['Created', new Date(exp.created_at).toLocaleDateString()],
              ].map(([k,v]) => (
                <div key={k}><div style={{fontSize:11,color:'var(--text-2)'}}>{k}</div><div style={{fontSize:13,fontFamily:'var(--font-mono)'}}>{v}</div></div>
              ))}
            </div>

            <div style={{display:'flex',gap:8,flexWrap:'wrap'}}>
              {exp.status === 'created' && <button className="btn btn-primary btn-sm" onClick={() => start(exp.id)}><Play size={12}/> Start</button>}
              {exp.status === 'running' && <button className="btn btn-ghost btn-sm" onClick={() => conclude(exp.id)}><CheckSquare size={12}/> Conclude</button>}
              <button className="btn btn-ghost btn-sm" onClick={() => viewResults(exp.id)}><TrendingUp size={12}/> Results</button>
            </div>

            {results[exp.id] && (
              <div style={{marginTop:12,padding:12,background:'var(--bg-3)',borderRadius:8}}>
                {results[exp.id].results?.status === 'insufficient_data' ? (
                  <div style={{color:'var(--yellow)',fontSize:12}}>⚠ Insufficient data. Need {results[exp.id].results.min_required} samples per arm.</div>
                ) : results[exp.id].results?.status === 'complete' ? (
                  <div className="grid-4" style={{gap:10}}>
                    {[['p-value', results[exp.id].results.p_value],
                      ['Significant', results[exp.id].results.significant ? '✓ Yes' : '✗ No'],
                      ['Lift', `${results[exp.id].results.relative_lift_pct?.toFixed(1)}%`],
                      ["Cohen's d", results[exp.id].results.cohens_d?.toFixed(3)],
                    ].map(([k,v]) => (
                      <div key={k}><div style={{fontSize:10,color:'var(--text-2)'}}>{k}</div>
                      <div style={{fontFamily:'var(--font-mono)',fontSize:13,fontWeight:700}}>{v}</div></div>
                    ))}
                  </div>
                ) : <div style={{fontSize:12,color:'var(--text-2)'}}>No data yet for this experiment.</div>}
              </div>
            )}
          </div>
        ))}
        {items.length === 0 && <div className="card" style={{textAlign:'center',color:'var(--text-2)',padding:40}}>No experiments yet. Create your first A/B test above.</div>}
      </div>
    </div>
  )
}
