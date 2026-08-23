import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Brain, Zap, ArrowLeft, Loader2 } from 'lucide-react'
import { signInWithGoogle, isFirebaseConfigured } from '../utils/firebase'
import toast from 'react-hot-toast'

// Inline Google icon SVG
const GoogleIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
  </svg>
)

export default function Login({ onBack }) {
  const [loading, setLoading] = useState(false)

  const handleGoogleSignIn = async () => {
    setLoading(true)
    try {
      await signInWithGoogle()
      // AuthContext will detect the user and App.jsx will redirect
    } catch (err) {
      toast.error('Sign-in failed: ' + (err.message || 'Unknown error'))
      setLoading(false)
    }
  }

  const handleContinueWithoutAuth = () => {
    onBack() // just go to onboarding without auth
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--gradient-hero)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '24px', position: 'relative', overflow: 'hidden',
    }}>
      {/* Background orbs */}
      <div style={{ position: 'fixed', top: '15%', left: '10%', width: 400, height: 400, borderRadius: '50%', background: 'radial-gradient(circle, rgba(124,58,237,0.15) 0%, transparent 70%)', pointerEvents: 'none' }} />
      <div style={{ position: 'fixed', bottom: '15%', right: '10%', width: 350, height: 350, borderRadius: '50%', background: 'radial-gradient(circle, rgba(6,182,212,0.12) 0%, transparent 70%)', pointerEvents: 'none' }} />

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        style={{ width: '100%', maxWidth: '420px', position: 'relative', zIndex: 1 }}
      >
        {/* Back button */}
        <button
          onClick={onBack}
          style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.875rem', marginBottom: '32px', padding: 0 }}
          onMouseEnter={e => e.currentTarget.style.color = 'var(--text-primary)'}
          onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}
        >
          <ArrowLeft size={16} /> Back
        </button>

        <div className="glass-card" style={{ padding: '40px', textAlign: 'center' }}>
          {/* Logo */}
          <motion.div
            animate={{ rotate: [0, 5, -5, 0] }}
            transition={{ duration: 4, repeat: Infinity }}
            style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 68, height: 68, borderRadius: '18px', background: 'var(--gradient-primary)', marginBottom: '20px', boxShadow: '0 0 40px rgba(124,58,237,0.4)' }}
          >
            <Brain size={34} color="white" />
          </motion.div>

          <h1 style={{ fontSize: '1.6rem', fontFamily: 'var(--font-display)', fontWeight: 800, marginBottom: '8px' }}>
            Welcome to <span className="gradient-text">Nexis</span>
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', lineHeight: 1.6, marginBottom: '32px' }}>
            Sign in to save your learning path across devices and sessions.
          </p>

          {isFirebaseConfigured ? (
            <>
              <button
                onClick={handleGoogleSignIn}
                disabled={loading}
                id="google-signin-btn"
                style={{
                  width: '100%', padding: '14px', borderRadius: 'var(--radius)',
                  background: 'white', color: '#1a1a2e', border: 'none',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontSize: '0.95rem', fontWeight: 600,
                  transition: 'all 0.2s', opacity: loading ? 0.7 : 1,
                  boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
                }}
                onMouseEnter={e => !loading && (e.currentTarget.style.transform = 'translateY(-2px)', e.currentTarget.style.boxShadow = '0 8px 30px rgba(0,0,0,0.4)')}
                onMouseLeave={e => (e.currentTarget.style.transform = 'none', e.currentTarget.style.boxShadow = '0 4px 20px rgba(0,0,0,0.3)')}
              >
                {loading ? <Loader2 size={20} style={{ animation: 'spin 1s linear infinite' }} /> : <GoogleIcon />}
                {loading ? 'Signing in…' : 'Continue with Google'}
              </button>

              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: '20px 0' }}>
                <div style={{ flex: 1, height: 1, background: 'var(--border-subtle)' }} />
                <span style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>or</span>
                <div style={{ flex: 1, height: 1, background: 'var(--border-subtle)' }} />
              </div>

              <button
                onClick={handleContinueWithoutAuth}
                style={{ width: '100%', padding: '12px', borderRadius: 'var(--radius)', background: 'transparent', border: '1px solid var(--border-subtle)', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.875rem', transition: 'all 0.2s' }}
                onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--border-accent)', e.currentTarget.style.color = 'var(--text-secondary)')}
                onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border-subtle)', e.currentTarget.style.color = 'var(--text-muted)')}
              >
                Continue without account (data won't be saved)
              </button>
            </>
          ) : (
            // Firebase not configured — just let them through
            <div>
              <div style={{ background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: 'var(--radius-sm)', padding: '12px 16px', marginBottom: '20px', fontSize: '0.82rem', color: '#f59e0b', textAlign: 'left' }}>
                ⚠️ Firebase not configured. Running in local mode — your data is saved in browser storage only.
              </div>
              <button
                onClick={handleContinueWithoutAuth}
                className="btn-primary"
                id="continue-local-btn"
                style={{ width: '100%', justifyContent: 'center', padding: '14px' }}
              >
                <Zap size={18} /> Continue to App
              </button>
            </div>
          )}

          {/* Feature list */}
          <div style={{ marginTop: '28px', borderTop: '1px solid var(--border-subtle)', paddingTop: '24px', textAlign: 'left' }}>
            {[
              'Synced across all your devices',
              'Progress never lost, even on free server restarts',
              'Path history and mastery tracked over time',
            ].map((f, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                <div style={{ width: 18, height: 18, borderRadius: '50%', background: 'rgba(124,58,237,0.2)', border: '1px solid rgba(124,58,237,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <span style={{ color: 'var(--accent-purple-light)', fontSize: '0.6rem' }}>✓</span>
                </div>
                {f}
              </div>
            ))}
          </div>
        </div>
      </motion.div>
    </div>
  )
}
