import React from 'react'
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from 'recharts'
import { motion } from 'framer-motion'

const SKILL_LABELS = {
  s_python: 'Python',
  s_ml: 'Machine Learning',
  s_stats: 'Statistics',
  s_dl: 'Deep Learning',
  s_data_viz: 'Data Viz',
  s_sql: 'SQL',
  s_pandas: 'Pandas',
  s_nlp: 'NLP',
  s_cv: 'Computer Vision',
  s_mlops: 'MLOps',
  s_feature_eng: 'Feature Eng',
  s_git: 'Git',
  s_r: 'R',
  s_docker: 'Docker',
  s_cloud: 'Cloud',
}

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const d = payload[0].payload
    return (
      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border-accent)',
        borderRadius: 'var(--radius-sm)', padding: '8px 12px', fontSize: '0.82rem'
      }}>
        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{d.skill}</div>
        <div style={{ color: 'var(--accent-purple-light)' }}>Mastery: {(d.mastery * 100).toFixed(1)}%</div>
      </div>
    )
  }
  return null
}

export default function MasteryRadar({ mastery = {} }) {
  const skillIds = Object.keys(mastery).filter((s) => s in SKILL_LABELS)
  const data = skillIds.map((sid) => ({
    skill: SKILL_LABELS[sid] || sid,
    mastery: mastery[sid] || 0,
    fullMark: 1,
  }))

  if (data.length < 3) {
    // Demo data
    const demoSkills = ['Python', 'Statistics', 'Machine Learning', 'SQL', 'Data Viz']
    const demoValues = [0.85, 0.4, 0.2, 0.6, 0.3]
    data.push(...demoSkills.map((s, i) => ({ skill: s, mastery: demoValues[i], fullMark: 1 })))
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="glass-card"
      style={{ padding: '20px' }}
    >
      <h3 style={{ marginBottom: '16px', fontSize: '1rem', fontWeight: 700 }}>
        Skill Mastery Radar
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '8px', fontWeight: 400 }}>
          BKT p(mastery) scores
        </span>
      </h3>
      <ResponsiveContainer width="100%" height={280}>
        <RadarChart data={data} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
          <PolarGrid stroke="rgba(255,255,255,0.08)" />
          <PolarAngleAxis
            dataKey="skill"
            tick={{ fill: 'var(--text-secondary)', fontSize: 11 }}
          />
          <Radar
            name="Mastery"
            dataKey="mastery"
            stroke="#7c3aed"
            fill="#7c3aed"
            fillOpacity={0.25}
            strokeWidth={2}
            dot={{ fill: '#9f67ff', strokeWidth: 0, r: 4 }}
          />
          <Tooltip content={<CustomTooltip />} />
        </RadarChart>
      </ResponsiveContainer>

      {/* Legend bars */}
      <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {data.slice(0, 6).map((d) => (
          <div key={d.skill} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ width: '80px', fontSize: '0.75rem', color: 'var(--text-secondary)', flexShrink: 0 }}>
              {d.skill}
            </span>
            <div className="progress-bar" style={{ flex: 1 }}>
              <motion.div
                className="progress-fill"
                initial={{ width: 0 }}
                animate={{ width: `${d.mastery * 100}%` }}
                transition={{ duration: 0.8, delay: 0.2 }}
              />
            </div>
            <span style={{ width: '36px', fontSize: '0.75rem', color: 'var(--accent-purple-light)', textAlign: 'right' }}>
              {(d.mastery * 100).toFixed(0)}%
            </span>
          </div>
        ))}
      </div>
    </motion.div>
  )
}
