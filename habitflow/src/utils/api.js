import axios from 'axios'

const http = axios.create({ baseURL: 'http://localhost:8000/api/v1/habitflow', timeout: 10000 })

http.interceptors.request.use(cfg => {
  const token = localStorage.getItem('hf_token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

http.interceptors.response.use(
  r => r.data,
  err => Promise.reject(err?.response?.data || { detail: 'Network error' })
)

export const auth = {
  signup: d => http.post('/auth/signup', d),
  login:  d => http.post('/auth/login', d),
  me:     ()=> http.get('/auth/me'),
}
export const habits = {
  list:     ()         => http.get('/habits'),
  create:   d          => http.post('/habits', d),
  update:   (id, d)    => http.patch(`/habits/${id}`, d),
  delete:   id         => http.delete(`/habits/${id}`),
  complete: (id, d)    => http.post(`/habits/${id}/complete`, d),
  uncomplete:(id, date)=> http.delete(`/habits/${id}/complete/${date}`),
  history:  (id, days) => http.get(`/habits/${id}/history?days=${days||90}`),
  range:    (s,e)      => http.get(`/habits/completions/range?start=${s}&end=${e}`),
}
export const nudge = {
  request:  ()        => http.post('/nudge/request'),
  feedback: (id, sig) => http.post(`/nudge/feedback?log_id=${id}&signal=${sig}`),
  history:  ()        => http.get('/nudge/history'),
}
export const stats = { get: () => http.get('/stats') }
export const social = {
  feed:     ()     => http.get('/social/feed'),
  discover: q      => http.get(`/social/discover${q?`?q=${q}`:''}` ),
  follow:   id     => http.post(`/social/follow/${id}`),
  unfollow: id     => http.delete(`/social/follow/${id}`),
  like:     id     => http.post(`/social/like/${id}`),
  profile:  name   => http.get(`/social/profile/${name}`),
}
export const categories = { list: () => http.get('/categories') }
export default http
