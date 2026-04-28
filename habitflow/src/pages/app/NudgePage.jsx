import { useEffect, useState } from 'react'
import { nudge as nudgeApi } from '../../utils/api'
import { useToast } from '../../components/ui/Toast'
import NudgeCard from '../../components/nudge/NudgeCard'
import { format } from 'date-fns'

const SIGNAL_COLORS = { completed:'var(--green)', engaged:'var(--blue)', ignored:'var(--text3)', dismissed:'var(--amber)', negative:'var(--red)' }
const SIGNAL_ICONS = { completed:'✓', engaged:'👀', ignored:'—', dismissed:'✕', negative:'👎' }

export default function NudgePage() {
  const [current, setCurrent] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const toast = useToast()

  useEffect(() => {
    nudgeApi.history().then(setHistory).catch(console.error)
  }, [])

  const getNudge = async () => {
    setLoading(true)
    try { setCurrent(await nudgeApi.request()) }
    catch (e) { toast('Could not get nudge', 'error') }
    finally { setLoading(false) }
  }

  const onFeedback = async (signal) => {
    if (!current) return
    try {
      await nudgeApi.feedback(current.log_id, signal)
      toast(signal === 'completed' ? '🎉 Awesome!' : 'Feedback saved', 'success')
      const updated = await nudgeApi.history()
      setHistory(updated)
      setCurrent(null)
    } catch (e) {}
  }

  return (
    <div className="page">
      <div style={{ padding:'20px 20px 16px' }}>
        <h1 style={{ fontFamily:'var(--font-display)', fontSize:24, fontWeight:800 }}>Nudge Center</h1>
        <p style={{ color:'var(--text2)', fontSize:13, marginTop:2 }}>AI-personalized motivational nudges</p>
      </div>

      <div style={{ padding:'0 20px', marginBottom:20 }}>
        {current ? (
          <NudgeCard nudge={current} onFeedback={onFeedback} />
        ) : (
          <div className="card" style={{ textAlign:'center', padding:28 }}>
            <div style={{ fontSize:40, marginBottom:12 }}>✦</div>
            <div style={{ fontFamily:'var(--font-display)', fontSize:16, fontWeight:700, marginBottom:6 }}>Get a nudge</div>
            <div style={{ color:'var(--text2)', fontSize:13, marginBottom:16 }}>
              Your AI coach will pick the best strategy for you right now
            </div>
            <button className="btn btn-primary" onClick={getNudge} disabled={loading}>
              {loading ? <><span className="spinner"/> Thinking...</> : '✦ Get personalized nudge'}
            </button>
          </div>
        )}
      </div>

      {history.length > 0 && (
        <>
          <div className="section-header">
            <div className="section-title">History</div>
          </div>
          <div style={{ padding:'0 20px' }}>
            {history.map(h => (
              <div key={h.id} className="card" style={{ marginBottom:8, padding:'12px 14px' }}>
                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:4 }}>
                  <span style={{ fontSize:11, color:'var(--text3)', fontFamily:'var(--font-mono)' }}>
                    {h.intervention_type?.slice(0,20)}
                  </span>
                  {h.feedback_signal && (
                    <span style={{ fontSize:12, fontWeight:600, color: SIGNAL_COLORS[h.feedback_signal] }}>
                      {SIGNAL_ICONS[h.feedback_signal]} {h.feedback_signal}
                    </span>
                  )}
                </div>
                <div style={{ fontSize:13, color:'var(--text)', marginBottom:4 }}>{h.message}</div>
                <div style={{ fontSize:11, color:'var(--text3)' }}>
                  {h.delivered_at ? format(new Date(h.delivered_at), 'MMM d, h:mm a') : ''}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
