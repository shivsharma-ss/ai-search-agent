import { AnimatePresence, motion } from 'framer-motion'
import { ClipboardCopy, Home, Library, Moon, RefreshCw, Settings2, Sun, Wand2 } from 'lucide-react'
import React, { useEffect, useState } from 'react'
import { Toaster, toast } from 'sonner'
import SettingsModal from './components/SettingsModal'
import Starfield from './components/Starfield'
import './index.css'

type ResearchResponse = {
  final_answer?: string
  google_results?: unknown
  bing_results?: unknown
  reddit_results?: unknown
  reddit_post_data?: unknown
  google_analysis?: string
  bing_analysis?: string
  reddit_analysis?: string
}

function LoadingPanel() {
  const messages = [
    'Greasing the internet tubes…',
    'Convincing APIs with cookies…',
    'Politely asking Bing for gossip…',
    'Googling how to Google Google…',
    'Summoning wise owls from Reddit…',
    'Untangling JSON spaghetti… careful, it’s al dente…',
    'Polishing neurons for extra sparkle…',
    'Bribing the rate limits with compliments…',
    'Finding the answer behind the couch…',
    'Teaching vectors to line dance…',
  ]
  const [i, setI] = useState(0)
  useEffect(() => {
    const id = setInterval(() => setI(v => (v + 1) % messages.length), 3000)
    return () => clearInterval(id)
  }, [])
  return (
    <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }} className="relative overflow-hidden rounded-lg border border-slate-200/60 dark:border-slate-700 bg-white/70 dark:bg-slate-900/70 p-4">
      <div className="absolute inset-0 tron-grid opacity-10 pointer-events-none"></div>
      <div className="flex items-center gap-4 relative">
        <motion.div
          className="w-11 h-11 rounded-full bg-brand-600/90 text-white flex items-center justify-center shadow"
          animate={{ rotate: [0, 10, -10, 0] }}
          transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut' }}
        >
          <Wand2 className="w-5 h-5" />
        </motion.div>
        <div className="flex-1">
          <AnimatePresence mode="wait">
            <motion.div key={i} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.22 }} className="font-medium">
              {messages[i]}
            </motion.div>
          </AnimatePresence>
          <div className="mt-3 h-2 rounded-full bg-slate-300/60 dark:bg-slate-700/60 indeterminate-bar"></div>
          <div className="mt-3 loading-dots">
            <span className="dot"></span>
            <span className="dot"></span>
            <span className="dot"></span>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

function useLocalStorage(key: string, initial: string = '') {
  const [val, setVal] = useState<string>(() => localStorage.getItem(key) ?? initial)
  const setter = (v: string) => {
    setVal(v)
    localStorage.setItem(key, v)
  }
  return [val, setter] as const
}

