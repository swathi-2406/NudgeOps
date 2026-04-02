import { useEffect, useState } from 'react'
import { monitoring, interventions as intvsApi, policies as policiesApi } from '../utils/api'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { Activity, TrendingUp, Users, Zap, AlertTriangle, CheckCircle } from 'lucide-react'

const COLORS = ['#7c6af7','#22d3a0','#f5c542','#f05070','#4ca8f0','#a594ff','#ff8c42','#52d9c8','#e879f9','#94a3b8']

function StatCard({ label, value, sub, accent }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={accent ? {color: accent} : {}}>{value ?? '—'}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  )
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null)
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([monitoring.metrics(), monitoring.health()])
      .then(([m, h]) => { setMetrics(m); setHealth(h) })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">⬡ Loading dashboard...</div>

  const feedbackData = metrics?.feedback_distribution_7d
    ? Object.entries(metrics.feedback_distribution_7d).map(([signal, cnt]) => ({ signal, count: cnt }))
    : []

  const typeData = metrics?.intervention_type_distribution_7d
    ? Object.entries(metrics.intervention_type_distribution_7d).slice(0,8).map(([id, cnt], i) => ({
        name: id.slice(0,8), count: cnt, fill: COLORS[i % COLORS.length]
      }))
    : []

  const statusColor = health?.status === 'healthy' ? 'var(--green)' : 'var(--yellow)'

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-title">System Dashboard</div>
          <div className="page-subtitle">Real-time intervention platform metrics</div>
        </div>
        <div style={{display:'flex',alignItems:'center',gap:8}}>
          {health?.status === 'healthy'
            ? <CheckCircle size={16} color="var(--green)" />
            : <AlertTriangle size={16} color="var(--yellow)" />}
          <span style={{fontSize:13,fontFamily:'var(--font-mono)',color:statusColor}}>
            {health?.status?.toUpperCase()}
          </span>
        </div>
      </div>

      {health?.alerts?.length > 0 && (
        <div style={{background:'rgba(245,197,66,0.08)',border:'1px solid rgba(245,197,66,0.3)',
                     borderRadius:10,padding:'12px 16px',marginBottom:20,display:'flex',gap:10,alignItems:'center'}}>
          <AlertTriangle size={16} color="var(--yellow)" />
          <span style={{fontSize:13,color:'var(--yellow)'}}>
            {health.alerts.map(a => a.message).join(' · ')}
          </span>
        </div>
      )}

      <div className="grid-4" style={{marginBottom:24}}>
        <StatCard label="Total Interventions" value={metrics?.total_interventions_all_time?.toLocaleString()} sub="all time" />
        <StatCard label="Last 24h" value={metrics?.interventions_last_24h} sub="deliveries" accent="var(--accent-2)" />
        <StatCard label="Active Users (7d)" value={metrics?.active_users_7d} sub="unique" accent="var(--green)" />
        <StatCard label="Completion Rate" value={metrics ? `${(metrics.completion_rate_7d * 100).toFixed(1)}%` : null} sub="7-day window" accent="var(--blue)" />
      </div>

      <div className="grid-2" style={{marginBottom:24}}>
        <div className="card">
          <div className="section-title">Feedback Distribution (7d)</div>
          {feedbackData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={feedbackData} barSize={32}>
                <XAxis dataKey="signal" tick={{fill:'var(--text-2)',fontSize:11}} axisLine={false} tickLine={false} />
                <YAxis tick={{fill:'var(--text-2)',fontSize:11}} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{background:'var(--bg-3)',border:'1px solid var(--border)',borderRadius:8,fontSize:12}} />
                <Bar dataKey="count" radius={[4,4,0,0]}>
                  {feedbackData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : <div style={{color:'var(--text-2)',fontSize:13,padding:'40px 0',textAlign:'center'}}>No feedback data yet — run the demo seed script</div>}
        </div>

        <div className="card">
          <div className="section-title">Intervention Type Distribution (7d)</div>
          {typeData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={typeData} cx="50%" cy="50%" innerRadius={55} outerRadius={90}
                     dataKey="count" nameKey="name" paddingAngle={3}>
                  {typeData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                </Pie>
                <Tooltip contentStyle={{background:'var(--bg-3)',border:'1px solid var(--border)',borderRadius:8,fontSize:12}} />
              </PieChart>
            </ResponsiveContainer>
          ) : <div style={{color:'var(--text-2)',fontSize:13,padding:'40px 0',textAlign:'center'}}>No data yet</div>}
        </div>
      </div>

      <div className="grid-3">
        <div className="card">
          <div className="section-title">Failure Detection</div>
          <div style={{fontSize:28,fontFamily:'var(--font-mono)',fontWeight:700,
                       color: (metrics?.failing_arms_count || 0) > 0 ? 'var(--red)' : 'var(--green)'}}>
            {metrics?.failing_arms_count ?? 0}
          </div>
          <div style={{color:'var(--text-2)',fontSize:12,marginTop:4}}>failing arms detected</div>
          {metrics?.failing_arms?.slice(0,3).map((fa,i) => (
            <div key={i} style={{marginTop:8,padding:'6px 10px',background:'rgba(240,80,112,0.08)',
                                  borderRadius:6,fontSize:12,color:'var(--red)'}}>
              {fa.intervention_type.replace('_',' ')} · user {fa.user_id.slice(0,8)}
            </div>
          ))}
        </div>

        <div className="card">
          <div className="section-title">Negative Feedback Rate</div>
          <div style={{fontSize:28,fontFamily:'var(--font-mono)',fontWeight:700,
                       color: (metrics?.negative_rate_7d || 0) > 0.2 ? 'var(--red)' : 'var(--green)'}}>
            {metrics ? `${(metrics.negative_rate_7d * 100).toFixed(1)}%` : '—'}
          </div>
          <div style={{color:'var(--text-2)',fontSize:12,marginTop:4}}>7-day window · threshold 20%</div>
          <div style={{marginTop:12,height:4,background:'var(--bg-3)',borderRadius:2}}>
            <div style={{height:'100%',borderRadius:2,
                          background: (metrics?.negative_rate_7d || 0) > 0.2 ? 'var(--red)' : 'var(--green)',
                          width:`${Math.min(100,(metrics?.negative_rate_7d||0)*500)}%`}} />
          </div>
        </div>

        <div className="card">
          <div className="section-title">Quick Actions</div>
          <div style={{display:'flex',flexDirection:'column',gap:8}}>
            <a href="/api/v1/monitoring/health" target="_blank" className="btn btn-ghost btn-sm" style={{justifyContent:'center'}}>
              API Health Check
            </a>
            <a href="http://localhost:8000/docs" target="_blank" className="btn btn-ghost btn-sm" style={{justifyContent:'center'}}>
              Swagger UI
            </a>
            <a href="/monitoring" className="btn btn-primary btn-sm" style={{justifyContent:'center'}}>
              View Full Monitoring
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
