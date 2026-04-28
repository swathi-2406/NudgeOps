const TYPE_LABELS = {
  streak_tracker:'Streak Tracker', public_accountability:'Public Accountability',
  dark_humor_reminder:'Dark Humor', loss_framing:'Loss Framing',
  positive_reinforcement:'Positive Reinforcement', social_proof:'Social Proof',
  implementation_intention:'Implementation', progress_visualization:'Progress',
  commitment_device:'Commitment', micro_challenge:'Micro Challenge',
}
const TYPE_COLORS = {
  streak_tracker:'#f97316', loss_framing:'#e63946', positive_reinforcement:'#2d6a4f',
  dark_humor_reminder:'#7b5ea7', social_proof:'#457b9d', micro_challenge:'#e9c46a',
}

export default function NudgeCard({ nudge, onFeedback }) {
  const color = TYPE_COLORS[nudge.intervention_type] || '#2d6a4f'
  const label = TYPE_LABELS[nudge.intervention_type] || nudge.intervention_type

  return (
    <div style={{ background:`linear-gradient(135deg, ${color}11, ${color}08)`,
                  border:`1.5px solid ${color}33`, borderRadius:20, padding:18 }}>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:10 }}>
        <span style={{ fontSize:11, fontWeight:600, color, background:`${color}18`, padding:'3px 10px', borderRadius:20 }}>
          ✦ {label}
        </span>
        <span style={{ fontSize:10, color:'var(--text3)', fontFamily:'var(--font-mono)' }}>
          {nudge.selection_reason}
        </span>
      </div>
      <div style={{ fontSize:15, fontWeight:600, color:'var(--text)', lineHeight:1.5, marginBottom:14 }}>
        {nudge.message}
      </div>
      <div style={{ display:'flex', gap:8 }}>
        <button onClick={() => onFeedback('completed')}
          style={{ flex:2, padding:'10px', borderRadius:12, border:'none', background:'var(--accent)', color:'white',
                   fontFamily:'var(--font-body)', fontSize:13, fontWeight:700, cursor:'pointer' }}>
          ✓ Done it!
        </button>
        <button onClick={() => onFeedback('engaged')}
          style={{ flex:1, padding:'10px', borderRadius:12, border:'1px solid var(--border)', background:'var(--surface)',
                   color:'var(--text2)', fontFamily:'var(--font-body)', fontSize:13, cursor:'pointer' }}>
          Maybe
        </button>
        <button onClick={() => onFeedback('dismissed')}
          style={{ flex:1, padding:'10px', borderRadius:12, border:'1px solid var(--border)', background:'var(--surface)',
                   color:'var(--text2)', fontFamily:'var(--font-body)', fontSize:13, cursor:'pointer' }}>
          Skip
        </button>
      </div>
      <div style={{ display:'flex', gap:6, marginTop:8 }}>
        <button onClick={() => onFeedback('ignored')}
          style={{ flex:1, padding:'7px', borderRadius:9, border:'1px solid var(--border)', background:'transparent',
                   color:'var(--text3)', fontSize:11, cursor:'pointer', fontFamily:'var(--font-body)' }}>
          Ignore
        </button>
        <button onClick={() => onFeedback('negative')}
          style={{ flex:1, padding:'7px', borderRadius:9, border:'1px solid rgba(230,57,70,0.2)', background:'transparent',
                   color:'var(--red)', fontSize:11, cursor:'pointer', fontFamily:'var(--font-body)' }}>
          Not helpful
        </button>
      </div>
    </div>
  )
}
