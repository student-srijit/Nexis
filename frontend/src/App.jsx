import React, { useEffect } from 'react'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './utils/AuthContext'
import { useStore } from './utils/store'
import { motion, AnimatePresence } from 'framer-motion'
import { Brain } from 'lucide-react'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'
import { getUserPath, getUserProfile } from './utils/firebase'

const TOAST_STYLE = {
  style: {
    background: 'var(--bg-card)',
    color: 'var(--text-primary)',
    border: '1px solid var(--border-accent)',
    borderRadius: '12px',
    fontSize: '0.875rem',
  },
  success: { iconTheme: { primary: '#10b981', secondary: 'white' } },
  error: { iconTheme: { primary: '#ef4444', secondary: 'white' } },
}

function AppInner() {
  const { user, authLoading } = useAuth()
  const { phase, setPhase, learnerId, setLearnerId, setCurrentPath, setProfile, setMastery, currentPath } = useStore()

  // When a Firebase user signs in, use their UID as the learner ID
  // and load their existing data from Firestore
  useEffect(() => {
    // If we have a stored path already (e.g. from previous session) — go straight to dashboard
    if (currentPath?.steps?.length > 0 && phase !== 'dashboard') {
      setPhase('dashboard')
    }
  }, [])

  useEffect(() => {
    if (!user) return
    if (user.uid !== learnerId) {
      setLearnerId(user.uid)
    }
    // Try to restore from Firestore
    const restore = async () => {
      try {
        const [savedPath, savedProfile] = await Promise.all([
          getUserPath(user.uid),
          getUserProfile(user.uid),
        ])
        if (savedProfile) setProfile(savedProfile)
        const currentPhase = useStore.getState().phase
        
        if (savedPath?.steps?.length > 0) {
          setCurrentPath(savedPath)
          setPhase('dashboard')
        } else if (currentPhase === 'landing' || currentPhase === 'login') {
          setPhase('onboarding')
        }
      } catch (_) {
        // Firestore unavailable — continue with local state
        const currentPhase = useStore.getState().phase
        if (currentPhase === 'landing' || currentPhase === 'login') {
          setPhase('onboarding')
        }
      }
    }
    restore()
  }, [user])

  // Full screen loading spinner while Firebase checks auth state
  if (authLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '16px', background: 'var(--bg-primary)' }}>
        <motion.div animate={{ rotate: 360 }} transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}>
          <Brain size={40} color="var(--accent-purple-light)" />
        </motion.div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Loading Nexis…</p>
      </div>
    )
  }

  return (
    <AnimatePresence mode="wait">
      {phase === 'landing' && (
        <motion.div key="landing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <Landing onGetStarted={() => setPhase('login')} />
        </motion.div>
      )}
      {phase === 'login' && (
        <motion.div key="login" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <Login onBack={() => setPhase('landing')} />
        </motion.div>
      )}
      {phase === 'onboarding' && (
        <motion.div key="onboarding" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <Onboarding />
        </motion.div>
      )}
      {phase === 'dashboard' && (
        <motion.div key="dashboard" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <Dashboard />
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <Toaster position="top-right" toastOptions={TOAST_STYLE} />
      <AppInner />
    </AuthProvider>
  )
}
