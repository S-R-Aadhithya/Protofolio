import { useState, useEffect } from 'react'
import axios from 'axios'
import { Eye, Download, History, BarChart3, Clock, Layout } from 'lucide-react'
import { motion } from 'framer-motion'

export default function Dashboard() {
  const [portfolios, setPortfolios] = useState([])
  const [loading, setLoading] = useState(true)
  const token = localStorage.getItem('token')

  const api = axios.create({
    baseURL: 'http://localhost:5001/api/portfolio',
    headers: { Authorization: `Bearer ${token}` }
  })

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const resp = await api.get('/list')
        setPortfolios(resp.data)
      } catch (err) {
        console.error("Fetch history failed", err)
      } finally {
        setLoading(false)
      }
    }
    fetchHistory()
  }, [])

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-[80vh] gap-4">
      <div className="w-12 h-12 border-4 border-white/10 border-t-white/80 rounded-full animate-spin"></div>
      <span className="font-bold text-slate-500">Retrieving Generation Archive...</span>
    </div>
  )

  return (
    <div className="p-8 md:p-12 max-w-7xl mx-auto space-y-12 animate-fade">
      <header className="space-y-2">
        <h1 className="text-4xl font-black">Generation Archive</h1>
        <p className="text-slate-400">Review your previously generated SPA portfolios and their engagement stats.</p>
      </header>

      {portfolios.length === 0 ? (
        <div className="bg-[#121218] rounded-3xl border border-[#26262e] p-24 text-center">
          <History size={48} className="mx-auto mb-6 text-slate-700" />
          <h3 className="text-2xl font-bold mb-2">No History Yet</h3>
          <p className="text-slate-500 max-w-xs mx-auto mb-8">Once the AI Council completes its first deliberation, your artifacts will appear here.</p>
          <button onClick={() => window.location.href='/generate'} className="bg-white text-black font-bold h-12 px-8">Start First Run</button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {portfolios.map((p, i) => (
            <motion.div 
              key={p.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="card bg-[#16161e] group overflow-hidden border-white/5 hover:border-white/10 transition-all"
            >
              <div className="h-40 bg-indigo-500/5 border-b border-white/5 relative overflow-hidden flex items-center justify-center">
                 <Layout size={40} className="text-white/5 scale-150 rotate-12" />
                 <div className="absolute top-4 left-4 bg-black/40 px-3 py-1 rounded-full text-[10px] font-bold tracking-widest text-white/60">#00{p.id}</div>
              </div>
              <div className="p-6 space-y-4">
                <div className="space-y-1">
                  <h3 className="text-lg font-bold text-white group-hover:text-indigo-400 transition-colors line-clamp-1">{p.title}</h3>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <Clock size={12} />
                    {new Date(p.created_at).toLocaleDateString()}
                  </div>
                </div>

                <div className="bg-white/5 rounded-xl p-4 flex justify-between items-center">
                  <div className="flex flex-col">
                    <span className="text-[10px] uppercase font-bold text-slate-500">Total Views</span>
                    <span className="text-xl font-black text-indigo-400 flex items-center gap-2">
                       <BarChart3 size={16} /> 
                       {p.views || 0}
                    </span>
                  </div>
                  <div className="bg-indigo-400/10 px-3 py-1 rounded-lg text-indigo-400 text-xs font-bold">{p.role}</div>
                </div>

                <div className="flex gap-2 pt-2">
                   <button 
                     onClick={() => window.open(`http://localhost:5001/api/portfolio/${p.id}/preview?theme=dark`, '_blank')}
                     className="flex-1 bg-white/5 hover:bg-white/10 text-white font-bold h-11 text-xs flex items-center justify-center gap-2"
                   >
                     <Eye size={16} /> Preview
                   </button>
                   <button 
                     onClick={() => window.location.href=`http://localhost:5001/api/portfolio/${p.id}/export?theme=dark&token=${token}`}
                     className="flex-1 bg-indigo-500 hover:bg-indigo-600 text-white font-bold h-11 text-xs flex items-center justify-center gap-2"
                   >
                     <Download size={16} /> Export
                   </button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
