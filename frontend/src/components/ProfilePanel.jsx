import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { User, Mail, Clock, Target, AlertTriangle, LogOut, Loader2, RefreshCw } from 'lucide-react'
import { useAuth } from '../utils/AuthContext'
import { useStore } from '../utils/store'
import { signOutUser, resetUserData } from '../utils/firebase'
import toast from 'react-hot-toast'

export default function ProfilePanel() {
  const { user } = useAuth() || {}
  const { profile, resetAll, setPhase, learnerId } = useStore()
  const [isResetting, setIsResetting] = useState(false)

  if (!user) return null

  const handleReset = async () => {
    if (!window.confirm("Are you sure? This will delete your current learning path and mastery data. You will be redirected to Onboarding to start fresh.")) {
      return
    }
    
    setIsResetting(true)
    try {
      await resetUserData(user.uid)
      resetAll()
      setPhase('onboarding')
      toast.success('Account reset successfully. Let\'s start fresh!')
    } catch (err) {
      toast.error('Failed to reset account: ' + err.message)
      setIsResetting(false)
    }
  }

  const handleSignOut = async () => {
    await signOutUser()
    resetAll()
    setPhase('landing')
    toast.success('Signed out')
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ padding: '24px 0', maxWidth: '800px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}
    >
      {/* Identity Card */}
      <div style={{ background: 'var(--bg-glass)', border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '24px', display: 'flex', gap: '24px', alignItems: 'center' }}>
        <img 
          src={user.photoURL || `https://ui-avatars.com/api/?name=${user.email}`} 
          alt={user.displayName} 
          style={{ width: '80px', height: '80px', borderRadius: '50%', border: '2px solid var(--border-accent)' }}
        />
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: '0 0 4px 0', fontSize: '1.5rem', color: 'var(--text-primary)' }}>{user.displayName}</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Mail size={14} /> {user.email}</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><User size={14} /> ID: {user.uid.slice(0, 8)}...</span>
          </div>
        </div>
      </div>

      {/* Learning Profile Details */}
      {profile && (
        <div style={{ background: 'var(--bg-glass)', border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '24px' }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Target size={18} color="var(--accent-purple-light)" /> Learning Profile
          </h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div style={{ background: 'var(--bg-elevated)', padding: '16px', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>Original Goal</div>
              <div style={{ color: 'var(--text-primary)', fontSize: '0.95rem', lineHeight: '1.4' }}>{profile.goal}</div>
            </div>
            
            <div style={{ background: 'var(--bg-elevated)', padding: '16px', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>Target Occupation</div>
              <div style={{ color: 'var(--text-primary)', fontSize: '0.95rem' }}>{profile.target_occupation || 'Data Scientist'}</div>
              
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '16px', marginBottom: '8px' }}>Pace</div>
              <div style={{ color: 'var(--text-primary)', fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Clock size={14} /> {profile.hours_per_week || 10} hours / week
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Danger Zone */}
      <div style={{ border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '12px', padding: '24px', background: 'rgba(239, 68, 68, 0.05)' }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: '1.1rem', color: '#ef4444', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertTriangle size={18} /> Danger Zone
        </h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '16px' }}>
          These actions are irreversible. If you reset your learning path, all your progress, mastery, and current course state will be permanently deleted.
        </p>
        <div style={{ display: 'flex', gap: '16px' }}>
          <button 
            onClick={handleReset} 
            disabled={isResetting}
            style={{ 
              background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.5)', 
              color: '#ef4444', padding: '10px 16px', borderRadius: '8px', cursor: isResetting ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, transition: 'all 0.2s'
            }}
          >
            {isResetting ? <Loader2 size={16} className="spin" /> : <RefreshCw size={16} />}
            Reset Learning Path
          </button>
          
          <button 
            onClick={handleSignOut} 
            style={{ 
              background: 'transparent', border: '1px solid var(--border-subtle)', 
              color: 'var(--text-secondary)', padding: '10px 16px', borderRadius: '8px', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, transition: 'all 0.2s'
            }}
          >
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      </div>
    </motion.div>
  )
}
