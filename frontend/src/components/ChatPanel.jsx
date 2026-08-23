import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Loader2, Bot, User, Sparkles } from 'lucide-react'
import { useStore } from '../utils/store'
import { chat } from '../utils/api'
import toast from 'react-hot-toast'

export default function ChatPanel({ courseId = null, compact = false }) {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: courseId
        ? "Ask me anything about this course — I'll explain exactly why it's recommended for you based on your mastery scores and skill gaps."
        : "Hi! I'm your AI learning assistant. Ask me why any course was recommended, or about your skill gaps. Every answer I give is grounded in your actual mastery scores and learning path data.",
    },
  ])
  const bottomRef = useRef(null)
  const { learnerId } = useStore()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return
    const userMsg = { role: 'user', content: input.trim() }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const history = messages.slice(-8).map((m) => ({ role: m.role, content: m.content }))
      const res = await chat(learnerId, userMsg.content, history, courseId)
      const reply = res.data.reply
      setMessages((prev) => [...prev, { role: 'assistant', content: reply }])
    } catch (err) {
      const errMsg = err.response?.data?.detail || 'Connection error. Is the backend running?'
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: `⚠ ${errMsg}\n\nTip: Start the backend with \`uvicorn app.main:app --reload\` from the backend/ directory.`
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  return (
    <div className={`glass-card flex flex-col ${compact ? '' : ''}`} style={{ height: compact ? '420px' : '560px' }}>
      {/* Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        display: 'flex', alignItems: 'center', gap: '10px'
      }}>
        <div style={{
          width: 36, height: 36, borderRadius: '50%',
          background: 'linear-gradient(135deg, #7c3aed, #06b6d4)',
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
          <Sparkles size={18} color="white" />
        </div>
        <div>
          <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>AI Explainer</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Powered by Gemini · Constrained to your actual data
          </div>
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <AnimatePresence initial={false}>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
              style={{
                display: 'flex',
                gap: '10px',
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
              }}
            >
              {/* Avatar */}
              <div style={{
                width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
                background: msg.role === 'user'
                  ? 'linear-gradient(135deg, #06b6d4, #7c3aed)'
                  : 'linear-gradient(135deg, #7c3aed, #ec4899)',
                display: 'flex', alignItems: 'center', justifyContent: 'center'
              }}>
                {msg.role === 'user' ? <User size={15} color="white" /> : <Bot size={15} color="white" />}
              </div>

              {/* Bubble */}
              <div style={{
                maxWidth: '78%',
                padding: '10px 14px',
                borderRadius: msg.role === 'user' ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
                background: msg.role === 'user'
                  ? 'linear-gradient(135deg, rgba(124,58,237,0.3), rgba(6,182,212,0.2))'
                  : 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                fontSize: '0.875rem',
                lineHeight: 1.6,
                color: 'var(--text-primary)',
                whiteSpace: 'pre-wrap',
              }}>
                {msg.content}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {loading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, #7c3aed, #ec4899)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Bot size={15} color="white" />
            </div>
            <div style={{ padding: '10px 14px', borderRadius: '4px 16px 16px 16px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', display: 'flex', gap: '6px', alignItems: 'center' }}>
              <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} color="var(--accent-purple-light)" />
              <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Analyzing your data…</span>
            </div>
          </motion.div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ padding: '12px 16px', borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', gap: '8px' }}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask about a course, your skill gaps, or why something was recommended…"
          rows={2}
          style={{ resize: 'none', flex: 1, fontSize: '0.875rem', padding: '10px 14px' }}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || loading}
          className="btn-primary"
          style={{ padding: '10px 16px', alignSelf: 'flex-end' }}
          id="chat-send-btn"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  )
}
