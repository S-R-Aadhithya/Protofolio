import { useState, useEffect } from 'react'
import axios from 'axios'
import { FileUp, Link, User, CheckCircle2, Loader2, Code, Database, Sparkles, AlertCircle } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'

// ── RAG status badge ─────────────────────────────────────────────
function RagBadge({ count, label }) {
  if (!count) return null
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30"
    >
      <Database size={10} className="text-emerald-400" />
      <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest">
        RAG {label}: {count} chunks
      </span>
    </motion.div>
  )
}

// ── Per-source summary preview ───────────────────────────────────
function SummaryCard({ title, summary }) {
  if (!summary) return null
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-4 p-4 bg-emerald-500/5 rounded-xl border border-emerald-500/20"
    >
      <div className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest mb-2 flex items-center gap-1.5">
        <Sparkles size={10} />Chairman SME Summary
      </div>
      <p className="text-xs text-slate-300 leading-relaxed">{summary}</p>
    </motion.div>
  )
}

export default function Setup() {
  const [loading, setLoading] = useState(null)
  const [status, setStatus] = useState({})
  const [ragStatus, setRagStatus] = useState({})      // { resume: N, linkedin: N, github: N }
  const [summaries, setSummaries] = useState({})      // chairman SME summaries per source
  const [searchParams, setSearchParams] = useSearchParams()
  const token = localStorage.getItem('token')

  useEffect(() => {
    const newToken = searchParams.get('token')
    const user = searchParams.get('user')
    if (newToken) {
      localStorage.setItem('token', newToken)
      localStorage.setItem('github_user', user)
      setSearchParams({})
      setStatus(prev => ({ ...prev, github: true }))
    } else if (!status.github && localStorage.getItem('github_user')) {
      setStatus(prev => ({ ...prev, github: true }))
    }
  }, [searchParams, setSearchParams, status.github])

  const api = axios.create({
    baseURL: 'http://localhost:5001/api',
    headers: { Authorization: `Bearer ${token}` }
  })

  const uploadResume = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setLoading('resume')
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await api.post('/ingest/resume', formData)
      setStatus(prev => ({ ...prev, resume: res.data.extracted_text }))
      if (res.data.chunk_counts) setRagStatus(prev => ({ ...prev, ...res.data.chunk_counts }))
      if (res.data.chairman_summary) setSummaries(prev => ({ ...prev, resume: res.data.chairman_summary }))
    } catch (err) {
      alert('Upload failed')
    } finally {
      setLoading(null)
    }
  }

  const syncLinkedIn = async (e) => {
    e.preventDefault()
    const url = e.target.linkedinUrl.value
    setLoading('linkedin')
    try {
      const res = await api.post('/ingest/linkedin', { linkedin_url: url })
      setStatus(prev => ({ ...prev, linkedin: res.data.summary }))
      if (res.data.chunk_counts) setRagStatus(prev => ({ ...prev, ...res.data.chunk_counts }))
      if (res.data.chairman_summary) setSummaries(prev => ({ ...prev, linkedin: res.data.chairman_summary }))
    } catch (err) {
      alert('LinkedIn sync failed')
    } finally {
      setLoading(null)
    }
  }

  const syncGithub = async () => {
    setLoading('github')
    try {
      const res = await api.post('/ingest/github')
      setStatus(prev => ({ ...prev, github: res.data.repos }))
      if (res.data.chunk_counts) setRagStatus(prev => ({ ...prev, ...res.data.chunk_counts }))
      if (res.data.chairman_summary) setSummaries(prev => ({ ...prev, github: res.data.chairman_summary }))
    } catch (err) {
      alert('GitHub sync failed')
    } finally {
      setLoading(null)
    }
  }

  const totalChunks = Object.values(ragStatus).reduce((a, b) => a + b, 0)

  return (
    <div className="p-12 max-w-5xl mx-auto space-y-12 animate-fade">
      <header className="space-y-4">
        <h1 className="text-4xl font-black">Data Ingestion</h1>
        <p className="text-slate-400 text-lg">Initialize your agent&apos;s memory with your professional profile.</p>
      </header>

      {/* ── RAG Memory Status Bar ─────────────────────────────── */}
      <AnimatePresence>
        {totalChunks > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex items-center gap-4 p-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/5"
          >
            <div className="p-2 rounded-xl bg-emerald-500/10">
              <Database size={20} className="text-emerald-400" />
            </div>
            <div className="flex-1">
              <div className="text-sm font-bold text-emerald-300 mb-1">RAG Memory Active — {totalChunks} vectors indexed</div>
              <div className="flex items-center gap-3">
                <RagBadge count={ragStatus.resume}   label="Resume"   />
                <RagBadge count={ragStatus.linkedin} label="LinkedIn" />
                <RagBadge count={ragStatus.github}   label="GitHub"   />
              </div>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
              <Sparkles size={12} className="text-emerald-400" />
              <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest">RAG Ready</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid md:grid-cols-2 gap-8">
        {/* Resume */}
        <div className={`card group transition-all duration-300 ${status.resume ? 'border-white/50' : 'hover:border-white/20'}`}>
          <div className="flex items-start justify-between mb-6">
            <div className="p-3 rounded-2xl bg-white/10 text-white">
              <FileUp size={28} />
            </div>
            <div className="flex items-center gap-2">
              {ragStatus.resume > 0 && <RagBadge count={ragStatus.resume} label="Indexed" />}
              {status.resume && <CheckCircle2 className="text-white" />}
            </div>
          </div>
          <h3 className="text-xl font-bold mb-2">Upload Resume</h3>
          <p className="text-slate-400 mb-6 font-medium leading-relaxed">Agentic parser extracts skills, experience, and key metrics from PDF — then embeds directly into ChromaDB.</p>
          <label className="block">
            <input
              type="file"
              className="hidden"
              accept=".pdf"
              onChange={uploadResume}
              disabled={loading === 'resume'}
            />
            <div className="w-full py-3 bg-white/5 border border-white/10 rounded-xl text-center font-bold cursor-pointer hover:bg-white/10 transition-colors">
              {loading === 'resume' ? <Loader2 className="animate-spin mx-auto" /> : 'Choose PDF File'}
            </div>
          </label>
          {typeof status.resume === 'string' && (
            <div className="mt-4 p-4 bg-white/5 rounded-xl border border-white/10 max-h-32 overflow-y-auto">
              <p className="text-xs text-slate-400 font-mono leading-relaxed line-clamp-5">{status.resume}</p>
            </div>
          )}
          <SummaryCard title="Resume" summary={summaries.resume} />
        </div>

        {/* LinkedIn */}
        <div className={`card group transition-all duration-300 ${status.linkedin ? 'border-white/50' : 'hover:border-white/20'}`}>
          <div className="flex items-start justify-between mb-6">
            <div className="p-3 rounded-2xl bg-white/10 text-white">
              <Link size={28} />
            </div>
            <div className="flex items-center gap-2">
              {ragStatus.linkedin > 0 && <RagBadge count={ragStatus.linkedin} label="Indexed" />}
              {status.linkedin && <CheckCircle2 className="text-white" />}
            </div>
          </div>
          <h3 className="text-xl font-bold mb-2">LinkedIn Profile</h3>
          <p className="text-slate-400 mb-6 font-medium leading-relaxed">Real-time scraping and persona matching — embedded into RAG memory.</p>
          <form onSubmit={syncLinkedIn} className="flex gap-2">
            <input
              name="linkedinUrl"
              placeholder="https://linkedin.com/in/..."
              autoComplete="off"
              required
              className="flex-1 bg-white/5 border-white/10 mb-0"
            />
            <button disabled={loading === 'linkedin'} className="bg-white text-black hover:bg-gray-200">
              {loading === 'linkedin' ? <Loader2 className="animate-spin text-black" /> : 'Sync'}
            </button>
          </form>
          {typeof status.linkedin === 'string' && (
            <div className="mt-4 p-4 bg-black/40 rounded-xl border border-white/5 max-h-24 overflow-y-auto">
              <p className="text-xs text-slate-300 font-mono break-words">{status.linkedin}</p>
            </div>
          )}
          <SummaryCard title="LinkedIn" summary={summaries.linkedin} />
        </div>

        {/* GitHub */}
        <div className={`card md:col-span-2 flex flex-col gap-6 transition-all duration-300 ${status.github ? 'border-white/50' : 'hover:border-white/20'}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div className="p-3 rounded-2xl bg-white/10 text-white"><User size={28} /></div>
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <h3 className="text-xl font-bold">GitHub Repositories</h3>
                  {ragStatus.github > 0 && <RagBadge count={ragStatus.github} label="Indexed" />}
                </div>
                <p className="text-slate-400 font-medium">Auto-index top 10 repos by star count for technical evidence.</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {!status.github && (
                <a
                  href="http://localhost:5001/api/auth/github/login"
                  className="bg-[#24292e] hover:bg-[#1a1e22] text-white px-6 py-2 rounded-xl flex items-center gap-2 font-bold transition-colors"
                >
                  <Code size={20} />Connect
                </a>
              )}
              <button
                onClick={syncGithub}
                disabled={loading === 'github'}
                className="bg-white hover:bg-gray-200 text-black px-8"
              >
                {loading === 'github' ? <Loader2 className="animate-spin text-black" /> : status.github ? 'Re-Sync Data' : 'Start Sync'}
              </button>
            </div>
          </div>

          {Array.isArray(status.github) && status.github.length > 0 && (
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
              {status.github.slice(0, 6).map((repo, idx) => (
                <div key={idx} className="p-4 bg-white/5 border border-white/10 rounded-xl">
                  <h4 className="font-bold text-sm text-white mb-1 truncate">{repo.name}</h4>
                  <p className="text-xs text-slate-400 line-clamp-2">{repo.description || 'No description provided.'}</p>
                  <div className="mt-3 flex items-center gap-4 text-xs font-mono text-slate-500">
                    {repo.language && <span>{repo.language}</span>}
                    <span>★ {repo.stars}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
          <SummaryCard title="GitHub" summary={summaries.github} />
        </div>
      </div>
    </div>
  )
}
