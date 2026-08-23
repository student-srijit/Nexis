import React, { useEffect, useRef, useState } from 'react'
import { motion, useAnimation, useInView } from 'framer-motion'
import {
  Brain, Target, Zap, BarChart2, ArrowRight, Github,
  BookOpen, TrendingUp, ChevronRight, Star, Users, Award
} from 'lucide-react'

const STATS = [
  { value: '14K+', label: 'ESCO Skills Mapped', icon: Target },
  { value: '0.85', label: 'DKT AUC Score', icon: Brain },
  { value: '100%', label: 'Free & Open Source', icon: Star },
  { value: '3', label: 'ML Models Fused', icon: Zap },
]

const FEATURES = [
  {
    icon: Brain,
    color: '#7c3aed',
    title: 'Bayesian Knowledge Tracing',
    desc: 'Deep Knowledge Tracing LSTM (AUC 0.85) tracks your mastery per skill in real time. Not a progress bar — actual probabilistic inference over your quiz history.',
    badge: 'DKT + BKT'
  },
  {
    icon: Target,
    color: '#06b6d4',
    title: 'ESCO Skill Graph',
    desc: `Your skill gaps are computed via Dijkstra's shortest-path over a 14K-node ESCO occupational ontology. Node2Vec embeddings fuse structural graph signal with content.`,
    badge: 'Node2Vec'
  },
  {
    icon: BarChart2,
    color: '#10b981',
    title: 'LightGBM Ranker',
    desc: 'A gradient-boosted ranking model scores each course by fusing content similarity, mastery gap priority, and structural embeddings. NDCG@5 optimized.',
    badge: 'NDCG@5'
  },
  {
    icon: TrendingUp,
    color: '#f59e0b',
    title: 'Adaptive Replanning',
    desc: 'Every quiz updates your BKT posterior. The path automatically replans around your true mastery — not self-reported skill checks.',
    badge: 'Real-time'
  },
  {
    icon: Zap,
    color: '#ec4899',
    title: 'AI Explainer Agent',
    desc: 'Every recommendation comes with a grounded explanation: why this course, given your mastery scores, skill gaps, and graph distance to your target role.',
    badge: 'OpenRouter'
  },
  {
    icon: BookOpen,
    color: '#8b5cf6',
    title: 'Topological Path Planning',
    desc: 'Courses are sequenced respecting prerequisite dependencies from the skill graph. You never get ML before Statistics.',
    badge: 'DAG Planning'
  },
]

const TESTIMONIALS = [
  { quote: 'The most technically rigorous learning path system I\'ve seen.', name: 'AI Engineering Lead', role: 'Enterprise Tech' },
  { quote: 'Real ML models, not GPT wrappers. BKT + LightGBM + Node2Vec — this is production-grade.', name: 'AI Researcher', role: 'Tech Innovators' },
]

function AnimatedCounter({ target, duration = 2000 }) {
  const [count, setCount] = useState(0)
  const ref = useRef(null)
  const inView = useInView(ref, { once: true })

  useEffect(() => {
    if (!inView) return
    const num = parseFloat(target.replace(/[^0-9.]/g, ''))
    const suffix = target.replace(/[0-9.]/g, '')
    const start = Date.now()
    const timer = setInterval(() => {
      const elapsed = Date.now() - start
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setCount((eased * num).toFixed(num % 1 !== 0 ? 2 : 0) + suffix)
      if (progress === 1) clearInterval(timer)
    }, 16)
    return () => clearInterval(timer)
  }, [inView, target, duration])

  return <span ref={ref}>{inView ? count : '0'}</span>
}

