// Zustand global store
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { v4 as uuidv4 } from 'uuid'

export const useStore = create(
  persist(
    (set, get) => ({
      learnerId: uuidv4(),
      profile: null,
      currentPath: null,
      mastery: {},
      chatHistory: [],
      quizQuestions: [],
      phase: 'onboarding', // 'onboarding' | 'quiz' | 'dashboard'

      setProfile: (profile) => set({ profile }),
      setCurrentPath: (path) => set({ currentPath: path }),
      setMastery: (mastery) => set({ mastery }),
      updateMastery: (updates) => set((state) => ({ mastery: { ...state.mastery, ...updates } })),
      addChatMessage: (msg) => set((state) => ({ chatHistory: [...state.chatHistory, msg] })),
      setQuizQuestions: (qs) => set({ quizQuestions: qs }),
      setPhase: (phase) => set({ phase }),
      resetAll: () => set({ profile: null, currentPath: null, mastery: {}, chatHistory: [], phase: 'onboarding', learnerId: uuidv4() }),
    }),
    { name: 'nexis-store', partialize: (state) => ({ learnerId: state.learnerId, profile: state.profile, mastery: state.mastery }) }
  )
)