export default function App() {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<ResearchResponse | null>(null)
  const [showDetails, setShowDetails] = useState(false)
  const [openaiKey, setOpenaiKey] = useLocalStorage('asa_openai_key')
  const [brightKey, setBrightKey] = useLocalStorage('asa_bright_key')
  const [redditDataset, setRedditDataset] = useLocalStorage('asa_reddit_dataset', 'gd_lvz8ah06191smkebj4')
  const [commentsDataset, setCommentsDataset] = useLocalStorage('asa_comments_dataset', 'gd_lvzdpsdlw09j6t702')
  const [serverMeta, setServerMeta] = useState<{ has_openai_api_key: boolean; has_brightdata_api_key: boolean; reddit_dataset_id?: string | null; reddit_comments_dataset_id?: string | null } | null>(null)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<'ask' | 'library'>('ask')
  const [theme, setTheme] = useState<string>(() => localStorage.getItem('asa_theme') || 'system')
  const [isDark, setIsDark] = useState<boolean>(() => document.documentElement.classList.contains('dark'))
  const [runs, setRuns] = useState<Array<{ id: string; ts: number; question: string; has_answer: boolean }>>([])
  const [srcTab, setSrcTab] = useState<'google' | 'bing' | 'reddit'>('google')

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setData(null)
    try {
      const res = await fetch('/api/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          openai_api_key: openaiKey || undefined,
          brightdata_api_key: brightKey || undefined,
          reddit_dataset_id: redditDataset || undefined,
          reddit_comments_dataset_id: commentsDataset || undefined,
        }),
      })
      if (!res.ok) throw new Error(await res.text())
      const json = (await res.json()) as ResearchResponse
      setData(json)
      toast.success('Research complete')
    } catch (err: any) {
      setError(err?.message ?? 'Request failed')
      toast.error(err?.message ?? 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Load server-side settings meta
    fetch('/api/settings')
      .then(r => r.ok ? r.json() : null)
      .then(meta => meta && setServerMeta(meta))
      .catch(() => {})
  }, [])

  useEffect(() => {
    // Apply theme on first render and when theme changes
    function doApply(t: string) {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      const dark = t === 'dark' || (t === 'system' && prefersDark)
      document.documentElement.classList.toggle('dark', dark)
      setIsDark(dark)
      localStorage.setItem('asa_theme', t)
    }
    doApply(theme)
    // React to OS preference changes when on system
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = (e: MediaQueryListEvent) => { if (theme === 'system') doApply('system') }
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [theme])

  useEffect(() => {
    if (serverMeta) {
      if (!redditDataset && serverMeta.reddit_dataset_id) setRedditDataset(serverMeta.reddit_dataset_id)
      if (!commentsDataset && serverMeta.reddit_comments_dataset_id) setCommentsDataset(serverMeta.reddit_comments_dataset_id)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [serverMeta])

  async function saveToServer() {
    setError(null)
    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          openai_api_key: openaiKey || undefined,
          brightdata_api_key: brightKey || undefined,
          reddit_dataset_id: redditDataset || undefined,
          reddit_comments_dataset_id: commentsDataset || undefined,
        })
      })
      if (!res.ok) throw new Error(await res.text())
      const meta = await res.json()
      setServerMeta(meta)
      toast.success('Settings saved to server')
    } catch (e: any) {
      setError(e?.message ?? 'Failed to save settings')
      toast.error(e?.message ?? 'Failed to save settings')
    }
  }

  async function testSettings() {
    setError(null)
    try {
      // Quick health ping
      const h = await fetch('/health')
      if (!h.ok) throw new Error('Backend health check failed')
      // Validate Bright Data token (payload optional; server uses session if empty)
      const res = await fetch('/api/test-settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          openai_api_key: openaiKey || undefined,
          brightdata_api_key: brightKey || undefined,
          reddit_dataset_id: redditDataset || undefined,
          reddit_comments_dataset_id: commentsDataset || undefined,
        })
      })
      const json = await res.json()
      if (!res.ok || !json.ok) {
        throw new Error(json?.message || 'Settings check failed')
      }
      toast.success('Settings OK: Bright Data token valid')
    } catch (e: any) {
      setError(e?.message ?? 'Test failed')
      toast.error(e?.message ?? 'Test failed')
    }
  }

  async function refreshRuns() {
    try {
      const r = await fetch('/api/runs')
      if (!r.ok) throw new Error(await r.text())
      const list = await r.json()
      setRuns(list)
    } catch (e: any) {
      toast.error(e?.message ?? 'Failed to load library')
    }
  }

  async function loadRun(id: string) {
    try {
      const r = await fetch(`/api/runs/${id}`)
      if (!r.ok) throw new Error(await r.text())
      const run = await r.json()
      const result = run?.result as ResearchResponse
      setData(result)
      setActiveTab('ask')
      toast.success('Loaded from library')
    } catch (e: any) {
      toast.error(e?.message ?? 'Failed to load run')
    }
  }

  function cycleTheme() {
    setTheme(prev => prev === 'dark' ? 'light' : prev === 'light' ? 'system' : 'dark')
  }

  return (
    <div className="min-h-screen gradient-bg text-slate-900 dark:text-slate-100">
      <Toaster richColors position="top-right" />
      <header className="border-b border-slate-200 dark:border-white/10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-brand-600 text-white flex items-center justify-center shadow"><Wand2 className="w-4 h-4" /></div>
            <h1 className="text-xl font-semibold">AI Search Agent</h1>
          </div>
          <nav className="flex items-center gap-2">
            <div className="hidden sm:flex gap-2 mr-2 rounded-lg bg-slate-100 dark:bg-white/5 p-1">
              <button className={`btn-ghost ${activeTab==='ask'?'!bg-slate-200 dark:!bg-white/10':''}`} onClick={() => setActiveTab('ask')}><Home className="w-4 h-4 mr-1"/> Ask</button>
              <button className={`btn-ghost ${activeTab==='library'?'!bg-slate-200 dark:!bg-white/10':''}`} onClick={() => { setActiveTab('library'); refreshRuns(); }}><Library className="w-4 h-4 mr-1"/> Library</button>
            </div>
            <button title="Settings" className="btn-ghost" onClick={() => setSettingsOpen(true)}><Settings2 className="w-4 h-4 mr-1"/>Settings</button>
            <button title="Test" className="btn-outline" onClick={() => testSettings()}><RefreshCw className="w-4 h-4 mr-1"/>Test</button>
            <button className="btn-ghost" onClick={cycleTheme}>
              {isDark ? <Moon className="w-4 h-4"/> : <Sun className="w-4 h-4"/>}
            </button>
          </nav>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-10">
        {/* Hero ask area */}
        <div className="flex items-center justify-center min-h-[50vh]">
        <motion.section initial={{opacity:0, y:12}} animate={{opacity:1, y:0}} transition={{duration:0.35, ease:'easeOut'}} className="relative neon-card overflow-hidden w-full float-slow" onMouseMove={(e) => {
          const el = e.currentTarget as HTMLElement
          const rect = el.getBoundingClientRect()
          const mx = ((e.clientX - rect.left) / rect.width) * 100
          const my = ((e.clientY - rect.top) / rect.height) * 100
          el.style.setProperty('--mx', mx + '%')
          el.style.setProperty('--my', my + '%')
        }}>
          <Starfield />
          <div className="absolute inset-0 tron-grid opacity-30"></div>
          <div className="scanline"></div>
          <div className="glow-sweep"></div>
          <div className="p-8 text-slate-900 dark:text-slate-100">
            <h2 className="text-2xl font-semibold mb-2 drop-shadow">Ask a question</h2>
            <p className="text-sm text-slate-600 dark:text-slate-300/90 mb-4">Synthesizes answers from Google, Bing, and Reddit.</p>
            <div className="mb-4 grid md:grid-cols-3 gap-2">
              {['Best laptop for ML under $1500','How to learn Rust efficiently','Is TypeScript worth it in 2025?'].map((ex) => (
                <button key={ex} className="btn-ghost bg-white/70 text-slate-900 hover:bg-white dark:bg-white/5 dark:text-white dark:hover:bg-white/10" onClick={() => setQuestion(ex)}>{ex}</button>
              ))}
            </div>
            <form onSubmit={submit} className="flex gap-3">
              <input className="input bg-white/95 dark:bg-slate-900/80 text-slate-800 dark:text-slate-100" placeholder="What do you want to know?" value={question} onChange={(e) => setQuestion(e.target.value)} required />
              <button type="submit" className="btn-neon ripple-container" disabled={loading} onMouseDown={(e) => {
                const target = e.currentTarget
                const span = document.createElement('span')
                const rect = target.getBoundingClientRect()
                span.className = 'ripple'
                span.style.left = `${e.clientX - rect.left}px`
                span.style.top = `${e.clientY - rect.top}px`
                target.appendChild(span)
                setTimeout(() => span.remove(), 700)
              }}>{loading ? 'Thinking…' : 'Research'}</button>
            </form>
            {error && <div className="mt-3 text-rose-400 text-sm drop-shadow">{error}</div>}
            <div className="mt-6 text-xs text-slate-300/90">Tip: Save your API keys in the settings for best experience.</div>
          </div>
        </motion.section>
        </div>

        {/* Library below hero when active */}
        <AnimatePresence>
          {activeTab === 'library' && (
            <motion.section initial={{opacity:0, y:8}} animate={{opacity:1, y:0}} exit={{opacity:0, y:8}} transition={{duration:0.2}} className="card p-6 mt-6 text-slate-900 dark:text-slate-100">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold">Library</h3>
                <button className="btn-outline" onClick={refreshRuns}><RefreshCw className="w-4 h-4 mr-1"/>Refresh</button>
              </div>
              <div className="max-h-80 overflow-auto divide-y divide-slate-200 dark:divide-slate-700">
                {runs.length === 0 && <div className="text-sm text-slate-500 py-6">No saved runs yet. Run a query to populate.</div>}
                {runs.map(r => (
                  <div key={r.id} className="py-3 flex items-center justify-between">
                    <div>
                      <div className="font-medium text-sm">{r.question}</div>
                      <div className="text-xs text-slate-500">{new Date(r.ts * 1000).toLocaleString()}</div>
                    </div>
                    <div className="flex gap-2">
                      <button className="btn-outline" onClick={() => loadRun(r.id)}>Open</button>
                      <button className="btn-ghost" onClick={async () => {
                        try {
                          const res = await fetch(`/api/runs/${r.id}/share`, { method: 'POST' })
                          if (!res.ok) throw new Error(await res.text())
                          const j = await res.json()
                          await navigator.clipboard.writeText(j.url)
                          toast.success('Share link copied')
                        } catch (e: any) {
                          toast.error(e?.message ?? 'Failed to share')
                        }
                      }}>Share</button>
                    </div>
                  </div>
                ))}
              </div>
            </motion.section>
          )}
        </AnimatePresence>

        {/* Answer area */}
        <section className="card p-6 mt-6 text-slate-900 dark:text-slate-100">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold">Answer</h2>
            <div className="flex gap-2">
              <button className="btn-outline" onClick={() => { if (data?.final_answer) { navigator.clipboard.writeText(String(data.final_answer)); toast.success('Copied answer'); } }}><ClipboardCopy className="w-4 h-4 mr-1"/>Copy</button>
              <button className="btn-ghost" onClick={() => setShowDetails(s => !s)}>{showDetails ? 'Hide details' : 'Show details'}</button>
            </div>
          </div>
          {loading && <LoadingPanel />}
          {!loading && !data && (
            <div className="space-y-2">
              <div className="h-4 w-3/5 skeleton"></div>
              <div className="h-4 w-4/5 skeleton"></div>
              <div className="h-4 w-2/5 skeleton"></div>
            </div>
          )}
          {data && (
            <>
              <motion.div initial={{opacity:0}} animate={{opacity:1}} transition={{duration:0.2}} className="whitespace-pre-wrap leading-relaxed">{data.final_answer || 'No answer produced.'}</motion.div>
              <div className="mt-6">
                {/* Source tabs */}
                <div className="flex gap-2 mb-3">
                  {(['google','bing','reddit'] as const).map(s => (
                    <button key={s} onClick={() => setSrcTab(s)} className={`btn-ghost ${srcTab===s?'!bg-white/10':''}`}>{s[0].toUpperCase()+s.slice(1)}</button>
                  ))}
                </div>
                <AnimatePresence mode="wait">
                  {srcTab==='google' && (
                    <motion.div key="google" initial={{opacity:0, y:6}} animate={{opacity:1, y:0}} exit={{opacity:0, y:6}} transition={{duration:0.2}}>
                      <h3 className="font-medium mb-1">Google Summary</h3>
                      <div className="text-sm mb-2 whitespace-pre-wrap">{(data as any).google_analysis || '—'}</div>
                      <details className="text-sm"><summary className="cursor-pointer">Raw results</summary><pre className="mt-2 text-xs bg-slate-900/70 border border-slate-700 rounded p-3 overflow-auto text-slate-100">{JSON.stringify((data as any).google_results, null, 2)}</pre></details>
                    </motion.div>
                  )}
                  {srcTab==='bing' && (
                    <motion.div key="bing" initial={{opacity:0, y:6}} animate={{opacity:1, y:0}} exit={{opacity:0, y:6}} transition={{duration:0.2}}>
                      <h3 className="font-medium mb-1">Bing Summary</h3>
                      <div className="text-sm mb-2 whitespace-pre-wrap">{(data as any).bing_analysis || '—'}</div>
                      <details className="text-sm"><summary className="cursor-pointer">Raw results</summary><pre className="mt-2 text-xs bg-slate-900/70 border border-slate-700 rounded p-3 overflow-auto text-slate-100">{JSON.stringify((data as any).bing_results, null, 2)}</pre></details>
                    </motion.div>
                  )}
                  {srcTab==='reddit' && (
                    <motion.div key="reddit" initial={{opacity:0, y:6}} animate={{opacity:1, y:0}} exit={{opacity:0, y:6}} transition={{duration:0.2}}>
                      <h3 className="font-medium mb-1">Reddit Summary</h3>
                      <div className="text-sm mb-2 whitespace-pre-wrap">{(data as any).reddit_analysis || '—'}</div>
                      <details className="text-sm"><summary className="cursor-pointer">Raw results</summary><pre className="mt-2 text-xs bg-slate-900/70 border border-slate-700 rounded p-3 overflow-auto text-slate-100">{JSON.stringify({ results: (data as any).reddit_results, comments: (data as any).reddit_post_data }, null, 2)}</pre></details>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
              {showDetails && (
                <div className="mt-4">
                  <h3 className="font-medium mb-2">Debug details</h3>
                  <pre className="text-xs bg-slate-900/70 border border-slate-700 rounded p-3 overflow-auto text-slate-100">{JSON.stringify(data, null, 2)}</pre>
                </div>
              )}
            </>
          )}
        </section>
      </main>

      <footer className="border-t border-white/10">
        <div className="max-w-7xl mx-auto px-4 py-6 text-sm text-slate-400">© {new Date().getFullYear()} AI Search Agent</div>
      </footer>

      <SettingsModal
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        openaiKey={openaiKey} setOpenaiKey={setOpenaiKey}
        brightKey={brightKey} setBrightKey={setBrightKey}
        redditDataset={redditDataset} setRedditDataset={setRedditDataset}
        commentsDataset={commentsDataset} setCommentsDataset={setCommentsDataset}
        onSaveServer={saveToServer}
        onTest={testSettings}
        serverMeta={serverMeta}
      />
    </div>
  )
}
