import { useState } from 'react'
import axios from 'axios'
import { FileUp, Link, User, CheckCircle2, Loader2 } from 'lucide-react'

export default function Setup() {
  const [loading, setLoading] = useState(null)
  const [status, setStatus] = useState({})
  const token = localStorage.getItem('token')

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
      await api.post('/ingest/resume', formData)
      setStatus(prev => ({ ...prev, resume: true }))
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
      await api.post('/ingest/linkedin', { linkedin_url: url })
      setStatus(prev => ({ ...prev, linkedin: true }))
    } catch (err) {
      alert('LinkedIn sync failed')
    } finally {
      setLoading(null)
    }
  }

  const syncGithub = async () => {
    setLoading('github')
    try {
      await api.post('/ingest/github')
      setStatus(prev => ({ ...prev, github: true }))
    } catch (err) {
      alert('GitHub sync failed')
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="p-12 max-w-5xl mx-auto space-y-12 animate-fade">
      <header className="space-y-4">
        <h1 className="text-4xl font-black">Data Ingestion</h1>
        <p className="text-slate-400 text-lg">Initialize your agent's memory with your professional profile.</p>
      </header>

      <div className="grid md:grid-cols-2 gap-8">
        {/* Resume */}
        <div className={`card group transition-all duration-300 ${status.resume ? 'border-indigo-500/50' : 'hover:border-white/20'}`}>
          <div className="flex items-start justify-between mb-6">
            <div className="p-3 rounded-2xl bg-indigo-500/10 text-indigo-400">
              <FileUp size={28} />
            </div>
            {status.resume && <CheckCircle2 className="text-indigo-500" />}
          </div>
          <h3 className="text-xl font-bold mb-2">Upload Resume</h3>
          <p className="text-slate-400 mb-6 font-medium leading-relaxed">Agentic parser will extract skills, experience, and key metrics from PDF.</p>
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
        </div>

        {/* LinkedIn */}
        <div className={`card group transition-all duration-300 ${status.linkedin ? 'border-sky-500/50' : 'hover:border-white/20'}`}>
          <div className="flex items-start justify-between mb-6">
            <div className="p-3 rounded-2xl bg-sky-500/10 text-sky-400">
              <Link size={28} />
            </div>
            {status.linkedin && <CheckCircle2 className="text-sky-500" />}
          </div>
          <h3 className="text-xl font-bold mb-2">LinkedIn Profile</h3>
          <p className="text-slate-400 mb-6 font-medium leading-relaxed">Input your URL for real-time scraping and persona matching.</p>
          <form onSubmit={syncLinkedIn} className="flex gap-2">
            <input 
              name="linkedinUrl" 
              placeholder="https://linkedin.com/in/..." 
              required
              className="flex-1 bg-white/5 border-white/10 mb-0"
            />
            <button disabled={loading === 'linkedin'} className="bg-sky-500 hover:bg-sky-600">
              {loading === 'linkedin' ? <Loader2 className="animate-spin" /> : 'Sync'}
            </button>
          </form>
        </div>

        {/* Github */}
        <div className={`card md:col-span-2 flex items-center justify-between transition-all duration-300 ${status.github ? 'border-emerald-500/50' : 'hover:border-white/20'}`}>
          <div className="flex items-center gap-6">
            <div className="p-3 rounded-2xl bg-emerald-500/10 text-emerald-400">
              <User size={28} />
            </div>
            <div>
              <h3 className="text-xl font-bold mb-1">GitHub Repositories</h3>
              <p className="text-slate-400 font-medium">Auto-index top 10 repos by star count for technical evidence.</p>
            </div>
          </div>
          <button 
            onClick={syncGithub}
            disabled={loading === 'github'}
            className="bg-emerald-500 hover:bg-emerald-600 px-8"
          >
            {loading === 'github' ? <Loader2 className="animate-spin" /> : status.github ? 'Re-Sync' : 'Start Sync'}
          </button>
        </div>
      </div>
    </div>
  )
}
