import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      habits: [],
      streak: 0,
      setUser: (user) => set({ user }),
      setToken: (token) => {
        localStorage.setItem('hf_token', token)
        set({ token })
      },
      setHabits: (habits) => set({ habits }),
      setStreak: (streak) => set({ streak }),
      logout: () => {
        localStorage.removeItem('hf_token')
        set({ user: null, token: null, habits: [] })
      },
      updateHabit: (id, updates) => set(state => ({
        habits: state.habits.map(h => h.id === id ? { ...h, ...updates } : h)
      })),
    }),
    { name: 'habitflow', partialize: s => ({ user: s.user, token: s.token }) }
  )
)
