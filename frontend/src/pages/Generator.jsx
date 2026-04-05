import { useState, useEffect, useRef } from 'react'
import {
  Sparkles, Terminal, Download, Eye, Loader2, UserCheck,
  Layout, Cpu, Database, Shield, ShieldCheck, ShieldAlert,
  ToggleLeft, ToggleRight, ChevronDown, ChevronUp
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'

const PERSONAS = [
  "Software Engineer", "Frontend Developer", "Backend Developer",
  "Fullstack Developer", "Mobile App Developer", "Data Scientist",
  "Machine Learning Engineer", "DevOps Engineer", "Product Manager",
  "UI/UX Designer", "Cloud Solutions Architect", "Site Reliability Engineer",
  "AI Research Engineer", "Data Engineer", "Cybersecurity Engineer"
]

const THEMES = [
  { id: 'dark',         name: 'Cyberpunk Dark',     accent: '#58a6ff' },
  { id: 'minimal',      name: 'Silicon Minimal',    accent: '#000000' },
  { id: 'creative',     name: 'Vibrant Creative',   accent: '#ff00ff' },
  { id: 'professional', name: 'Professional',       accent: '#2c3e50' },
  { id: 'modern',       name: 'Modern Sleek',       accent: '#6d28d9' },
]

// IndexedDB helpers
const initDB = () => new Promise((resolve, reject) => {
  const req = indexedDB.open('ProtofolioDB', 1)
  req.onupgradeneeded = e => {
    const db = e.target.result
    if (!db.objectStoreNames.contains('blueprints'))
      db.createObjectStore('blueprints', { keyPath: 'id', autoIncrement: true })
  }
  req.onsuccess = e => resolve(e.target.result)
  req.onerror   = e => reject(e.target.error)
})

const saveBlueprint = async (bp) => {
  const db = await initDB()
  const tx = db.transaction('blueprints', 'readwrite')
  tx.objectStore('blueprints').add({ ...bp, timestamp: new Date().toISOString() })
}

// ── Approval Verdict Card ─────────────────────────────────────────
function VerdictCard({ verdict }) {
  const [open, setOpen] = useState(false)
  if (!verdict) return null

  const decided = verdict.council_decision || 'APPROVED'
  const approved = verdict.approved !== false
  const score    = Math.round((verdict.confidence_score || 0.85) * 100)

  const colorMap = {
    APPROVED:    'emerald',
    CONDITIONAL: 'amber',
    REJECTED:    'red',
  }
  const col = colorMap[decided] || 'emerald'
  const Icon = decided === 'APPROVED' ? ShieldCheck : decided === 'CONDITIONAL' ? Shield : ShieldAlert

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`p-4 rounded-xl bg-${col}-500/5 border border-${col}-500/20`}
    >
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between"
      >
        <div className="flex items-center gap-2">
          <Icon size={16} className={`text-${col}-400`} />
          <span className={`text-xs font-black uppercase tracking-widest text-${col}-400`}>
            Council Verdict: {decided}
          </span>
          <span className={`px-2 py-0.5 rounded-full bg-${col}-500/10 text-${col}-400 text-[10px] font-bold`}>
            {score}% confidence
          </span>
        </div>
        {open ? <ChevronUp size={14} className="text-slate-500" /> : <ChevronDown size={14} className="text-slate-500" />}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="mt-4 space-y-3 text-xs text-slate-400">
              {verdict.tech_notes   && <p><span className="text-indigo-400 font-bold">⚙ Tech:</span> {verdict.tech_notes}</p>}
              {verdict.design_notes && <p><span className="text-purple-400 font-bold">🎨 Design:</span> {verdict.design_notes}</p>}
              {verdict.market_notes && <p><span className="text-amber-400 font-bold">📈 Market:</span> {verdict.market_notes}</p>}

              {verdict.key_strengths?.length > 0 && (
                <div>
                  <div className="text-emerald-400 font-bold mb-1">✓ Strengths</div>
                  <ul className="space-y-0.5 pl-2">
                    {verdict.key_strengths.map((s, i) => <li key={i}>• {s}</li>)}
                  </ul>
                </div>
              )}
              {verdict.gaps_to_address?.length > 0 && (
                <div>
                  <div className="text-amber-400 font-bold mb-1">△ Gaps to Address</div>
                  <ul className="space-y-0.5 pl-2">
                    {verdict.gaps_to_address.map((g, i) => <li key={i}>• {g}</li>)}
                  </ul>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default function Generator() {
  const [persona,      setPersona]      = useState(PERSONAS[0])
  const [theme,        setTheme]        = useState(THEMES[0].id)
  const [mode,         setMode]         = useState('rag')        // 'rag' | 'classic'
  const [isGenerating, setIsGenerating] = useState(false)
  const [logs,         setLogs]         = useState([])
  const [result,       setResult]       = useState(null)
  const [blueprint,    setBlueprint]    = useState(null)
  const [htmlPreview,  setHtmlPreview]  = useState('')
  const [ragInfo,      setRagInfo]      = useState(null)         // { chunk_counts, finetune_active }
  const logEndRef  = useRef(null)
  const navigate   = useNavigate()

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  useEffect(() => {
    const load = async () => {
      try {
        const db = await initDB()
        const tx = db.transaction('blueprints', 'readonly')
        const req = tx.objectStore('blueprints').getAll()
        req.onsuccess = () => {
          if (req.result.length > 0) setBlueprint(req.result[req.result.length - 1])
        }
      } catch (e) { console.error('DB Load Error', e) }
    }
    load()
  }, [])

  useEffect(() => {
    if (result) {
      const token = localStorage.getItem('token')
      axios.get(`http://localhost:5001/api/portfolio/${result}/preview?theme=${theme}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      .then(res => setHtmlPreview(res.data.html || ''))
      .catch(err => console.error('Preview fetch failed:', err))
    } else {
      setHtmlPreview('')
    }
  }, [result, theme])

  const startGeneration = async () => {
    setIsGenerating(true)
    setLogs([])
    setResult(null)
    setBlueprint(null)
    setRagInfo(null)

    const token = localStorage.getItem('token')
    try {
      const response = await fetch('http://localhost:5001/api/portfolio/generate/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ job_goal: persona, theme, mode })
      })

      const reader  = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        for (const line of chunk.split('\n')) {
          if (!line.startsWith('data: ')) continue
          try {
            const data = JSON.parse(line.substring(6))
            if (data.type === 'status') {
              setLogs(prev => [...prev, { agent: data.agent, message: data.message, time: new Date().toLocaleTimeString() }])
            } else if (data.type === 'rag_chunks') {
              setRagInfo({ chunk_counts: data.chunk_counts, total: data.total, finetune_active: false })
            } else if (data.type === 'complete') {
              setBlueprint(data.blueprint)
              saveBlueprint(data.blueprint)
              setRagInfo({ chunk_counts: data.chunk_counts, total: Object.values(data.chunk_counts || {}).reduce((a,b)=>a+b,0), finetune_active: data.finetune_active })
            } else if (data.type === 'save_complete') {
              setResult(data.portfolio_id)
              setIsGenerating(false)
              if (data.finetune_active !== undefined)
                setRagInfo(prev => ({ ...prev, finetune_active: data.finetune_active }))
            }
          } catch (e) { console.error('SSE parse error', e) }
        }
      }
    } catch (err) {
      setLogs(prev => [...prev, { agent: 'System', message: 'Fatal Error: ' + err.message }])
      setIsGenerating(false)
    }
  }

  const downloadZip = () => {
    const token = localStorage.getItem('token')
    window.location.href = `http://localhost:5001/api/portfolio/${result}/export?theme=${theme}&token=${token}`
  }

  const downloadJSON = () => {
    const blob = new Blob([JSON.stringify(blueprint, null, 2)], { type: 'application/json' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href = url; a.download = `blueprint-${persona.replace(/ /g,'-')}.json`; a.click()
  }

  const printResume = () => {
    if (!htmlPreview) return
    const w = window.open('', '_blank')
    w.document.write(htmlPreview)
    w.document.close()
    w.focus()
    setTimeout(() => w.print(), 500)
  }

  return (
    <div className="p-8 md:p-12 max-w-6xl mx-auto space-y-12">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-2">
          <h1 className="text-5xl font-black text-white">Council Hub</h1>
          <p className="text-slate-400 text-lg">Instruct the AI council on your target career persona.</p>
        </div>

        {!isGenerating && !result && (
          <div className="flex items-center gap-3">
            {/* RAG / Classic toggle */}
            <button
              onClick={() => setMode(m => m === 'rag' ? 'classic' : 'rag')}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl border text-sm font-bold transition-all ${
                mode === 'rag'
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                  : 'bg-white/5 border-white/10 text-slate-400'
              }`}
            >
              {mode === 'rag'
                ? <><ToggleRight size={18} /> RAG Mode</>
                : <><ToggleLeft  size={18} /> Classic Mode</>
              }
            </button>
            <button
              onClick={startGeneration}
              className="premium-gradient group h-16 px-10 rounded-2xl flex items-center justify-center gap-3 font-bold text-lg shadow-2xl shadow-indigo-500/20"
            >
              <Sparkles size={22} className="group-hover:rotate-12 transition-transform" />
              Start Deliberation
            </button>
          </div>
        )}
      </header>

      {!isGenerating && !result ? (
        <div className="grid md:grid-cols-2 gap-8 animate-fade">
          <div className="card space-y-8 h-fit">
            <div className="space-y-4">
              <label className="text-sm font-bold text-indigo-400 uppercase tracking-widest">Select Persona</label>
              <select value={persona} onChange={e => setPersona(e.target.value)} className="w-full text-lg font-semibold h-14">
                {PERSONAS.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
              <p className="text-sm text-slate-500">
                {mode === 'rag'
                  ? '⚡ RAG Mode: Chairman SME synthesises your profile in a single call (70-80% fewer tokens).'
                  : '🔄 Classic Mode: Full 7-agent Council deliberation pipeline.'}
              </p>
            </div>

            <div className="space-y-4">
              <label className="text-sm font-bold text-indigo-400 uppercase tracking-widest">Global Theme</label>
              <div className="grid grid-cols-3 gap-3">
                {THEMES.map(t => (
                  <button
                    key={t.id}
                    onClick={() => setTheme(t.id)}
                    className={`p-4 rounded-xl border-2 transition-all text-center ${
                      theme === t.id
                        ? 'border-indigo-500 bg-indigo-500/10'
                        : 'border-[#26262e] bg-[#16161e] hover:border-white/10'
                    }`}
                  >
                    <div className="text-sm font-bold">{t.name}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-[#121218] rounded-3xl border border-[#26262e] p-8 flex flex-col justify-center items-center text-center space-y-6">
            <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center border border-white/10">
              <Cpu size={40} className="text-white/20" />
            </div>
            <div className="space-y-2">
              <h3 className="text-xl font-bold">Agents Awaiting Instructions</h3>
              <p className="text-slate-500 max-w-xs mx-auto">
                {mode === 'rag'
                  ? 'RAG Mode will retrieve your indexed profile and synthesise the portfolio in one optimised call.'
                  : 'Classic Mode routes through all 3 council agents + Chairman for maximum deliberation depth.'}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-8">
          {/* RAG Info bar */}
          <AnimatePresence>
            {ragInfo && (
              <motion.div
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-4 px-5 py-3 rounded-2xl border border-emerald-500/20 bg-emerald-500/5"
              >
                <Database size={16} className="text-emerald-400" />
                <span className="text-xs font-bold text-emerald-300">
                  ⚡ RAG Mode — {ragInfo.total || 0} vectors retrieved
                  {ragInfo.finetune_active && ' · Fine-Tuned Model Active 🔥'}
                </span>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="md:col-span-2 space-y-8">
              {/* Deliberation Logs */}
              <div className="card bg-black/40 border-indigo-500/20 h-[300px] flex flex-col p-0 overflow-hidden">
                <div className="p-4 border-b border-indigo-500/10 bg-indigo-500/5 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-indigo-400 font-bold">
                    <Terminal size={18} />
                    <span>Agent Deliberation Logs</span>
                  </div>
                  {isGenerating && <Loader2 size={18} className="animate-spin text-indigo-500" />}
                </div>
                <div className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-hide">
                  <AnimatePresence mode="popLayout">
                    {logs.map((log, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="flex gap-4 items-start"
                      >
                        <span className="text-[10px] font-mono text-slate-600 mt-1">{log.time}</span>
                        <div className="space-y-1">
                          <span className={`text-xs font-black uppercase tracking-tighter ${
                            log.agent === 'RAG' ? 'text-emerald-500/80' :
                            log.agent === 'Chairman SME' ? 'text-amber-500/80' :
                            'text-indigo-500/80'
                          }`}>[{log.agent}]</span>
                          <p className="text-sm text-slate-300 leading-relaxed">{log.message}</p>
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                  <div ref={logEndRef} />
                </div>
              </div>

              {/* Live Sandbox */}
              <div className="card p-0 overflow-hidden border-white/5 bg-[#0a0a0f] h-[500px] relative">
                <div className="absolute top-4 left-4 z-10 flex gap-2">
                  <div className="px-3 py-1 bg-white/10 backdrop-blur-md rounded-full text-[10px] font-bold border border-white/10 tracking-widest uppercase">Live Sandbox</div>
                  {isGenerating && <div className="px-3 py-1 bg-indigo-500/20 text-indigo-400 rounded-full text-[10px] font-bold border border-indigo-500/20 uppercase animate-pulse">Rendering...</div>}
                  {mode === 'rag' && <div className="px-3 py-1 bg-emerald-500/20 text-emerald-400 rounded-full text-[10px] font-bold border border-emerald-500/20 uppercase">RAG Mode</div>}
                </div>
                {result ? (
                  <pre className="w-full h-full p-8 pt-16 overflow-auto text-emerald-400 font-mono text-sm scrollbar-hide">
                    {JSON.stringify(blueprint, null, 2)}
                  </pre>
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center text-slate-700 space-y-4">
                    <Eye size={48} className="opacity-20" />
                    <p className="font-medium">Sandbox activates once blueprint is finalised</p>
                  </div>
                )}
              </div>
            </div>

            {/* Blueprint Synthesis Panel */}
            <div className="space-y-4">
              <div className="card h-fit bg-gradient-to-b from-[#16161e] to-black sticky top-8">
                <h3 className="font-bold mb-6 flex items-center gap-2">
                  <UserCheck size={18} className="text-emerald-500" />
                  Blueprint Synthesis
                </h3>

                {blueprint ? (
                  <div className="space-y-5">
                    <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
                      <div className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest mb-1">Generated Tagline</div>
                      <div className="font-bold text-white text-pretty">{blueprint.tagline}</div>
                    </div>

                    {/* Approval Verdict */}
                    <VerdictCard verdict={blueprint.approval_verdict} />

                    {blueprint.template_dif && (
                      <div className="p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/20">
                        <div className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-2 flex items-center gap-1">
                          <Cpu size={12} /> Visual Diff Applied
                        </div>
                        <ul className="text-xs text-slate-400 space-y-1">
                          {blueprint.template_dif.map((d, i) => <li key={i} className="flex gap-2"><span>•</span> {d}</li>)}
                        </ul>
                      </div>
                    )}

                    <div>
                      <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3">Core Stack</div>
                      <div className="flex flex-wrap gap-2">
                        {blueprint.tech_stack?.map(t => (
                          <span key={t} className="px-2 py-1 rounded-md bg-white/5 border border-white/10 text-[10px] font-medium">{t}</span>
                        ))}
                      </div>
                    </div>

                    {result && (
                      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="pt-4 space-y-3">
                        <button
                          onClick={() => {
                            const token = localStorage.getItem('token')
                            window.open(`http://localhost:5001/api/portfolio/${result}/preview?theme=${theme}&token=${token}&raw=true`, '_blank')
                          }}
                          className="w-full bg-indigo-500 hover:bg-indigo-600 transition-colors text-white font-bold h-12 flex items-center justify-center gap-2 rounded-xl"
                        >
                          <Eye size={18} /> Review Live HTML
                        </button>
                        <button onClick={printResume} className="w-full bg-white text-black font-bold h-12 flex items-center justify-center gap-2 rounded-xl">
                          <Download size={18} /> Download PDF
                        </button>
                        <button onClick={downloadJSON} className="w-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-bold h-12 flex items-center justify-center gap-2 rounded-xl">
                          <Terminal size={18} /> Download JSON
                        </button>
                        <button onClick={downloadZip} className="w-full bg-[#26262e] text-white font-bold h-12 flex items-center justify-center gap-2 rounded-xl">
                          <Download size={18} /> Export ZIP Source
                        </button>
                      </motion.div>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-64 text-slate-600">
                    <Layout size={32} className="mb-2 opacity-20" />
                    <span className="text-sm font-medium text-center">Assembling AI Blueprint from Memory...</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
