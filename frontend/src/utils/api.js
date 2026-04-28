import axios from 'axios'

const API_BASE = 'https://nudgeops-api.onrender.com'

const api = axios.create({ baseURL: `${API_BASE}/api/v1`, timeout: 10000 })

api.interceptors.response.use(
  res => res.data,
  err => Promise.reject(err?.response?.data || { detail: 'Network error' })
)

export const users = {
  list: (params) => api.get('/users/', { params }),
  get: (id) => api.get(`/users/${id}`),
  create: (data) => api.post('/users/', data),
  update: (id, data) => api.patch(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`),
}

export const events = {
  ingest: (data) => api.post('/events/', data),
  batchIngest: (data) => api.post('/events/batch', data),
  getForUser: (userId, params) => api.get(`/events/user/${userId}`, { params }),
}

export const bandit = {
  getNudge: (data) => api.post('/bandit/nudge', data),
  submitFeedback: (data) => api.post('/bandit/feedback', data),
  getState: (userId) => api.get(`/bandit/state/${userId}`),
}

export const interventions = {
  list: (params) => api.get('/interventions/', { params }),
  get: (id) => api.get(`/interventions/${id}`),
  getLogs: (id, params) => api.get(`/interventions/${id}/logs`, { params }),
}

export const policies = {
  list: () => api.get('/policies/'),
  get: (id) => api.get(`/policies/${id}`),
  create: (data) => api.post('/policies/', data),
  promote: (id) => api.post(`/policies/${id}/promote`),
  rollback: (id) => api.post(`/policies/${id}/rollback`),
  evaluate: (id, params) => api.get(`/policies/${id}/evaluate`, { params }),
}

export const experiments = {
  list: () => api.get('/experiments/'),
  create: (data) => api.post('/experiments/', data),
  start: (id) => api.post(`/experiments/${id}/start`),
  conclude: (id) => api.post(`/experiments/${id}/conclude`),
  results: (id) => api.get(`/experiments/${id}/results`),
}

export const monitoring = {
  metrics: () => api.get('/monitoring/metrics'),
  health: () => api.get('/monitoring/health'),
  fairness: () => api.get('/monitoring/fairness'),
}

export const features = {
  getForUser: (userId) => api.get(`/features/user/${userId}`),
  computeEmbedding: (userId) => api.post(`/features/user/${userId}/embedding`),
  similar: (userId, params) => api.get(`/features/user/${userId}/similar`, { params }),
}

export const audit = {
  list: (params) => api.get('/audit/', { params }),
}

export default api
