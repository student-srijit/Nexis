import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Sparkles, Brain, Target, Clock, ChevronRight, CheckCircle2, Loader2 } from 'lucide-react'
import { useStore } from '../utils/store'
import { createProfile, submitQuiz, generatePath } from '../utils/api'
import { saveUserProfile, saveUserPath, saveUserMastery, signOutUser } from '../utils/firebase'
import toast from 'react-hot-toast'

const EXAMPLE_GOALS = [
  "I want to become a Data Scientist in 3 months, I know basic Python",
  "Help me transition into Machine Learning Engineering — I know Python and SQL",
  "I'm a student who wants to learn Data Analysis with 10 hours/week",
  "I want to master Deep Learning — I already know Python and ML fundamentals",
]

const PHASES = { CHAT: 'chat', QUIZ: 'quiz', GENERATING: 'generating' }

export default function Onboarding() {
  const [phase, setPhase] = useState(PHASES.CHAT)
  const [goalInput, setGoalInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [quizAnswers, setQuizAnswers] = useState({})
  const [quizSubmitting, setQuizSubmitting] = useState(false)
  const { learnerId, setProfile, setCurrentPath, setMastery, setQuizQuestions, quizQuestions, setPhase: setStorePhase } = useStore()

  const handleGoalSubmit = async () => {
    if (!goalInput.trim() || loading) return
    setLoading(true)
    try {
      const res = await createProfile(learnerId, goalInput.trim())
      const { profile, quiz_questions } = res.data
      setProfile(profile)
      setQuizQuestions(quiz_questions || [])
      toast.success('Profile created! Answer a few questions to personalize your path.')
      setPhase(PHASES.QUIZ)
    } catch (err) {
      const msg = err.response?.data?.detail || 'Backend error. Make sure the server is running.'
      toast.error(msg)
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleQuizSubmit = async () => {
    if (quizSubmitting) return
    setQuizSubmitting(true)
    setPhase(PHASES.GENERATING)

    try {
      // Submit quiz
      const responses = quizQuestions.map((q, i) => ({
        question_id: q.question_id,
        skill_id: q.skill_id,
        answer_index: quizAnswers[q.question_id] ?? -1,
      }))
      const quizRes = await submitQuiz(learnerId, responses)
      setMastery(quizRes.data.skill_updates || {})

      // Generate path — retry up to 5x with 5s gaps for cold-start 503s
      let pathRes = null
      let lastErr = null
      for (let attempt = 1; attempt <= 5; attempt++) {
        try {
          pathRes = await generatePath(learnerId)
          break
        } catch (err) {
          lastErr = err
          const is503 = err.response?.status === 503
          if (is503 && attempt < 5) {
            toast.loading(`ML models warming up… retrying (${attempt}/5)`, { id: 'retry' })
            await new Promise(r => setTimeout(r, 5000))
          } else {
            toast.dismiss('retry')
            break
          }
        }
      }
      toast.dismiss('retry')

      if (!pathRes) throw lastErr

      setCurrentPath(pathRes.data)

      // Sync to Firestore so data survives backend restarts
      await saveUserProfile(learnerId, { goal: goalInput })
      await saveUserPath(learnerId, pathRes.data)
      await saveUserMastery(learnerId, quizRes.data.skill_updates || {})

      setStorePhase('dashboard')
      toast.success('🎉 Your personalized learning path is ready!')
    } catch (err) {
      const msg = err.response?.data?.detail || 'Error generating path.'
      toast.error(msg)
      setPhase(PHASES.QUIZ)
    } finally {
      setQuizSubmitting(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--gradient-hero)', position: 'relative', overflow: 'hidden' }}>
      {/* Background orbs */}
      <div style={{ position: 'fixed', top: '10%', left: '5%', width: 400, height: 400, borderRadius: '50%', background: 'radial-gradient(circle, rgba(124,58,237,0.12) 0%, transparent 70%)', pointerEvents: 'none' }} />
      <div style={{ position: 'fixed', top: '40%', right: '5%', width: 350, height: 350, borderRadius: '50%', background: 'radial-gradient(circle, rgba(6,182,212,0.1) 0%, transparent 70%)', pointerEvents: 'none' }} />
      <div style={{ position: 'fixed', bottom: '10%', left: '30%', width: 300, height: 300, borderRadius: '50%', background: 'radial-gradient(circle, rgba(236,72,153,0.08) 0%, transparent 70%)', pointerEvents: 'none' }} />

      <button 
        onClick={() => {
          signOutUser().then(() => {
            setStorePhase('landing')
            toast.success('Signed out')
          })
        }}
        style={{
          position: 'absolute', top: '24px', right: '24px',
          background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-subtle)', color: 'var(--text-muted)',
          cursor: 'pointer', fontSize: '0.8rem', padding: '8px 16px', borderRadius: 'var(--radius-full)',
          zIndex: 10
        }}
      >
        Sign Out
      </button>

      <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', minHeight: '100vh', alignItems: 'center', justifyContent: 'center', padding: '40px 24px' }}>

        {/* Hero Header */}
        <AnimatePresence>
          {phase === PHASES.CHAT && (
            <motion.div
              initial={{ opacity: 0, y: -30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              style={{ textAlign: 'center', marginBottom: '48px', maxWidth: '680px' }}
            >
              {/* Logo */}
              <motion.div
                animate={{ rotate: [0, 5, -5, 0] }}
                transition={{ duration: 4, repeat: Infinity }}
                style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 72, height: 72, borderRadius: '20px', background: 'var(--gradient-primary)', marginBottom: '20px', boxShadow: '0 0 40px rgba(124,58,237,0.4)' }}
              >
                <Brain size={36} color="white" />
              </motion.div>

              <h1 style={{ marginBottom: '16px' }}>
                <span className="gradient-text">Nexis</span>
              </h1>
              <p style={{ fontSize: '1.15rem', color: 'var(--text-secondary)', lineHeight: 1.7, maxWidth: '520px', margin: '0 auto' }}>
                Your personalized learning path, powered by <strong style={{ color: 'var(--text-primary)' }}>real ML</strong> — Bayesian Knowledge Tracing, LightGBM ranking, and a skill graph backed by ESCO data.
              </p>

              {/* Feature pills */}
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap', marginTop: '24px' }}>
                {['BKT Mastery Model', 'ESCO Skill Graph', 'LightGBM Ranker', 'AI Explainer'].map((f) => (
                  <span key={f} className="badge badge-purple">{f}</span>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Card */}
        <motion.div
          layout
          className="glass-card"
          style={{ width: '100%', maxWidth: '680px', padding: '32px' }}
          animate={{ boxShadow: '0 0 60px rgba(124,58,237,0.15)' }}
        >
          {/* Phase: Chat */}
          {phase === PHASES.CHAT && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <h2 style={{ marginBottom: '8px', fontSize: '1.3rem' }}>Tell me your learning goal</h2>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '20px' }}>
                Describe your goal in plain English — I'll extract a structured profile and build your custom path.
              </p>
              <textarea
                id="goal-input"
                value={goalInput}
                onChange={(e) => setGoalInput(e.target.value)}
                placeholder="e.g. I want to become a Data Scientist in 3 months. I know basic Python and Excel..."
                rows={4}
                onKeyDown={(e) => e.key === 'Enter' && e.ctrlKey && handleGoalSubmit()}
                style={{ marginBottom: '16px', resize: 'vertical' }}
              />

              {/* Example goals */}
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '10px' }}>Try an example:</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '20px' }}>
                {EXAMPLE_GOALS.map((g, i) => (
                  <button
                    key={i}
                    onClick={() => setGoalInput(g)}
                    id={`example-goal-${i}`}
                    style={{
                      background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)',
                      color: 'var(--text-secondary)', borderRadius: 'var(--radius-sm)',
                      padding: '8px 12px', textAlign: 'left', cursor: 'pointer',
                      fontSize: '0.82rem', transition: 'var(--transition)',
                    }}
                    onMouseEnter={(e) => { e.target.style.borderColor = 'var(--border-accent)'; e.target.style.color = 'var(--text-primary)' }}
                    onMouseLeave={(e) => { e.target.style.borderColor = 'var(--border-subtle)'; e.target.style.color = 'var(--text-secondary)' }}
                  >
                    <ChevronRight size={12} style={{ display: 'inline', marginRight: '6px' }} />
                    {g}
                  </button>
                ))}
              </div>

              <button
                onClick={handleGoalSubmit}
                disabled={!goalInput.trim() || loading}
                className="btn-primary"
                id="submit-goal-btn"
                style={{ width: '100%', justifyContent: 'center', padding: '14px' }}
              >
                {loading ? <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} /> : <Sparkles size={18} />}
                {loading ? 'Analyzing your goal…' : 'Build My Learning Path'}
              </button>
            </motion.div>
          )}

          {/* Phase: Quiz */}
          {phase === PHASES.QUIZ && (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
              <h2 style={{ marginBottom: '8px', fontSize: '1.2rem' }}>Quick Knowledge Check</h2>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '24px' }}>
                {quizQuestions.length} questions to calibrate your BKT mastery scores. Be honest — this makes your path more accurate.
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '24px' }}>
                {quizQuestions.map((q, qi) => (
                  <div key={q.question_id}>
                    <p style={{ fontWeight: 600, marginBottom: '10px', fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                      <span style={{ color: 'var(--accent-purple-light)', marginRight: '8px' }}>Q{qi + 1}</span>
                      <span className="badge badge-cyan" style={{ marginRight: '8px', fontSize: '0.68rem' }}>{q.skill_label}</span>
                      {q.question_text}
                    </p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {q.options.map((opt, oi) => {
                        const selected = quizAnswers[q.question_id] === oi
                        return (
                          <button
                            key={oi}
                            id={`quiz-opt-${qi}-${oi}`}
                            onClick={() => setQuizAnswers((prev) => ({ ...prev, [q.question_id]: oi }))}
                            style={{
                              padding: '10px 14px', borderRadius: 'var(--radius-sm)',
                              border: selected ? '2px solid var(--accent-purple)' : '1px solid var(--border-subtle)',
                              background: selected ? 'rgba(124,58,237,0.15)' : 'var(--bg-card)',
                              color: selected ? 'var(--accent-purple-light)' : 'var(--text-secondary)',
                              cursor: 'pointer', textAlign: 'left', fontSize: '0.875rem',
                              transition: 'all 0.15s', fontWeight: selected ? 600 : 400,
                            }}
                          >
                            <span style={{ marginRight: '8px', opacity: 0.5 }}>{String.fromCharCode(65 + oi)}.</span>
                            {opt}
                            {selected && <CheckCircle2 size={14} style={{ float: 'right', marginTop: '2px', color: 'var(--accent-purple)' }} />}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </div>

              <button
                onClick={handleQuizSubmit}
                disabled={quizSubmitting}
                className="btn-primary"
                id="submit-quiz-btn"
                style={{ width: '100%', justifyContent: 'center', padding: '14px' }}
              >
                {quizSubmitting ? <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} /> : <Target size={18} />}
                {quizSubmitting ? 'Generating your path…' : 'Generate My Learning Path'}
              </button>

              <button
                onClick={handleQuizSubmit}
                style={{ width: '100%', marginTop: '10px', background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.82rem', padding: '8px' }}
                id="skip-quiz-btn"
              >
                Skip quiz (use defaults)
              </button>
            </motion.div>
          )}

          {/* Phase: Generating */}
          {phase === PHASES.GENERATING && (
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              style={{ textAlign: 'center', padding: '40px 0' }}
            >
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                style={{ display: 'inline-flex', marginBottom: '20px' }}
              >
                <Sparkles size={48} color="var(--accent-purple-light)" />
              </motion.div>
              <h3 style={{ marginBottom: '8px' }}>Building your personalized path…</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                Running BKT mastery analysis · Querying skill graph · Ranking courses with LightGBM
              </p>

              <div style={{ marginTop: '24px', display: 'flex', flexDirection: 'column', gap: '8px', maxWidth: '320px', margin: '24px auto 0' }}>
                {['Skill gap analysis', 'BKT mastery init', 'Embedding search', 'LightGBM ranking', 'Generating explanations'].map((step, i) => (
                  <motion.div
                    key={step}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.4 }}
                    style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)', fontSize: '0.82rem' }}
                  >
                    <motion.div
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.3 }}
                      style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent-purple)' }}
                    />
                    {step}
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </motion.div>

        {/* Stats footer */}
        {phase === PHASES.CHAT && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            style={{ display: 'flex', gap: '32px', marginTop: '40px', flexWrap: 'wrap', justifyContent: 'center' }}
          >
            {[
              { icon: Brain, label: 'BKT Mastery Model', desc: 'OULAD-trained' },
              { icon: Target, label: 'ESCO Skill Graph', desc: '14K+ skills' },
              { icon: Sparkles, label: 'LightGBM Ranker', desc: 'NDCG@5 optimized' },
              { icon: Clock, label: 'Adaptive Replanning', desc: 'Quiz → update' },
            ].map(({ icon: Icon, label, desc }) => (
              <div key={label} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                <Icon size={20} style={{ color: 'var(--accent-purple-light)', marginBottom: '4px' }} />
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>{label}</div>
                <div style={{ fontSize: '0.72rem' }}>{desc}</div>
              </div>
            ))}
          </motion.div>
        )}
      </div>
    </div>
  )
}
