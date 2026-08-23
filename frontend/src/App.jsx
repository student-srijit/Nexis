import React from 'react'
import { Toaster } from 'react-hot-toast'
import { useStore } from './utils/store'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'

export default function App() {
  const { phase } = useStore()

  return (
    <>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: 'var(--bg-card)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-accent)',
            borderRadius: '12px',
            fontSize: '0.875rem',
          },
          success: { iconTheme: { primary: '#10b981', secondary: 'white' } },
          error: { iconTheme: { primary: '#ef4444', secondary: 'white' } },
        }}
      />
      {phase === 'dashboard' ? <Dashboard /> : <Onboarding />}
    </>
  )
}