export default function Landing({ onGetStarted }) {
  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)', overflow: 'hidden' }}>
      {/* ─── Nav ─── */}
      <nav style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
        background: 'rgba(10,10,20,0.7)', backdropFilter: 'blur(16px)',
        borderBottom: '1px solid var(--border-subtle)',
        padding: '0 32px', height: '60px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: 36, height: 36, borderRadius: '10px', background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 20px rgba(124,58,237,0.4)' }}>
            <Brain size={20} color="white" />
          </div>
          <span style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.2rem' }} className="gradient-text">Nexis</span>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <a href="https://github.com/student-srijit/Nexis" target="_blank" rel="noreferrer"
            style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.875rem', textDecoration: 'none' }}
            onMouseEnter={e => e.currentTarget.style.color = 'var(--text-primary)'}
            onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}
          >
            <Github size={16} /> GitHub
          </a>
          <button onClick={onGetStarted} className="btn-primary" id="nav-get-started" style={{ padding: '8px 20px', fontSize: '0.875rem' }}>
            Get Started <ArrowRight size={14} />
          </button>
        </div>
      </nav>

      {/* ─── Hero ─── */}
      <section style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', padding: '80px 24px 40px' }}>
        {/* Background glow orbs */}
        <div style={{ position: 'absolute', top: '20%', left: '10%', width: 500, height: 500, borderRadius: '50%', background: 'radial-gradient(circle, rgba(124,58,237,0.15) 0%, transparent 70%)', pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', top: '30%', right: '5%', width: 400, height: 400, borderRadius: '50%', background: 'radial-gradient(circle, rgba(6,182,212,0.12) 0%, transparent 70%)', pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', bottom: '10%', left: '30%', width: 350, height: 350, borderRadius: '50%', background: 'radial-gradient(circle, rgba(236,72,153,0.08) 0%, transparent 70%)', pointerEvents: 'none' }} />

        <div style={{ maxWidth: '860px', textAlign: 'center', position: 'relative', zIndex: 1 }}>
          {/* Badge */}
          <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <span className="badge badge-purple" style={{ fontSize: '0.8rem', padding: '6px 16px', marginBottom: '28px', display: 'inline-block' }}>
              🚀 Enterprise-Grade AI Learning Platform
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.7 }}
            style={{ fontSize: 'clamp(2.4rem, 6vw, 4.5rem)', lineHeight: 1.1, marginBottom: '24px', fontFamily: 'var(--font-display)', fontWeight: 900 }}
          >
            Your learning path,{' '}
            <span className="gradient-text">powered by real ML</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
            style={{ fontSize: '1.2rem', color: 'var(--text-secondary)', lineHeight: 1.7, maxWidth: '640px', margin: '0 auto 40px' }}
          >
            Not another GPT wrapper. Nexis fuses <strong style={{ color: 'var(--text-primary)' }}>Bayesian Knowledge Tracing</strong>,{' '}
            <strong style={{ color: 'var(--text-primary)' }}>LightGBM ranking</strong>, and a{' '}
            <strong style={{ color: 'var(--text-primary)' }}>Node2Vec skill graph</strong> to build a truly personalized path to your dream role.
          </motion.p>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
            style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}
          >
            <button onClick={onGetStarted} className="btn-primary" id="hero-get-started"
              style={{ padding: '14px 32px', fontSize: '1rem', justifyContent: 'center', boxShadow: '0 0 40px rgba(124,58,237,0.35)' }}
            >
              <Zap size={18} /> Build My Learning Path
            </button>
            <a href="https://github.com/student-srijit/Nexis" target="_blank" rel="noreferrer"
              style={{ textDecoration: 'none' }}
            >
              <button className="btn-ghost" style={{ padding: '14px 28px', fontSize: '1rem' }}>
                <Github size={18} /> View Source
              </button>
            </a>
          </motion.div>

          {/* Tech pill row */}
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.7 }}
            style={{ display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap', marginTop: '36px' }}
          >
            {['PyTorch · DKT LSTM', 'BKT · pyBKT', 'LightGBM Ranker', 'Node2Vec · Gensim', 'FAISS ANN', 'ESCO Ontology', 'FastAPI', 'Firebase'].map(t => (
              <span key={t} style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', borderRadius: '999px', padding: '4px 14px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>{t}</span>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ─── Stats ─── */}
      <section style={{ background: 'var(--bg-secondary)', borderTop: '1px solid var(--border-subtle)', borderBottom: '1px solid var(--border-subtle)', padding: '48px 24px' }}>
        <div style={{ maxWidth: 960, margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '32px' }}>
          {STATS.map(({ value, label, icon: Icon }) => (
            <motion.div key={label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              style={{ textAlign: 'center' }}
            >
              <Icon size={28} style={{ color: 'var(--accent-purple-light)', marginBottom: '12px' }} />
              <div style={{ fontSize: '2.5rem', fontWeight: 800, fontFamily: 'var(--font-display)' }} className="gradient-text">
                <AnimatedCounter target={value} />
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginTop: '4px' }}>{label}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ─── Features ─── */}
      <section style={{ padding: '80px 24px', maxWidth: 1200, margin: '0 auto' }}>
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} style={{ textAlign: 'center', marginBottom: '56px' }}>
          <h2 style={{ fontSize: 'clamp(1.8rem, 4vw, 2.8rem)', fontFamily: 'var(--font-display)', fontWeight: 800, marginBottom: '16px' }}>
            Not your average <span className="gradient-text">learning app</span>
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem', maxWidth: '560px', margin: '0 auto', lineHeight: 1.7 }}>
            Every component is a real ML model, trained on real data, explainable at every step.
          </p>
        </motion.div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          {FEATURES.map(({ icon: Icon, color, title, desc, badge }, i) => (
            <motion.div key={title}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              whileHover={{ y: -4, boxShadow: `0 20px 60px ${color}22` }}
              className="glass-card"
              style={{ padding: '28px', cursor: 'default', transition: 'all 0.25s' }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '16px' }}>
                <div style={{ width: 48, height: 48, borderRadius: '12px', background: `${color}22`, border: `1px solid ${color}44`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Icon size={22} color={color} />
                </div>
                <span style={{ background: `${color}22`, border: `1px solid ${color}44`, color, borderRadius: '999px', padding: '3px 10px', fontSize: '0.72rem', fontWeight: 600 }}>{badge}</span>
              </div>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '8px' }}>{title}</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', lineHeight: 1.65 }}>{desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ─── How It Works ─── */}
      <section style={{ background: 'var(--bg-secondary)', borderTop: '1px solid var(--border-subtle)', borderBottom: '1px solid var(--border-subtle)', padding: '80px 24px' }}>
        <div style={{ maxWidth: 960, margin: '0 auto' }}>
          <motion.h2 initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            style={{ textAlign: 'center', fontSize: 'clamp(1.6rem, 3.5vw, 2.4rem)', fontFamily: 'var(--font-display)', fontWeight: 800, marginBottom: '48px' }}
          >
            From goal to <span className="gradient-text">mastery</span> in 4 steps
          </motion.h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '24px' }}>
            {[
              { step: '01', title: 'Describe Your Goal', desc: 'Plain English. We extract your target role using NLP and map it to ESCO occupations.', color: '#7c3aed' },
              { step: '02', title: 'Diagnostic Quiz', desc: 'Short quiz calibrates your BKT priors. Your mastery scores are initialized, not guessed.', color: '#06b6d4' },
              { step: '03', title: 'ML Path Generation', desc: 'Gap analysis → Node2Vec + MiniLM retrieval → LightGBM ranking → topological ordering.', color: '#10b981' },
              { step: '04', title: 'Adaptive Replan', desc: 'Every quiz updates your BKT posterior. Your path evolves with you, automatically.', color: '#f59e0b' },
            ].map(({ step, title, desc, color }, i) => (
              <motion.div key={step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                style={{ textAlign: 'center', padding: '24px 16px' }}
              >
                <div style={{ width: 56, height: 56, borderRadius: '50%', background: `${color}20`, border: `2px solid ${color}60`, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px', fontSize: '0.85rem', fontWeight: 800, color, fontFamily: 'var(--font-display)' }}>{step}</div>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '8px' }}>{title}</h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', lineHeight: 1.6 }}>{desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section style={{ padding: '80px 24px', textAlign: 'center', position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', width: 600, height: 600, borderRadius: '50%', background: 'radial-gradient(circle, rgba(124,58,237,0.12) 0%, transparent 70%)', pointerEvents: 'none' }} />
        <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} style={{ position: 'relative', zIndex: 1, maxWidth: '600px', margin: '0 auto' }}>
          <h2 style={{ fontSize: 'clamp(1.8rem, 4vw, 2.8rem)', fontFamily: 'var(--font-display)', fontWeight: 900, marginBottom: '16px' }}>
            Ready to build your <span className="gradient-text">intelligent path?</span>
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', marginBottom: '36px', lineHeight: 1.7 }}>
            Sign in with Google. Free. Open source. Enterprise-grade ML under the hood.
          </p>
          <button onClick={onGetStarted} className="btn-primary" id="cta-get-started"
            style={{ padding: '16px 40px', fontSize: '1.05rem', justifyContent: 'center', boxShadow: '0 0 60px rgba(124,58,237,0.4)' }}
          >
            <Zap size={20} /> Get Started Free
          </button>
        </motion.div>
      </section>

      {/* ─── Footer ─── */}
      <footer style={{ background: 'var(--bg-secondary)', borderTop: '1px solid var(--border-subtle)', padding: '24px 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: 28, height: 28, borderRadius: '8px', background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Brain size={15} color="white" />
          </div>
          <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.95rem' }} className="gradient-text">Nexis</span>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>· AI-Powered Learning</span>
        </div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>
          Built with PyTorch · BKT · LightGBM · Node2Vec · FastAPI · React · Firebase
        </div>
        <a href="https://github.com/student-srijit/Nexis" target="_blank" rel="noreferrer"
          style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', textDecoration: 'none', fontSize: '0.82rem' }}
          onMouseEnter={e => e.currentTarget.style.color = 'var(--text-primary)'}
          onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}
        >
          <Github size={14} /> Open Source
        </a>
      </footer>
    </div>
  )
}
