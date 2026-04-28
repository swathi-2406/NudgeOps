import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { habits as habitsApi, nudge as nudgeApi } from '../../utils/api'
import { useStore } from '../../store'
import { useToast } from '../../components/ui/Toast'
import { format } from 'date-fns'
import AddHabitModal from '../../components/habits/AddHabitModal'
import NudgeCard from '../../components/nudge/NudgeCard'

export default function HomePage() {
  const { user } = useStore()
  const [habitList, setHabitList] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [nudgeData, setNudgeData] = useState(null)
  const [nudgeLoading, setNudgeLoading] = useState(false)
  const [streak, setStreak] = useState(user?.current_streak || 0)
  const toast = useToast()
  const today = format(new Date(), 'yyyy-MM-dd')
  const dayName = format(new Date(), 'EEEE')
  const dateStr = format(new Date(), 'MMMM d')

  const loadHabits = useCallback(async () => {
    try {
      const data = await habitsApi.list()
      setHabitList(data)
    } catch (e) { toast('Failed to load habits', 'error') }
    finally { setLoading(false) }
  }, [])

  useEffect(() => {
  loadHabits()
  autoNudge()
}, [loadHabits])

  const toggleHabit = async (habit) => {
    if (habit.completed_today) {
      try {
        await habitsApi.uncomplete(habit.id, today)
        setHabitList(p => p.map(h => h.id === habit.id ? { ...h, completed_today: false } : h))
      } catch (e) { toast('Error', 'error') }
    } else {
      try {
        const res = await habitsApi.complete(habit.id, { completed_date: today })
        setHabitList(p => p.map(h => h.id === habit.id ? { ...h, completed_today: true } : h))
        setStreak(res.current_streak)
        if (res.current_streak > 0 && res.current_streak % 7 === 0)
          toast(`🔥 ${res.current_streak} day streak!`, 'success')
        else toast(`✓ ${habit.name} done!`, 'success')
      } catch (e) { toast(e.detail || 'Error', 'error') }
    }
  }

  const getNudge = async () => {
  setNudgeLoading(true)
  try {
    const data = await nudgeApi.request()
    setNudgeData(data)
  } catch (e) { toast('Could not get nudge', 'error') }
  finally { setNudgeLoading(false) }
}

const autoNudge = async () => {
  const lastNudgeDate = localStorage.getItem('hf_last_nudge_date')
  const today = format(new Date(), 'yyyy-MM-dd')
  if (lastNudgeDate === today) return
  await new Promise(r => setTimeout(r, 1500))
  try {
    const data = await nudgeApi.request()
    setNudgeData(data)
    localStorage.setItem('hf_last_nudge_date', today)
  } catch (e) {}
}

  const onFeedback = async (signal) => {
    if (!nudgeData) return
    try {
      await nudgeApi.feedback(nudgeData.log_id, signal)
      toast(signal === 'completed' ? '🎉 Great job!' : 'Feedback recorded', 'success')
      setNudgeData(null)
    } catch (e) {}
  }

  const doneCount = habitList.filter(h => h.completed_today).length
  const totalCount = habitList.length

  return (
    <div className="page">
      {/* Header */}
      <div style={{ padding:'20px 20px 0', marginBottom:20 }}>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start' }}>
          <div>
            <div style={{ fontSize:13, color:'var(--text2)', marginBottom:2 }}>{dayName}, {dateStr}</div>
            <h1 style={{ fontFamily:'var(--font-display)', fontSize:24, fontWeight:800 }}>
              Hey, {user?.display_name?.split(' ')[0]} 👋
            </h1>
          </div>
          <div style={{ display:'flex', alignItems:'center', gap:6, background:'var(--surface)', border:'1px solid var(--border)', borderRadius:12, padding:'6px 12px' }}>
            <span style={{ fontSize:16 }}>🔥</span>
            <span style={{ fontFamily:'var(--font-display)', fontWeight:800, fontSize:18 }}>{streak}</span>
          </div>
        </div>

        {/* Progress bar */}
        {totalCount > 0 && (
          <div style={{ marginTop:16 }}>
            <div style={{ display:'flex', justifyContent:'space-between', fontSize:12, color:'var(--text2)', marginBottom:6 }}>
              <span>{doneCount}/{totalCount} habits today</span>
              <span>{Math.round(doneCount/totalCount*100)}%</span>
            </div>
            <div style={{ height:6, background:'var(--bg2)', borderRadius:3, overflow:'hidden' }}>
              <div style={{ height:'100%', background:'var(--accent)', borderRadius:3, width:`${totalCount > 0 ? doneCount/totalCount*100 : 0}%`, transition:'width 0.4s ease' }} />
            </div>
          </div>
        )}
      </div>

      {/* Nudge section */}
      <div style={{ padding:'0 20px', marginBottom:20 }}>
        {nudgeData ? (
          <NudgeCard nudge={nudgeData} onFeedback={onFeedback} />
        ) : (
          <button onClick={getNudge} disabled={nudgeLoading}
            style={{ width:'100%', padding:'14px', borderRadius:16, border:'1.5px dashed var(--border2)',
                     background:'transparent', cursor:'pointer', color:'var(--accent)',
                     fontFamily:'var(--font-display)', fontSize:14, fontWeight:700,
                     display:'flex', alignItems:'center', justifyContent:'center', gap:8 }}>
            {nudgeLoading ? <><span className="spinner"/> Getting your nudge...</> : <>✦ Get AI nudge</>}
          </button>
        )}
      </div>

      {/* Habits list */}
      <div className="section-header">
        <div className="section-title">Today's habits</div>
        <button className="btn btn-sm btn-ghost" onClick={() => setShowAdd(true)}>+ Add</button>
      </div>

      <div style={{ padding:'0 20px' }}>
        {loading ? (
          <div className="loading"><span className="spinner" /></div>
        ) : habitList.length === 0 ? (
          <div className="empty-state">
            <div className="icon">🌱</div>
            <div style={{ fontWeight:600, marginBottom:4 }}>No habits yet</div>
            <div>Add your first habit to get started</div>
            <button className="btn btn-primary btn-sm" style={{ marginTop:16 }} onClick={() => setShowAdd(true)}>Add habit</button>
          </div>
        ) : (
          habitList.map(h => (
            <div key={h.id} className={`habit-item ${h.completed_today ? 'done' : ''}`} onClick={() => toggleHabit(h)}>
              <div className="habit-icon-wrap" style={{ background: h.color + '22' }}>{h.icon}</div>
              <div style={{ flex:1 }}>
                <div style={{ fontWeight:600, fontSize:14, textDecoration: h.completed_today ? 'line-through' : 'none', color: h.completed_today ? 'var(--text2)' : 'var(--text)' }}>{h.name}</div>
                {h.description && <div style={{ fontSize:11, color:'var(--text3)', marginTop:1 }}>{h.description}</div>}
              </div>
              <div className="habit-check">
                {h.completed_today && <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 6l3 3 5-5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>}
              </div>
            </div>
          ))
        )}
      </div>

      {showAdd && <AddHabitModal onClose={() => setShowAdd(false)} onSaved={(h) => { setHabitList(p => [...p, h]); setShowAdd(false) }} />}
    </div>
  )
}
