import { useEffect, useState } from 'react'
import { stats as statsApi } from '../../utils/api'
import { format, subDays } from 'date-fns'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

export default function StatsPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    statsApi.get().then(setData).catch(console.error).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading"><span className="spinner"/></div>
  if (!data) return <div className="empty-state"><div className="icon">📊</div><div>No stats yet</div></div>

  // Build last 30 days heatmap
  const today = new Date()
  const days = Array.from({ length: 30 }, (_, i) => {
    const d = subDays(today, 29 - i)
    const key = format(d, 'yyyy-MM-dd')
    return { date: key, label: format(d, 'EEE'), count: data.heatmap?.[key] || 0 }
  })

  const maxCount = Math.max(...days.map(d => d.count), 1)

  return (
    <div className="page">
      <div style={{ padding:'20px 20px 16px' }}>
        <h1 style={{ fontFamily:'var(--font-display)', fontSize:24, fontWeight:800 }}>Your Progress</h1>
      </div>

      {/* Big stats */}
      <div style={{ padding:'0 20px', display:'grid', gridTemplateColumns:'1fr 1fr', gap:10, marginBottom:16 }}>
        {[
          { label:'Current streak', value:`${data.current_streak} 🔥`, color:'var(--coral)' },
          { label:'Longest streak', value:`${data.longest_streak} days`, color:'var(--accent)' },
          { label:'Total completions', value:data.total_completions, color:'var(--blue)' },
          { label:'Active habits', value:data.active_habits, color:'var(--purple)' },
        ].map(s => (
          <div key={s.label} className="card">
            <div style={{ fontSize:11, color:'var(--text2)', marginBottom:4 }}>{s.label}</div>
            <div style={{ fontFamily:'var(--font-display)', fontSize:22, fontWeight:800, color:s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Activity heatmap */}
      <div style={{ padding:'0 20px', marginBottom:16 }}>
        <div className="card">
          <div style={{ fontFamily:'var(--font-display)', fontWeight:700, marginBottom:14 }}>30-day activity</div>
          <div style={{ display:'flex', flexWrap:'wrap', gap:4 }}>
            {days.map(d => (
              <div key={d.date} title={`${d.date}: ${d.count} completions`}
                style={{ width:20, height:20, borderRadius:4,
                         background: d.count === 0 ? 'var(--bg2)' : `rgba(45,106,79,${0.2 + (d.count/maxCount)*0.8})`,
                         border:'1px solid var(--border)' }} />
            ))}
          </div>
          <div style={{ display:'flex', gap:8, marginTop:10, alignItems:'center' }}>
            <span style={{ fontSize:11, color:'var(--text3)' }}>Less</span>
            {[0.1,0.3,0.6,0.9].map(o => (
              <div key={o} style={{ width:16, height:16, borderRadius:3, background:`rgba(45,106,79,${o})` }} />
            ))}
            <span style={{ fontSize:11, color:'var(--text3)' }}>More</span>
          </div>
        </div>
      </div>

      {/* Nudge effectiveness */}
      <div style={{ padding:'0 20px', marginBottom:16 }}>
        <div className="card">
          <div style={{ fontFamily:'var(--font-display)', fontWeight:700, marginBottom:12 }}>Nudge effectiveness</div>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:10 }}>
            <div>
              <div style={{ fontSize:11, color:'var(--text2)' }}>Total nudges received</div>
              <div style={{ fontFamily:'var(--font-display)', fontSize:22, fontWeight:800, color:'var(--accent)' }}>{data.total_nudges}</div>
            </div>
            <div>
              <div style={{ fontSize:11, color:'var(--text2)' }}>Completion rate</div>
              <div style={{ fontFamily:'var(--font-display)', fontSize:22, fontWeight:800, color:'var(--green)' }}>
                {data.total_nudges > 0 ? `${(data.nudge_completion_rate * 100).toFixed(0)}%` : '—'}
              </div>
            </div>
          </div>
          {data.total_nudges > 0 && (
            <div style={{ marginTop:12 }}>
              <div style={{ height:6, background:'var(--bg2)', borderRadius:3, overflow:'hidden' }}>
                <div style={{ height:'100%', background:'var(--accent)', borderRadius:3, width:`${data.nudge_completion_rate*100}%` }} />
              </div>
              <div style={{ fontSize:11, color:'var(--text3)', marginTop:6 }}>
                Powered by NudgeOps Thompson Sampling bandit
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Weekly bar chart */}
      <div style={{ padding:'0 20px' }}>
        <div className="card">
          <div style={{ fontFamily:'var(--font-display)', fontWeight:700, marginBottom:12 }}>Last 7 days</div>
          <ResponsiveContainer width="100%" height={120}>
            <BarChart data={days.slice(-7)} barSize={24}>
              <XAxis dataKey="label" tick={{ fontSize:11, fill:'var(--text2)' }} axisLine={false} tickLine={false} />
              <YAxis hide />
              <Tooltip contentStyle={{ background:'var(--surface)', border:'1px solid var(--border)', borderRadius:8, fontSize:12 }} />
              <Bar dataKey="count" radius={[4,4,0,0]}>
                {days.slice(-7).map((d,i) => (
                  <Cell key={i} fill={d.count > 0 ? 'var(--accent)' : 'var(--bg2)'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
