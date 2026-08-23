import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { ExternalLink, Clock, BarChart2, Sparkles, ChevronDown, ChevronUp } from 'lucide-react'

const DIFFICULTY_CONFIG = {
  beginner: { color: 'var(--accent-green)', badge: 'badge-green', label: 'Beginner' },
  intermediate: { color: 'var(--accent-orange)', badge: 'badge-orange', label: 'Intermediate' },
  advanced: { color: 'var(--accent-pink)', badge: 'badge-purple', label: 'Advanced' },
}

const PROVIDER_COLORS = {
  'Coursera': '#0056D2',
  'Udemy': '#A435F0',
  'Kaggle': '#20BEFF',
  'IBM': '#006699',
  'Google': '#4285F4',
  'Stanford': '#8C1515',
  'Hugging Face': '#FF9D00',
}

export default function CourseCard({ step, index, onAskAI, isCompleted = false }) {
  const [expanded, setExpanded] = useState(false)
  const diff = DIFFICULTY_CONFIG[step.difficulty] || DIFFICULTY_CONFIG.intermediate
  const providerColor = Object.entries(PROVIDER_COLORS).find(([k]) => step.course_title?.includes(k) || step.provider?.includes(k))?.[1] || 'var(--accent-purple)'

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.08 }}
      className="glass-card"
      style={{
        padding: '20px',
        border: isCompleted ? '1px solid rgba(16,185,129,0.3)' : '1px solid var(--border-subtle)',
        opacity: isCompleted ? 0.6 : 1,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Step number */}
      <div style={{
        position: 'absolute', top: 0, left: 0,
        background: 'var(--gradient-primary)',
        color: 'white', fontWeight: 700, fontSize: '0.7rem',
        padding: '4px 10px 4px 12px',
        borderRadius: '0 0 12px 0',
      }}>
        STEP {(step.step_index ?? index) + 1}
      </div>

      <div style={{ marginTop: '16px' }}>
        {/* Title row */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
          <div style={{ flex: 1 }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '4px', color: 'var(--text-primary)' }}>
              {step.course_title}
            </h3>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
              {/* Provider badge */}
              <span style={{
                fontSize: '0.72rem', fontWeight: 600, color: 'white',
                background: providerColor, padding: '2px 8px', borderRadius: '4px',
              }}>
                {step.provider || 'Coursera'}
              </span>
              {/* Difficulty */}
              <span className={`badge ${diff.badge}`}>{diff.label}</span>
              {/* Milestone */}
              <span className="badge badge-cyan">Week {step.milestone_week}</span>
            </div>
          </div>

          {/* Scores */}
          <div style={{ textAlign: 'right', flexShrink: 0 }}>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, background: 'var(--gradient-primary)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              {(step.recommendation_score * 100).toFixed(0)}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>score</div>
          </div>
        </div>

        {/* Meta row */}
        <div style={{ display: 'flex', gap: '16px', marginTop: '12px', color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Clock size={13} /> {step.estimated_hours}h
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <BarChart2 size={13} /> Mastery: {(step.mastery_score_before * 100).toFixed(0)}%
          </span>
        </div>

        {/* Skills taught */}
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '10px' }}>
          {step.skills_taught?.map((sk) => (
            <span key={sk} style={{
              fontSize: '0.72rem', padding: '3px 8px', borderRadius: '4px',
              background: 'rgba(124,58,237,0.15)', color: 'var(--accent-purple-light)',
              border: '1px solid rgba(124,58,237,0.2)'
            }}>
              {sk.replace('s_', '').replace(/_/g, ' ')}
            </span>
          ))}
        </div>

        {/* Expandable why */}
        {step.why_recommended && (
          <div style={{ marginTop: '12px' }}>
            <button
              onClick={() => setExpanded(!expanded)}
              style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                background: 'transparent', border: 'none', color: 'var(--accent-cyan-light)',
                fontSize: '0.82rem', cursor: 'pointer', padding: 0, fontWeight: 500
              }}
              id={`course-expand-${step.course_id}`}
            >
              <Sparkles size={13} /> Why recommended?
              {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            </button>
            {expanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                style={{
                  marginTop: '8px', padding: '12px', borderRadius: 'var(--radius-sm)',
                  background: 'rgba(6,182,212,0.06)', border: '1px solid rgba(6,182,212,0.15)',
                  fontSize: '0.83rem', color: 'var(--text-secondary)', lineHeight: 1.6
                }}
              >
                {step.why_recommended}
              </motion.div>
            )}
          </div>
        )}

        {/* Actions */}
        <div style={{ display: 'flex', gap: '8px', marginTop: '14px', flexWrap: 'wrap' }}>
          <button
            onClick={() => onAskAI && onAskAI(step.course_id)}
            className="btn-secondary"
            style={{ padding: '7px 14px', fontSize: '0.8rem' }}
            id={`ask-ai-btn-${step.course_id}`}
          >
            <Sparkles size={13} /> Ask AI
          </button>
          {step.url && (
            <a
              href={step.url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-ghost"
              style={{ padding: '7px 14px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '5px', textDecoration: 'none' }}
            >
              <ExternalLink size={13} /> Open Course
            </a>
          )}
        </div>
      </div>
    </motion.div>
  )
}
