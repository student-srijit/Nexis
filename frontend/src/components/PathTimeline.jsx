import React from 'react'
import { motion } from 'framer-motion'
import { CheckCircle2, Circle, Clock, Target, BookOpen } from 'lucide-react'

const MILESTONE_COLORS = ['#7c3aed', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6']

export default function PathTimeline({ steps = [], currentStep = 0 }) {
  if (!steps || steps.length === 0) return (
    <div className="glass-card" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
      <BookOpen size={32} style={{ marginBottom: '8px', opacity: 0.5 }} />
      <p>Generate your path to see the timeline</p>
    </div>
  )

  return (
    <div className="glass-card" style={{ padding: '20px' }}>
      <h3 style={{ marginBottom: '20px', fontSize: '1rem', fontWeight: 700 }}>
        Learning Path Timeline
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '8px', fontWeight: 400 }}>
          {steps.length} steps · ~{steps.reduce((a, s) => a + (s.estimated_hours || 0), 0).toFixed(0)}h total
        </span>
      </h3>

      <div style={{ position: 'relative' }}>
        {/* Vertical line */}
        <div style={{
          position: 'absolute', left: '15px', top: '8px',
          width: '2px',
          height: `calc(100% - 16px)`,
          background: 'linear-gradient(to bottom, #7c3aed, #06b6d4)',
          opacity: 0.3,
        }} />

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
          {steps.map((step, i) => {
            const isComplete = i < currentStep
            const isCurrent = i === currentStep
            const color = MILESTONE_COLORS[i % MILESTONE_COLORS.length]

            return (
              <motion.div
                key={step.course_id || i}
                initial={{ opacity: 0, x: -16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.07 }}
                style={{ display: 'flex', gap: '14px', paddingBottom: i < steps.length - 1 ? '20px' : '0' }}
              >
                {/* Icon */}
                <div style={{ position: 'relative', zIndex: 1, flexShrink: 0 }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: '50%',
                    background: isComplete ? 'var(--accent-green)' : isCurrent ? color : 'var(--bg-card)',
                    border: `2px solid ${isComplete ? 'var(--accent-green)' : isCurrent ? color : 'var(--border-subtle)'}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    boxShadow: isCurrent ? `0 0 16px ${color}40` : 'none',
                    transition: 'all 0.3s',
                  }}>
                    {isComplete
                      ? <CheckCircle2 size={16} color="white" />
                      : isCurrent
                        ? <Target size={15} color="white" />
                        : <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)' }}>{i + 1}</span>
                    }
                  </div>
                </div>

                {/* Content */}
                <div style={{
                  flex: 1, paddingTop: '4px',
                  borderRadius: 'var(--radius-sm)',
                  padding: isCurrent ? '10px 12px' : '4px 8px',
                  background: isCurrent ? `${color}10` : 'transparent',
                  border: isCurrent ? `1px solid ${color}30` : '1px solid transparent',
                  transition: 'all 0.3s',
                }}>
                  <div style={{ fontWeight: isCurrent ? 700 : 500, fontSize: '0.875rem', color: isComplete ? 'var(--text-muted)' : 'var(--text-primary)' }}>
                    {step.course_title}
                  </div>
                  <div style={{ display: 'flex', gap: '10px', marginTop: '4px', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '3px' }}>
                      <Clock size={11} /> {step.estimated_hours}h
                    </span>
                    <span style={{ fontSize: '0.72rem', color: color }}>Week {step.milestone_week}</span>
                    {step.difficulty && (
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                        {step.difficulty}
                      </span>
                    )}
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
