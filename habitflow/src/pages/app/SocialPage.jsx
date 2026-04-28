import { useEffect, useState } from 'react'
import { social } from '../../utils/api'
import { useToast } from '../../components/ui/Toast'
import { useStore } from '../../store'
import { formatDistanceToNow } from 'date-fns'

function Avatar({ name, color, size = 36 }) {
  return (
    <div className="avatar" style={{ width:size, height:size, background:color, fontSize:size*0.38 }}>
      {(name||'?').slice(0,2).toUpperCase()}
    </div>
  )
}

function FeedItem({ item, onLike }) {
  return (
    <div className="card" style={{ marginBottom:10, padding:'14px 16px' }}>
      <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:10 }}>
        <Avatar name={item.user.display_name} color={item.user.avatar_color} />
        <div>
          <div style={{ fontWeight:600, fontSize:13 }}>{item.user.display_name}</div>
          <div style={{ fontSize:11, color:'var(--text3)' }}>@{item.user.username} · {formatDistanceToNow(new Date(item.created_at), {addSuffix:true})}</div>
        </div>
      </div>
      <div style={{ fontSize:14, color:'var(--text)', marginBottom:10 }}>{item.content}</div>
      <button onClick={() => onLike(item.id)}
        style={{ background:'none', border:'1px solid var(--border)', borderRadius:20, padding:'5px 12px',
                 fontSize:12, cursor:'pointer', color: item.liked_by_me ? 'var(--coral)' : 'var(--text2)',
                 fontWeight: item.liked_by_me ? 600 : 400, transition:'all 0.15s' }}>
        {item.liked_by_me ? '♥' : '♡'} {item.likes_count}
      </button>
    </div>
  )
}

export default function SocialPage() {
  const [tab, setTab] = useState('feed')
  const [feed, setFeed] = useState([])
  const [discover, setDiscover] = useState([])
  const [searchQ, setSearchQ] = useState('')
  const [loading, setLoading] = useState(true)
  const { user } = useStore()
  const toast = useToast()

  useEffect(() => {
    if (tab === 'feed') {
      social.feed().then(setFeed).catch(console.error).finally(() => setLoading(false))
    } else {
      social.discover(searchQ).then(setDiscover).catch(console.error).finally(() => setLoading(false))
    }
  }, [tab, searchQ])

  const onLike = async (id) => {
    try {
      const res = await social.like(id)
      setFeed(p => p.map(f => f.id === id ? { ...f, liked_by_me: res.liked, likes_count: f.likes_count + (res.liked ? 1 : -1) } : f))
    } catch (e) {}
  }

  const onFollow = async (uid, isFollowing) => {
    try {
      if (isFollowing) await social.unfollow(uid)
      else await social.follow(uid)
      setDiscover(p => p.map(u => u.id === uid ? { ...u, is_following: !isFollowing } : u))
      toast(isFollowing ? 'Unfollowed' : 'Following!', 'success')
    } catch (e) { toast(e.detail || 'Error', 'error') }
  }

  return (
    <div className="page">
      <div style={{ padding:'20px 20px 16px' }}>
        <h1 style={{ fontFamily:'var(--font-display)', fontSize:24, fontWeight:800 }}>Community</h1>
      </div>

      {/* Tabs */}
      <div style={{ display:'flex', gap:8, padding:'0 20px', marginBottom:16 }}>
        {['feed','discover'].map(t => (
          <button key={t} onClick={() => setTab(t)}
            style={{ flex:1, padding:'10px', borderRadius:10, border:'1.5px solid', cursor:'pointer',
                     borderColor: tab===t ? 'var(--accent)' : 'var(--border)',
                     background: tab===t ? 'var(--accent-bg)' : 'var(--surface)',
                     color: tab===t ? 'var(--accent)' : 'var(--text2)',
                     fontWeight:600, fontSize:13, fontFamily:'var(--font-body)' }}>
            {t === 'feed' ? '📰 Feed' : '🔍 Discover'}
          </button>
        ))}
      </div>

      <div style={{ padding:'0 20px' }}>
        {tab === 'discover' && (
          <div style={{ marginBottom:12 }}>
            <input className="input" placeholder="Search users..." value={searchQ}
              onChange={e => setSearchQ(e.target.value)} />
          </div>
        )}

        {loading ? (
          <div className="loading"><span className="spinner"/></div>
        ) : tab === 'feed' ? (
          feed.length === 0 ? (
            <div className="empty-state">
              <div className="icon">👥</div>
              <div style={{ fontWeight:600, marginBottom:4 }}>Nothing here yet</div>
              <div>Follow people from Discover to see their activity</div>
            </div>
          ) : feed.map(item => <FeedItem key={item.id} item={item} onLike={onLike} />)
        ) : (
          discover.length === 0 ? (
            <div className="empty-state"><div className="icon">🔍</div><div>No users found</div></div>
          ) : discover.map(u => (
            <div key={u.id} className="card" style={{ display:'flex', alignItems:'center', gap:12, marginBottom:8, padding:'12px 14px' }}>
              <Avatar name={u.display_name} color={u.avatar_color} size={42} />
              <div style={{ flex:1 }}>
                <div style={{ fontWeight:600, fontSize:14 }}>{u.display_name}</div>
                <div style={{ fontSize:12, color:'var(--text2)' }}>@{u.username}</div>
                {u.current_streak > 0 && <div style={{ fontSize:11, color:'var(--coral)' }}>🔥 {u.current_streak} day streak</div>}
              </div>
              <button className={`btn btn-sm ${u.is_following ? 'btn-ghost' : 'btn-primary'}`}
                onClick={() => onFollow(u.id, u.is_following)}>
                {u.is_following ? 'Following' : 'Follow'}
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
