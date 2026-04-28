import { useState } from 'react'
import { habits as habitsApi, categories } from '../../utils/api'
import { useToast } from '../ui/Toast'
import { useEffect } from 'react'

const ICONS = ['✅','💪','📚','🧘','💧','🚶','🥗','😴','🎯','🎸','✍️','🏃','🧹','💊','🌿','📖','🎨','🧠','💡','🌅']
const COLORS = ['#6ee7b7','#60a5fa','#a78bfa','#fb7185','#fbbf24','#34d399','#f97316','#e879f9','#2d6a4f','#457b9d']
const DAYS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']

export default function AddHabitModal({ onClose, onSaved }) {
  const [form, setForm] = useState({
    name:'', description:'', icon:'✅', color:'#6ee7b7',
    frequency:'daily', target_days:[0,1,2,3,4,5,6], is_public:false,
    category_id:null, reminder_time:''
  })
  const [cats, setCats] = useState([])
  const [loading, setLoading] = useState(false)
  const toast = useToast()

  useEffect(() => { categories.list().then(setCats).catch(() => {}) }, [])

  const save = async () => {
    if (!form.name.trim()) { toast('Name is required', 'error'); return }
    setLoading(true)
    try {
      const h = await habitsApi.create({ ...form, reminder_time: form.reminder_time || null })
      toast('Habit created! 🌱', 'success')
      onSaved(h)
    } catch (e) { toast(e.detail || 'Error', 'error') }
    finally { setLoading(false) }
  }

  const toggleDay = (d) => setForm(p => ({
    ...p, target_days: p.target_days.includes(d) ? p.target_days.filter(x => x !== d) : [...p.target_days, d]
  }))

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-sheet" onClick={e => e.stopPropagation()}>
        <div className="modal-handle"/>
        <div className="modal-title">New habit</div>

        <div className="input-group">
          <label className="input-label">Name *</label>
          <input className="input" placeholder="e.g. Morning meditation" value={form.name}
            onChange={e => setForm(p => ({ ...p, name: e.target.value }))} />
        </div>

        <div className="input-group">
          <label className="input-label">Description</label>
          <input className="input" placeholder="Optional details..." value={form.description}
            onChange={e => setForm(p => ({ ...p, description: e.target.value }))} />
        </div>

        <div style={{ marginBottom:14 }}>
          <label className="input-label">Icon</label>
          <div style={{ display:'flex', flexWrap:'wrap', gap:8, marginTop:6 }}>
            {ICONS.map(icon => (
              <button key={icon} onClick={() => setForm(p => ({ ...p, icon }))}
                style={{ width:36, height:36, borderRadius:10, border:`2px solid ${form.icon===icon?'var(--accent)':'var(--border)'}`,
                         background: form.icon===icon?'var(--accent-bg)':'var(--surface)', fontSize:18, cursor:'pointer' }}>
                {icon}
              </button>
            ))}
          </div>
        </div>

        <div style={{ marginBottom:14 }}>
          <label className="input-label">Color</label>
          <div style={{ display:'flex', gap:8, marginTop:6 }}>
            {COLORS.map(c => (
              <div key={c} onClick={() => setForm(p => ({ ...p, color:c }))}
                style={{ width:28, height:28, borderRadius:'50%', background:c, cursor:'pointer',
                         border: form.color===c?'3px solid var(--text)':'3px solid transparent' }} />
            ))}
          </div>
        </div>

        <div className="input-group">
          <label className="input-label">Frequency</label>
          <select className="input" value={form.frequency} onChange={e => setForm(p => ({ ...p, frequency:e.target.value }))}>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="custom">Custom days</option>
          </select>
        </div>

        {form.frequency === 'custom' && (
          <div style={{ marginBottom:14 }}>
            <label className="input-label">Days</label>
            <div style={{ display:'flex', gap:6, marginTop:6 }}>
              {DAYS.map((d,i) => (
                <button key={i} onClick={() => toggleDay(i)}
                  style={{ flex:1, padding:'7px 0', borderRadius:8, border:'1.5px solid',
                           borderColor: form.target_days.includes(i)?'var(--accent)':'var(--border)',
                           background: form.target_days.includes(i)?'var(--accent-bg)':'var(--surface)',
                           color: form.target_days.includes(i)?'var(--accent)':'var(--text2)',
                           fontSize:11, fontWeight:600, cursor:'pointer' }}>
                  {d}
                </button>
              ))}
            </div>
          </div>
        )}

        {cats.length > 0 && (
          <div className="input-group">
            <label className="input-label">Category</label>
            <select className="input" value={form.category_id || ''} onChange={e => setForm(p => ({ ...p, category_id: e.target.value || null }))}>
              <option value="">No category</option>
              {cats.map(c => <option key={c.id} value={c.id}>{c.icon} {c.name}</option>)}
            </select>
          </div>
        )}

        <div className="input-group">
          <label className="input-label">Reminder time (optional)</label>
          <input className="input" type="time" value={form.reminder_time}
            onChange={e => setForm(p => ({ ...p, reminder_time:e.target.value }))} />
        </div>

        <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:20 }}>
          <input type="checkbox" id="pub" checked={form.is_public}
            onChange={e => setForm(p => ({ ...p, is_public:e.target.checked }))} />
          <label htmlFor="pub" style={{ fontSize:13, cursor:'pointer', color:'var(--text2)' }}>
            Share completions on feed
          </label>
        </div>

        <button className="btn btn-primary btn-full" onClick={save} disabled={loading}>
          {loading ? <><span className="spinner"/> Creating...</> : 'Create habit'}
        </button>
      </div>
    </div>
  )
}
