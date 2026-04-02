import { useState, useEffect } from 'react'
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import { Layout, User, Settings, PieChart, Sparkles, LogOut, Globe } from 'lucide-react'
import Setup from './pages/Setup'
import Generator from './pages/Generator'
import Dashboard from './pages/Dashboard'
import Preview from './pages/Preview'

function App() {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token'))
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const urlToken = params.get('token')
    const urlUser = params.get('user')
    
    if (urlToken) {
      localStorage.setItem('token', urlToken)
      setToken(urlToken)
      if (urlUser) localStorage.setItem('user', urlUser)
      // Following a fresh login, redirect to the setup page to initialize memory.
      navigate('/setup', { replace: true })
    }
  }, [location, navigate])

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setToken(null)
    setUser(null)
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-[#0d0d12] text-white flex relative overflow-hidden">
      {/* Dynamic Background Gradient */}
      <div className="fixed inset-0 bg-radial -z-10 animate-pulse pointer-events-none" />
      
      {token && location.pathname !== '/preview' && (
        <aside className="w-64 glass border-r border-[#26262e] flex flex-col p-6 fixed h-screen top-0 left-0 hidden md:flex">
          <div className="flex items-center gap-3 mb-10">
            <div className="w-8 h-8 rounded-lg premium-gradient flex items-center justify-center">
              <Sparkles size={18} />
            </div>
            <span className="font-bold text-xl tracking-tight">Protofolio</span>
          </div>

          <nav className="flex-1 space-y-2">
            {[
              { path: '/setup', label: 'Setup', icon: Settings },
              { path: '/generate', label: 'Council Hub', icon: Sparkles },
              { path: '/dashboard', label: 'History', icon: PieChart },
            ].map((item) => (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                  location.pathname === item.path 
                  ? 'bg-white/10 text-white shadow-lg' 
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
                style={{ backgroundColor: location.pathname === item.path ? 'rgba(255,255,255,0.1)' : 'transparent' }}
              >
                <item.icon size={20} />
                <span className="font-medium">{item.label}</span>
              </button>
            ))}
          </nav>

          <button 
            onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-red-400 hover:bg-red-500/10 transition-colors mt-auto"
          >
            <LogOut size={20} />
            <span className="font-medium">Sign Out</span>
          </button>
        </aside>
      )}

      <main className={`flex-1 transition-all duration-300 ${token && location.pathname !== '/preview' ? 'md:ml-64' : ''}`}>
        <Routes>
          <Route path="/" element={<Home token={token} />} />
          <Route path="/setup" element={<Setup />} />
          <Route path="/generate" element={<Generator />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/preview/:id" element={<Preview />} />
        </Routes>
      </main>
    </div>
  )
}

function Home({ token }) {
  const navigate = useNavigate()

  if (token) {
    useEffect(() => navigate('/setup'), [navigate])
    return null
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="max-w-4xl w-full text-center space-y-12">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-sm font-medium animate-fade">
            <Sparkles size={14} />
            <span>AI Council Engine v2.0</span>
          </div>
          <h1 className="text-6xl md:text-8xl font-black tracking-tight text-white leading-tight">
            Design your brand <br/>
            <span className="premium-gradient text-transparent bg-clip-text">autonomously.</span>
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
            The first AI-agent council that deliberates on your career data to generate high-conversion portfolios automatically.
          </p>
        </div>

        <div className="flex flex-col md:flex-row items-center justify-center gap-4 relative z-10">
          <button 
            onClick={() => {
              console.log("Redirecting to GitHub login...");
              window.location.href = 'http://localhost:5001/api/auth/github/login';
            }}
            className="w-full md:w-auto px-8 py-4 bg-white text-black font-bold flex items-center justify-center gap-3 hover:scale-105 transition-transform"
          >
            <User size={20} />
            Get Started with GitHub
          </button>
        </div>

        <div className="pt-12 grid grid-cols-2 md:grid-cols-4 gap-8 opacity-50 border-t border-white/5">
          <div className="text-center font-bold">PDF Parsing</div>
          <div className="text-center font-bold">LinkedIn Scraping</div>
          <div className="text-center font-bold">Council Decisions</div>
          <div className="text-center font-bold">Auto-Deployment</div>
        </div>
      </div>
    </div>
  )
}

export default App
