import { useEffect, useState } from 'react'
import { audit } from '../utils/api'
import { BookOpen, RefreshCw } from 'lucide-react'

const ACTION_BADGE = {
  user_created:'badge-green', policy_promoted:'badge-blue', policy_rolled_back:'badge-red',
  experiment_started:'badge-purple', experiment_concluded:'badge-green',
}

export default function AuditPage() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState({ actor:'', action:'' })

  const load = () => {
    audit.list({ ...Object.fromEntries(Object.entries(filter).filter(([,v])=>v)), limit:200 })
      .then(setLogs).catch(console.error).finally(() => setLoading(false))
  }
  useEffect(() => { load() }, [])

  if (loading) return <div className="loading">Loading audit logs...</div>

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-title">Audit Log</div>
          <div className="page-subtitle">Human-readable compliance and policy change trail</div>
        </div>
        <button className="btn btn-ghost" onClick={load}><RefreshCw size={14}/> Refresh</button>
      </div>

      <div className="card" style={{marginBottom:16,padding:14}}>
        <div style={{display:'flex',gap:12,alignItems:'flex-end'}}>
          <div style={{flex:1}}>
            <label>Filter by Actor</label>
            <input placeholder="api, system, ..." value={filter.actor} onChange={e=>setFilter(p=>({...p,actor:e.target.value}))} />
          </div>
          <div style={{flex:1}}>
            <label>Filter by Action</label>
            <input placeholder="policy_promoted, ..." value={filter.action} onChange={e=>setFilter(p=>({...p,action:e.target.value}))} />
          </div>
          <button className="btn btn-primary btn-sm" onClick={load} style={{marginBottom:1}}>Apply</button>
        </div>
      </div>

      <div className="card" style={{padding:0}}>
        <table>
          <thead><tr><th>Time</th><th>Actor</th><th>Action</th><th>Resource</th><th>Outcome</th><th>Details</th></tr></thead>
          <tbody>
            {logs.map(l => (
              <tr key={l.id}>
                <td style={{fontSize:11,color:'var(--text-2)',fontFamily:'var(--font-mono)',whiteSpace:'nowrap'}}>
                  {new Date(l.created_at).toLocaleString()}
                </td>
                <td style={{fontFamily:'var(--font-mono)',fontSize:12}}>{l.actor}</td>
                <td><span className={`badge ${ACTION_BADGE[l.action]||'badge-gray'}`}>{l.action.replace(/_/g,' ')}</span></td>
                <td style={{fontSize:12}}>
                  <span style={{color:'var(--text-2)'}}>{l.resource_type}</span>
                  {l.resource_id && <span style={{fontFamily:'var(--font-mono)',fontSize:10,color:'var(--text-2)',marginLeft:6}}>
                    {l.resource_id.slice(0,10)}…
                  </span>}
                </td>
                <td><span className={`badge ${l.outcome==='success'?'badge-green':'badge-red'}`}>{l.outcome}</span></td>
                <td style={{fontSize:11,color:'var(--text-2)',maxWidth:200,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>
                  {Object.keys(l.details||{}).length > 0 ? JSON.stringify(l.details) : '—'}
                </td>
              </tr>
            ))}
            {logs.length === 0 && (
              <tr><td colSpan={6} style={{textAlign:'center',color:'var(--text-2)',padding:40}}>No audit logs yet</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
