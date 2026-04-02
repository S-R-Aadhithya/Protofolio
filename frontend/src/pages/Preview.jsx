import { useParams, useSearchParams } from 'react-router-dom'

export default function Preview() {
  const { id } = useParams()
  const [searchParams] = useSearchParams()
  const theme = searchParams.get('theme') || 'dark'
  const token = localStorage.getItem('token')

  return (
    <div className="h-screen w-full flex flex-col bg-black">
      <div className="h-14 bg-[#16161e] border-b border-[#26262e] px-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
           <span className="font-bold text-sm tracking-tight">SPA Preview</span>
           <div className="flex items-center gap-2 px-2 py-0.5 rounded bg-white/5 border border-white/10 text-[10px] font-mono text-slate-400">
             ID: {id} | THEME: {theme.toUpperCase()}
           </div>
        </div>
        <button 
          onClick={() => window.history.back()}
          className="text-xs font-bold text-slate-400 hover:text-white transition-colors"
        >
          Exit Preview
        </button>
      </div>
      <iframe 
        src={`http://localhost:5001/api/portfolio/${id}/preview?theme=${theme}&token=${token}`}
        className="flex-1 w-full border-0"
        title="Portfolio Preview"
      />
    </div>
  )
}
