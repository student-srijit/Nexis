import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Brain, Target, BarChart2, MessageSquare, RefreshCw,
  CheckCircle2, ChevronRight, Trophy, Loader2, BookOpen,
  Zap, TrendingUp, RotateCcw
} from 'lucide-react'
import { useStore } from '../utils/store'
import { getCurrentPath, getMastery, submitQuiz, replanPath } from '../utils/api'
import MasteryRadar from '../components/MasteryRadar'
import PathTimeline from '../components/PathTimeline'
import CourseCard from '../components/CourseCard'
import ChatPanel from '../components/ChatPanel'
import toast from 'react-hot-toast'

const TABS = [
  { id: 'path', label: 'Learning Path', icon: Target },
  { id: 'mastery', label: 'Mastery', icon: Brain },
  { id: 'chat', label: 'AI Assistant', icon: MessageSquare },
  { id: 'quiz', label: 'Quiz & Replan', icon: Zap },
]

// Mini quiz for adaptive replanning
const REPLAN_QUIZ = [
  { question_id: 'rq_python', skill_id: 's_python', question_text: "Complete: list_comp = [x**2 for x in range(5)] → result?", options: ['[0,1,4,9,16]', '[1,4,9,16,25]', '[0,2,4,6,8]', 'Error'], correct_index: 0, skill_label: 'Python' },
  { question_id: 'rq_ml', skill_id: 's_ml', question_text: "Which metric is best for imbalanced classification?", options: ['Accuracy', 'F1-Score', 'MSE', 'R²'], correct_index: 1, skill_label: 'ML' },
  { question_id: 'rq_stats', skill_id: 's_stats', question_text: "What does p < 0.05 mean in hypothesis testing?", options: ['Reject null hypothesis', 'Accept null hypothesis', 'No conclusion', 'Data is wrong'], correct_index: 0, skill_label: 'Stats' },
  { question_id: 'rq_dl', skill_id: 's_dl', question_text: "What is backpropagation?", options: ['Algorithm to compute gradients via chain rule', 'Forward pass through network', 'Data augmentation technique', 'Regularization method'], correct_index: 0, skill_label: 'Deep Learning' },
  { question_id: 'rq_sql', skill_id: 's_sql', question_text: "What does GROUP BY do in SQL?", options: ['Groups rows sharing values, used with aggregates', 'Filters rows', 'Sorts results', 'Joins tables'], correct_index: 0, skill_label: 'SQL' },
]

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('path')
  const [loading, setLoading] = useState(true)
  const [path, setPath] = useState(null)
  const [mastery, setLocalMastery] = useState({})
  const [quizAnswers, setQuizAnswers] = useState({})
  const [quizSubmitting, setQuizSubmitting] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [activeCourseId, setActiveCourseId] = useState(null)

  const { learnerId, profile, currentPath, mastery: storedMastery, setCurrentPath, updateMastery, resetAll } = useStore()

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    setLoading(true)
    try {
      const [pathRes, masteryRes] = await Promise.all([
        getCurrentPath(learnerId),
        getMastery(learnerId),
      ])
      setPath(pathRes.data)
      setCurrentPath(pathRes.data)
      setLocalMastery(masteryRes.data.skill_mastery || storedMastery)
      updateMastery(masteryRes.data.skill_mastery || {})
    } catch (err) {
      if (currentPath) {
        setPath(currentPath)
        setLocalMastery(storedMastery)
      } else {
        toast.error('Could not load path. Using demo data.')
        setPath(getDemoPath())
        setLocalMastery({ s_python: 0.2, s_stats: 0.4, s_ml: 0.1, s_dl: 0.05, s_sql: 0.6, s_data_viz: 0.3, s_pandas: 0.25 })
      }
    } finally {
      setLoading(false)
    }
  }

  const handleQuizSubmit = async () => {
    setQuizSubmitting(true)
    try {
      const responses = REPLAN_QUIZ.map((q) => ({
        question_id: q.question_id,
        skill_id: q.skill_id,
        answer_index: quizAnswers[q.question_id] ?? -1,
      }))

      const quizRes = await submitQuiz(learnerId, responses)
      const newMastery = quizRes.data.skill_updates || {}
      updateMastery(newMastery)
      setLocalMastery((prev) => ({ ...prev, ...newMastery }))

      toast.success(`Quiz done! ${quizRes.data.correct_count}/${quizRes.data.total_count} correct. Replanning path…`)

      // Replan
      const replanRes = await replanPath(learnerId, [])
      setPath(replanRes.data)
      setCurrentPath(replanRes.data)
      toast.success(`🔄 Path updated! Version ${replanRes.data.version}`)
      setActiveTab('path')
      setCurrentStep(0)
    } catch (err) {
      toast.error('Replan failed: ' + (err.response?.data?.detail || err.message))
      // Simulate locally
      const correct = Object.values(quizAnswers).filter((a, i) => a === REPLAN_QUIZ[i]?.correct_index).length
      const total = Object.keys(quizAnswers).length
      toast(`Quiz scored ${correct}/${total}. Backend needed for real replan.`)
    } finally {
      setQuizSubmitting(false)
    }
  }

  const totalHours = path?.total_estimated_hours || 0
  const completedHours = path?.steps?.slice(0, currentStep).reduce((a, s) => a + (s.estimated_hours || 0), 0) || 0
  const progressPct = totalHours > 0 ? (completedHours / totalHours) * 100 : 0

  if (loading) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '16px' }}>
      <motion.div animate={{ rotate: 360 }} transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}>
        <Brain size={40} color="var(--accent-purple-light)" />
      </motion.div>
      <p style={{ color: 'var(--text-muted)' }}>Loading your learning path…</p>
    </div>
  )

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)' }}>
      {/* Header */}
      <header style={{
        borderBottom: '1px solid var(--border-subtle)',
        background: 'var(--bg-glass)',
        backdropFilter: 'blur(12px)',
        position: 'sticky', top: 0, zIndex: 100,
        padding: '0 24px',
      }}>
        <div style={{ maxWidth: 1400, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: '60px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: 32, height: 32, borderRadius: '8px', background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Brain size={18} color="white" />
            </div>
            <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.1rem' }} className="gradient-text">
              Nexis
            </span>
          </div>

          {/* Goal display */}
          {profile && (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem', maxWidth: '400px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              🎯 {profile.goal}
            </div>
          )}

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <button onClick={loadDashboard} className="btn-ghost" style={{ padding: '6px 10px' }}>
              <RefreshCw size={14} />
            </button>
            <button onClick={resetAll} className="btn-ghost" style={{ padding: '6px 10px', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              <RotateCcw size={14} /> Reset
            </button>
          </div>
        </div>
      </header>

      {/* Stats bar */}
      <div style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-subtle)', padding: '12px 24px' }}>
        <div style={{ maxWidth: 1400, margin: '0 auto', display: 'flex', gap: '32px', flexWrap: 'wrap', alignItems: 'center' }}>
          {[
            { label: 'Total Hours', value: `${totalHours.toFixed(0)}h`, color: 'var(--accent-purple-light)' },
            { label: 'Total Weeks', value: `${path?.total_weeks || 0}w`, color: 'var(--accent-cyan)' },
            { label: 'Courses', value: path?.steps?.length || 0, color: 'var(--accent-green)' },
            { label: 'Path Version', value: `v${path?.version || 1}`, color: 'var(--accent-orange)' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color }}>{value}</div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{label}</div>
            </div>
          ))}
          <div style={{ flex: 1, minWidth: '200px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Progress</span>
              <span style={{ fontSize: '0.75rem', color: 'var(--accent-purple-light)' }}>{progressPct.toFixed(0)}%</span>
            </div>
            <div className="progress-bar">
              <motion.div
                className="progress-fill"
                initial={{ width: 0 }}
                animate={{ width: `${progressPct}%` }}
                transition={{ duration: 1 }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Navigation tabs */}
      <div style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-subtle)', padding: '0 24px' }}>
        <div style={{ maxWidth: 1400, margin: '0 auto', display: 'flex', gap: '4px' }}>
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              id={`tab-${id}`}
              onClick={() => setActiveTab(id)}
              style={{
                background: 'transparent',
                border: 'none',
                borderBottom: activeTab === id ? '2px solid var(--accent-purple)' : '2px solid transparent',
                color: activeTab === id ? 'var(--accent-purple-light)' : 'var(--text-muted)',
                padding: '12px 16px',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: activeTab === id ? 600 : 400,
                display: 'flex', alignItems: 'center', gap: '6px',
                transition: 'var(--transition)',
              }}
            >
              <Icon size={15} />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Main content */}
      <div style={{ maxWidth: 1400, margin: '0 auto', padding: '24px' }}>
        <AnimatePresence mode="wait">
          {/* PATH TAB */}
          {activeTab === 'path' && (
            <motion.div key="path" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '24px' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h2 style={{ fontSize: '1.1rem' }}>Your Personalized Path</h2>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      Target: {profile?.target_occupation?.replace('occ_', '').replace(/_/g, ' ') || 'Data Scientist'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {path?.steps?.map((step, i) => (
                      <CourseCard
                        key={step.course_id || i}
                        step={step}
                        index={i}
                        isCompleted={i < currentStep}
                        onAskAI={(courseId) => {
                          setActiveCourseId(courseId)
                          setActiveTab('chat')
                        }}
                      />
                    )) || (
                      <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                        <BookOpen size={40} style={{ marginBottom: '12px' }} />
                        <p>No path loaded. Try refreshing.</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Sidebar */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <PathTimeline steps={path?.steps || []} currentStep={currentStep} />

                  {/* Step completion control */}
                  <div className="glass-card" style={{ padding: '16px' }}>
                    <h3 style={{ fontSize: '0.9rem', marginBottom: '12px' }}>Mark Progress</h3>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
                      Step {currentStep + 1} of {path?.steps?.length || 0}
                    </p>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
                        className="btn-ghost"
                        style={{ flex: 1, padding: '8px' }}
                        disabled={currentStep === 0}
                      >
                        ←
                      </button>
                      <button
                        onClick={() => {
                          const next = Math.min((path?.steps?.length || 1) - 1, currentStep + 1)
                          setCurrentStep(next)
                          toast.success(`✓ Marked step ${currentStep + 1} complete!`)
                        }}
                        className="btn-primary"
                        style={{ flex: 2, padding: '8px', fontSize: '0.82rem', justifyContent: 'center' }}
                        disabled={currentStep >= (path?.steps?.length || 1) - 1}
                        id="mark-complete-btn"
                      >
                        <CheckCircle2 size={14} /> Mark Done
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* MASTERY TAB */}
          {activeTab === 'mastery' && (
            <motion.div key="mastery" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                <MasteryRadar mastery={mastery} />
                <div className="glass-card" style={{ padding: '20px' }}>
                  <h3 style={{ marginBottom: '16px', fontSize: '1rem' }}>Skill Mastery Details</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginBottom: '16px' }}>
                    BKT p(mastery) — Bayesian probability that you've mastered each skill, updated from quiz answers.
                  </p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {Object.entries(mastery).length > 0
                      ? Object.entries(mastery).sort((a, b) => b[1] - a[1]).map(([sid, val]) => (
                        <div key={sid} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <span style={{ width: '120px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                            {sid.replace('s_', '').replace(/_/g, ' ')}
                          </span>
                          <div className="progress-bar" style={{ flex: 1 }}>
                            <motion.div className="progress-fill" initial={{ width: 0 }}
                              animate={{ width: `${val * 100}%` }} transition={{ duration: 0.7 }} />
                          </div>
                          <span style={{ width: '40px', textAlign: 'right', fontSize: '0.78rem', color: val >= 0.7 ? 'var(--accent-green)' : val >= 0.4 ? 'var(--accent-orange)' : 'var(--accent-pink)' }}>
                            {(val * 100).toFixed(0)}%
                          </span>
                        </div>
                      ))
                      : <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No mastery data yet. Take the quiz!</p>
                    }
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* CHAT TAB */}
          {activeTab === 'chat' && (
            <motion.div key="chat" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <div style={{ maxWidth: '800px' }}>
                <div style={{ marginBottom: '16px' }}>
                  <h2 style={{ fontSize: '1.1rem', marginBottom: '4px' }}>AI Explainer</h2>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                    Ask why any course was recommended. Every answer is grounded in your actual BKT mastery scores and ranker output — no hallucinated content.
                  </p>
                </div>
                <ChatPanel courseId={activeCourseId} />
                {activeCourseId && (
                  <button
                    onClick={() => setActiveCourseId(null)}
                    className="btn-ghost"
                    style={{ marginTop: '8px', fontSize: '0.8rem' }}
                  >
                    Clear course context
                  </button>
                )}
              </div>
            </motion.div>
          )}

          {/* QUIZ TAB */}
          {activeTab === 'quiz' && (
            <motion.div key="quiz" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <div style={{ maxWidth: '720px' }}>
                <div style={{ marginBottom: '20px' }}>
                  <h2 style={{ fontSize: '1.1rem', marginBottom: '4px' }}>Adaptive Quiz → Replan</h2>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                    Answer these questions. Your BKT mastery scores will update, then your learning path will replan automatically.
                    This is the adaptive loop: quiz → mastery update → path change.
                  </p>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '24px' }}>
                  {REPLAN_QUIZ.map((q, qi) => (
                    <div key={q.question_id} className="glass-card" style={{ padding: '20px' }}>
                      <p style={{ fontWeight: 600, marginBottom: '12px', fontSize: '0.9rem' }}>
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
                              id={`replan-opt-${qi}-${oi}`}
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
                  id="replan-submit-btn"
                  style={{ width: '100%', justifyContent: 'center', padding: '14px' }}
                >
                  {quizSubmitting ? <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} /> : <TrendingUp size={18} />}
                  {quizSubmitting ? 'Updating mastery & replanning…' : 'Submit & Replan My Path'}
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

function getDemoPath() {
  return {
    learner_id: 'demo',
    path_id: 'demo-path',
    target_occupation: 'occ_ds',
    total_estimated_hours: 155,
    total_weeks: 16,
    version: 1,
    generated_at: new Date().toISOString(),
    steps: [
      { step_index: 0, course_id: 'c_py_001', course_title: 'Python for Everybody', skills_taught: ['s_python'], prerequisite_skills: [], estimated_hours: 30, difficulty: 'beginner', mastery_score_before: 0.18, recommendation_score: 0.82, milestone_week: 3, why_recommended: 'Recommended because your Python mastery is 0.18 (low). This is the first prerequisite toward Machine Learning (2 hops away). Ranker score: 0.82 — highest in your gap.', provider: 'Coursera', url: 'https://www.coursera.org/specializations/python' },
      { step_index: 1, course_id: 'c_st_002', course_title: 'Introduction to Statistics', skills_taught: ['s_stats'], prerequisite_skills: ['s_python'], estimated_hours: 15, difficulty: 'beginner', mastery_score_before: 0.25, recommendation_score: 0.76, milestone_week: 5, why_recommended: 'Statistics mastery at 0.25. Required for ML (prerequisite). Ranker score: 0.76.', provider: 'Stanford (Coursera)', url: 'https://www.coursera.org/learn/stanford-statistics' },
      { step_index: 2, course_id: 'c_pd_001', course_title: 'Data Analysis with Python', skills_taught: ['s_pandas', 's_data_viz'], prerequisite_skills: ['s_python'], estimated_hours: 20, difficulty: 'intermediate', mastery_score_before: 0.15, recommendation_score: 0.71, milestone_week: 7, why_recommended: 'Pandas mastery at 0.15. Closes gap in data manipulation, required before ML practical work.', provider: 'Coursera (IBM)', url: 'https://www.coursera.org/learn/data-analysis-with-python' },
      { step_index: 3, course_id: 'c_ml_001', course_title: 'Machine Learning Specialization', skills_taught: ['s_ml'], prerequisite_skills: ['s_python', 's_stats'], estimated_hours: 65, difficulty: 'intermediate', mastery_score_before: 0.08, recommendation_score: 0.88, milestone_week: 13, why_recommended: 'ML mastery at 0.08 (critical gap for Data Scientist role). After completing Python and Stats prerequisites, this is the core target skill. Ranker score: 0.88.', provider: 'Coursera (DeepLearning.AI)', url: 'https://www.coursera.org/specializations/machine-learning-introduction' },
      { step_index: 4, course_id: 'c_sql_001', course_title: 'SQL for Data Science', skills_taught: ['s_sql'], prerequisite_skills: [], estimated_hours: 15, difficulty: 'beginner', mastery_score_before: 0.35, recommendation_score: 0.64, milestone_week: 14, why_recommended: 'SQL mastery at 0.35 — partial. Data Scientists need SQL for querying databases. Ranker score: 0.64.', provider: 'Coursera (UC Davis)', url: 'https://www.coursera.org/learn/sql-for-data-science' },
      { step_index: 5, course_id: 'c_dl_001', course_title: 'Deep Learning Specialization', skills_taught: ['s_dl'], prerequisite_skills: ['s_ml'], estimated_hours: 80, difficulty: 'advanced', mastery_score_before: 0.05, recommendation_score: 0.73, milestone_week: 16, why_recommended: 'Deep Learning mastery at 0.05. Optional but highly valued for Data Scientist role. Unlocked after ML completion.', provider: 'Coursera (DeepLearning.AI)', url: 'https://www.coursera.org/specializations/deep-learning' },
    ]
  }
}
