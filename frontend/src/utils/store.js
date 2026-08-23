// Zustand global store with Firebase auth support
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { v4 as uuidv4 } from 'uuid'

export const useStore = create(
  persist(
    (set, get) => ({
      learnerId: uuidv4(),
      user: null,             // Firebase user object
      profile: null,
      currentPath: null,
      mastery: {},
      chatHistory: [],
      quizQuestions: [],
      phase: 'landing',       // 'landing' | 'login' | 'onboarding' | 'dashboard'

      setLearnerId: (id) => set({ learnerId: id }),
      setUser: (user) => set({ user }),
      setProfile: (profile) => set({ profile }),
      setCurrentPath: (path) => set({ currentPath: path }),
      setMastery: (mastery) => set({ mastery }),
      updateMastery: (updates) => set((state) => ({ mastery: { ...state.mastery, ...updates } })),
      addChatMessage: (msg) => set((state) => ({ chatHistory: [...state.chatHistory, msg] })),
      setQuizQuestions: (qs) => set({ quizQuestions: qs }),
      setPhase: (phase) => set({ phase }),
      resetAll: () => set({
        profile: null,
        currentPath: null,
        mastery: {},
        chatHistory: [],
        quizQuestions: [],
        phase: 'landing',
        learnerId: uuidv4(),
      }),
    }),
    {
      name: 'nexis-store',
      partialize: (state) => ({
        learnerId: state.learnerId,
        profile: state.profile,
        mastery: state.mastery,
        currentPath: state.currentPath,
        // Only persist 'dashboard' phase — everything else resets to 'landing' on reload
        // so users are never stuck on login/onboarding screens after a refresh
        phase: state.phase === 'dashboard' ? 'dashboard' : 'landing',
      }),
    }
  )
)
