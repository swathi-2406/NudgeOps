import { useEffect, useState } from 'react'
import { interventions as intvsApi } from '../utils/api'
import { Zap } from 'lucide-react'

const RISK_BADGE = { low: 'badge-green', medium: 'badge-yellow', high: 'badge-red' }

const MANIP_COLOR = (score) => {
  if (score <= 3) return 'var(--green)'
  if (score <= 6) return 'var(--yellow)'
  return 'var(--red)'
}

export default function InterventionsPage() {
  const [items, setItems] = useState([])
  const [selected, setSelected] = useState(null)
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    intvsApi.list({ active_only: false }).then(setItems).catch(console.error).finally(() => setLoading(false))
  }, [])

  const selectIntv = async (intv) => {
    setSelected(intv)
    const l = await intvsApi.getLogs(intv.id, { limit: 20 }).catch(() => [])
    setLogs(l)
  }

  if (loading) return <div className="loading">Loading interventions...</div>

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-title">Interventions</div>
          <div className="page-subtitle">{items.length} strategy types in catalog</div>
        </div>
      </div>

      <div className="grid-2">
        <div style={{display:'flex',flexDirection:'column',gap:10}}>
          {items.map(intv => (
            <div key={intv.id} onClick={() => selectIntv(intv)}
                 className="card" style={{cursor:'pointer',transition:'border-color 0.15s',
                   borderColor: selected?.id === intv.id ? 'var(--accent)' : 'var(--border)'}}>
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:8}}>
                <div style={{fontWeight:600,fontSize:14}}>{intv.name}</div>
                <div style={{display:'flex',gap:6}}>
                  <span className={`badge ${RISK_BADGE[intv.risk_level] || 'badge-gray'}`}>{intv.risk_level}</span>
                  {!intv.is_active && <span className="badge badge-red">inactive</span>}
                </div>
              </div>
              <div style={{fontSize:12,color:'var(--text-2)',marginBottom:10}}>{intv.description}</div>
              <div style={{padding:'8px 12px',background:'var(--bg-3)',borderRadius:6,fontStyle:'italic',fontSize:12,color:'var(--text)'}}>
                "{intv.message_template}"
              </div>
              <div style={{display:'flex',alignItems:'center',gap:12,marginTop:10}}>
                <div style={{fontSize:11,color:'var(--text-2)'}}>Manipulativeness</div>
                <div style={{flex:1,height:3,background:'var(--bg-3)',borderRadius:2}}>
                  <div style={{width:`${intv.manipulativeness_score*10}%`,height:'100%',
                                background:MANIP_COLOR(intv.manipulativeness_score),borderRadius:2}} />
                </div>
                <div style={{fontFamily:'var(--font-mono)',fontSize:11,color:MANIP_COLOR(intv.manipulativeness_score)}}>
                  {intv.manipulativeness_score}/10
                </div>
              </div>
            </div>
          ))}
        </div>

        <div>
          {selected ? (
            <div className="card" style={{position:'sticky',top:70}}>
              <div className="section-title">Recent Delivery Logs</div>
              <div style={{fontWeight:700,marginBottom:4}}>{selected.name}</div>
              <div style={{fontSize:12,color:'var(--text-2)',marginBottom:16}}>
                Type: <span style={{fontFamily:'var(--font-mono)',color:'var(--accent-2)'}}>{selected.intervention_type}</span>
              </div>
              {logs.length === 0 ? (
                <div style={{color:'var(--text-2)',fontSize:13,padding:'20px 0'}}>No delivery logs yet</div>
              ) : (
                <table>
                  <thead><tr><th>User</th><th>Signal</th><th>Reward</th><th>Date</th></tr></thead>
                  <tbody>
                    {logs.map(l => (
                      <tr key={l.id}>
                        <td style={{fontFamily:'var(--font-mono)',fontSize:11}}>{l.user_id.slice(0,10)}</td>
                        <td><span className={`badge ${l.feedback_signal === 'completed' ? 'badge-green' : l.feedback_signal === 'negative' ? 'badge-red' : 'badge-gray'}`}>
                          {l.feedback_signal || 'pending'}
                        </span></td>
                        <td style={{fontFamily:'var(--font-mono)',fontSize:12,color:l.reward > 0 ? 'var(--green)' : l.reward < 0 ? 'var(--red)' : 'var(--text-2)'}}>
                          {l.reward != null ? l.reward.toFixed(2) : '—'}
                        </td>
                        <td style={{fontSize:11,color:'var(--text-2)'}}>{new Date(l.delivered_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          ) : (
            <div className="card" style={{display:'flex',alignItems:'center',justifyContent:'center',height:200,color:'var(--text-2)',fontSize:13}}>
              ← Select an intervention to view logs
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
