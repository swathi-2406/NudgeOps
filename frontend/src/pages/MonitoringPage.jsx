import { useEffect, useState } from 'react'
import { monitoring } from '../utils/api'
import { RefreshCw, AlertTriangle, CheckCircle, ShieldCheck } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const COLORS = ['#7c6af7','#22d3a0','#f5c542','#f05070','#4ca8f0','#a594ff','#ff8c42','#52d9c8']

export default function MonitoringPage() {
  const [metrics, setMetrics] = useState(null)
  const [fairness, setFairness] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const load = async () => {
    setRefreshing(true)
    const [m, f] = await Promise.all([monitoring.metrics(), monitoring.fairness()])
    setMetrics(m)
    setFairness(f)
    setLoading(false)
    setRefreshing(false)
  }
  useEffect(() => { load() }, [])

  if (loading) return <div className="loading">Loading monitoring data...</div>

  const feedbackData = metrics?.feedback_distribution_7d
    ? Object.entries(metrics.feedback_distribution_7d).map(([s,c],i) => ({ signal:s, count:c, fill:COLORS[i] }))
    : []

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-title">System Monitoring</div>
          <div className="page-subtitle">Live platform health, fairness checks, failure detection</div>
        </div>
        <button className="btn btn-ghost" onClick={load} disabled={refreshing}>
          <RefreshCw size={14} className={refreshing ? 'spinning' : ''}/> Refresh
        </button>
      </div>

      {metrics?.alerts?.length > 0 && (
        <div style={{marginBottom:20}}>
          {metrics.alerts.map((a,i) => (
            <div key={i} style={{display:'flex',gap:10,alignItems:'center',padding:'10px 14px',
                                   background:'rgba(245,197,66,0.08)',border:'1px solid rgba(245,197,66,0.3)',
                                   borderRadius:8,marginBottom:8}}>
              <AlertTriangle size={15} color="var(--yellow)" />
              <span style={{fontSize:13,color:'var(--yellow)'}}>{a.message}</span>
            </div>
          ))}
        </div>
      )}

      <div className="grid-4" style={{marginBottom:24}}>
        <div className="stat-card">
          <div className="stat-label">Total Interventions</div>
          <div className="stat-value">{metrics?.total_interventions_all_time?.toLocaleString()}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Last 24h</div>
          <div className="stat-value" style={{color:'var(--accent-2)'}}>{metrics?.interventions_last_24h}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Active Users (7d)</div>
          <div className="stat-value" style={{color:'var(--green)'}}>{metrics?.active_users_7d}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Failing Arms</div>
          <div className="stat-value" style={{color: (metrics?.failing_arms_count||0) > 0 ? 'var(--red)' : 'var(--green)'}}>
            {metrics?.failing_arms_count ?? 0}
          </div>
        </div>
      </div>

      <div className="grid-2" style={{marginBottom:24}}>
        <div className="card">
          <div className="section-title">Feedback Signals (7d)</div>
          <div className="grid-2" style={{gap:8,marginBottom:16}}>
            <div style={{padding:'10px 12px',background:'var(--bg-3)',borderRadius:8}}>
              <div style={{fontSize:11,color:'var(--text-2)'}}>Completion Rate</div>
              <div style={{fontFamily:'var(--font-mono)',fontSize:20,fontWeight:700,color:'var(--green)'}}>
                {metrics ? `${(metrics.completion_rate_7d*100).toFixed(1)}%` : '—'}
              </div>
            </div>
            <div style={{padding:'10px 12px',background:'var(--bg-3)',borderRadius:8}}>
              <div style={{fontSize:11,color:'var(--text-2)'}}>Negative Rate</div>
              <div style={{fontFamily:'var(--font-mono)',fontSize:20,fontWeight:700,color: (metrics?.negative_rate_7d||0)>0.2?'var(--red)':'var(--text)'}}>
                {metrics ? `${(metrics.negative_rate_7d*100).toFixed(1)}%` : '—'}
              </div>
            </div>
          </div>
          {feedbackData.length > 0 && (
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={feedbackData} barSize={28}>
                <XAxis dataKey="signal" tick={{fill:'var(--text-2)',fontSize:11}} axisLine={false} tickLine={false} />
                <YAxis tick={{fill:'var(--text-2)',fontSize:11}} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{background:'var(--bg-3)',border:'1px solid var(--border)',borderRadius:8,fontSize:12}} />
                <Bar dataKey="count" radius={[4,4,0,0]}>
                  {feedbackData.map((d,i) => <Cell key={i} fill={d.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="card">
          <div className="section-title" style={{display:'flex',alignItems:'center',gap:8}}>
            <ShieldCheck size={14}/> Fairness Report
          </div>
          <div style={{display:'flex',alignItems:'center',gap:12,marginBottom:16,padding:'12px 14px',
                       background: fairness?.is_fair ? 'rgba(34,211,160,0.08)' : 'rgba(240,80,112,0.08)',
                       borderRadius:8, border: `1px solid ${fairness?.is_fair ? 'rgba(34,211,160,0.2)' : 'rgba(240,80,112,0.2)'}`}}>
            {fairness?.is_fair
              ? <><CheckCircle size={16} color="var(--green)"/><span style={{color:'var(--green)',fontWeight:600}}>Fairness constraints satisfied</span></>
              : <><AlertTriangle size={16} color="var(--red)"/><span style={{color:'var(--red)',fontWeight:600}}>{fairness?.violation_count} fairness violations detected</span></>
            }
          </div>
          <div className="grid-2" style={{gap:10}}>
            {[['Users Analyzed', fairness?.users_analyzed],
              ['Window', `${fairness?.window_days}d`],
              ['Fairness Cap', `${(fairness?.fairness_cap||0)*100}%`],
              ['Violations', fairness?.violation_count]].map(([k,v]) => (
              <div key={k}><div style={{fontSize:11,color:'var(--text-2)'}}>{k}</div>
              <div style={{fontFamily:'var(--font-mono)',fontSize:15,fontWeight:700}}>{v ?? '—'}</div></div>
            ))}
          </div>
          {fairness?.violations?.length > 0 && (
            <div style={{marginTop:12}}>
              <div style={{fontSize:11,color:'var(--text-2)',marginBottom:8}}>Violations</div>
              {fairness.violations.slice(0,5).map((v,i) => (
                <div key={i} style={{padding:'6px 10px',background:'rgba(240,80,112,0.08)',borderRadius:6,
                                      fontSize:11,marginBottom:4,fontFamily:'var(--font-mono)',color:'var(--red)'}}>
                  user {v.user_id.slice(0,10)} · arm {v.intervention_id.slice(0,8)} · {(v.share*100).toFixed(0)}% share
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {metrics?.failing_arms?.length > 0 && (
        <div className="card">
          <div className="section-title">🔴 Failing Intervention Arms</div>
          <table>
            <thead><tr><th>User ID</th><th>Intervention Type</th><th>Status</th></tr></thead>
            <tbody>
              {metrics.failing_arms.map((fa,i) => (
                <tr key={i}>
                  <td style={{fontFamily:'var(--font-mono)',fontSize:11}}>{fa.user_id}</td>
                  <td>{fa.intervention_type.replace(/_/g,' ')}</td>
                  <td><span className="badge badge-red">failing</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
