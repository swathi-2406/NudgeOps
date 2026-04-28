import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { habits as habitsApi } from '../../utils/api'
import { useToast } from '../../components/ui/Toast'
import { format, subDays } from 'date-fns'
import { BarChart, Bar, XAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

export default function HabitDetailPage() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  const toast = useToast()

  useEffect(() => {
    habitsApi.history(id, 90).then(setData).catch(e => { toast('Error loading habit', 'error'); navigate('/') })
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="loading"><span className="spinner"/></div>
  if (!data) return null

  const { habit, completions, completion_rate, total } = data

  // Build 30-day chart
  const completedDates = new Set(completions.map(c => c.date))
  const chartData = Array.from({ length: 30 }, (_, i) => {
    const d = subDays(new Date(), 29 - i)
    const key = format(d, 'yyyy-MM-dd')
    return { day: format(d, 'dd'), done: completedDates.has(key) ? 1 : 0, date: key }
  })

  return (
    <div className="page">
      <div style={{ padding:'20px 20px 0' }}>
        <button onClick={() => navigate('/')} style={{ background:'none', border:'none', color:'var(--accent)', cursor:'pointer', fontSize:14, fontWeight:600, marginBottom:16 }}>← Back</button>

        <div style={{ display:'flex', alignItems:'center', gap:14, marginBottom:20 }}>
          <div style={{ width:56, height:56, borderRadius:16, background:habit.color+'22', display:'flex', alignItems:'center', justifyContent:'center', fontSize:28 }}>{habit.icon}</div>
          <div>
            <h1 style={{ fontFamily:'var(--font-display)', fontSize:22, fontWeight:800 }}>{habit.name}</h1>
            {habit.description && <div style={{ color:'var(--text2)', fontSize:13 }}>{habit.description}</div>}
          </div>
        </div>

        {/* Stats */}
        <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:10, marginBottom:20 }}>
          {[
            { label:'Completions', val:total },
            { label:'Rate (90d)', val:`${Math.round(completion_rate*100)}%` },
            { label:'Frequency', val:habit.frequency },
          ].map(s => (
            <div key={s.label} className="card" style={{ textAlign:'center' }}>
              <div style={{ fontFamily:'var(--font-display)', fontSize:18, fontWeight:800, color:'var(--accent)' }}>{s.val}</div>
              <div style={{ fontSize:11, color:'var(--text2)' }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* 30-day chart */}
        <div className="card" style={{ marginBottom:20 }}>
          <div style={{ fontFamily:'var(--font-display)', fontWeight:700, marginBottom:12 }}>Last 30 days</div>
          <ResponsiveContainer width="100%" height={80}>
            <BarChart data={chartData} barSize={8}>
              <XAxis dataKey="day" tick={{ fontSize:9, fill:'var(--text3)' }} axisLine={false} tickLine={false} interval={4} />
              <Tooltip contentStyle={{ background:'var(--surface)', border:'1px solid var(--border)', borderRadius:8, fontSize:11 }}
                formatter={(v) => [v ? 'Done ✓' : 'Missed', '']} />
              <Bar dataKey="done" radius={[3,3,0,0]}>
                {chartData.map((d,i) => <Cell key={i} fill={d.done ? habit.color || 'var(--accent)' : 'var(--bg2)'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Recent completions */}
        <div className="section-header" style={{ padding:0, marginBottom:12 }}>
          <div className="section-title">Recent completions</div>
        </div>
        {completions.slice(0,20).map(c => (
          <div key={c.date} className="card" style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:8, padding:'10px 14px' }}>
            <div style={{ display:'flex', alignItems:'center', gap:10 }}>
              <span style={{ fontSize:16 }}>✅</span>
              <span style={{ fontWeight:600, fontSize:13 }}>{format(new Date(c.date+'T12:00:00'), 'MMMM d, yyyy')}</span>
            </div>
            {c.mood && <span>{'⭐'.repeat(c.mood)}</span>}
          </div>
        ))}
        {completions.length === 0 && (
          <div className="empty-state"><div className="icon">{habit.icon}</div><div>No completions yet. You got this!</div></div>
        )}
      </div>
    </div>
  )
}
