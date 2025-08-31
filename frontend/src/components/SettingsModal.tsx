import React, { useEffect, useState } from 'react'

type Props = {
  open: boolean
  onClose: () => void
  openaiKey: string
  setOpenaiKey: (v: string) => void
  brightKey: string
  setBrightKey: (v: string) => void
  redditDataset: string
  setRedditDataset: (v: string) => void
  commentsDataset: string
  setCommentsDataset: (v: string) => void
  onSaveServer: () => Promise<void>
  onTest: () => Promise<void>
  serverMeta?: { has_openai_api_key: boolean; has_brightdata_api_key: boolean; reddit_dataset_id?: string | null; reddit_comments_dataset_id?: string | null } | null
}

export default function SettingsModal(props: Props) {
  const { open, onClose, openaiKey, setOpenaiKey, brightKey, setBrightKey, redditDataset, setRedditDataset, commentsDataset, setCommentsDataset, onSaveServer, onTest, serverMeta } = props
  const [showOpenAI, setShowOpenAI] = useState(false)
  const [showBright, setShowBright] = useState(false)

  useEffect(() => {
    function onEsc(e: KeyboardEvent) { if (e.key === 'Escape') onClose() }
    if (open) window.addEventListener('keydown', onEsc)
    return () => window.removeEventListener('keydown', onEsc)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="absolute inset-0 flex items-center justify-center p-4">
        <div className="card w-full max-w-2xl">
          <div className="p-6 border-b border-slate-200/60 dark:border-slate-700 flex items-center justify-between">
            <h3 className="text-lg font-semibold">API Settings</h3>
            <button className="btn-ghost" onClick={onClose}>Close</button>
          </div>
          <div className="p-6 space-y-4">
            <div>
              <div className="flex items-center justify-between text-sm mb-1">
                <span>OpenAI API Key {serverMeta?.has_openai_api_key ? <em className="text-emerald-600 ml-1">• on server</em> : null}</span>
                <a className="text-brand-600 hover:underline" href="https://platform.openai.com/api-keys" target="_blank" rel="noreferrer">Get key</a>
              </div>
              <div className="flex gap-2">
                <input className="input" type={showOpenAI ? 'text' : 'password'} placeholder="sk-..." value={openaiKey} onChange={(e) => setOpenaiKey(e.target.value)} />
                <button className="btn-outline" onClick={() => setShowOpenAI(s => !s)}>{showOpenAI ? 'Hide' : 'Show'}</button>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between text-sm mb-1">
                <span>Bright Data API Token {serverMeta?.has_brightdata_api_key ? <em className="text-emerald-600 ml-1">• on server</em> : null}</span>
                <span className="text-xs flex gap-3">
                  <a className="text-brand-600 hover:underline" href="https://brightdata.com/cp" target="_blank" rel="noreferrer">Dashboard</a>
                  <a className="text-brand-600 hover:underline" href="https://brightdata.com/docs/api/authentication" target="_blank" rel="noreferrer">Docs</a>
                </span>
              </div>
              <div className="flex gap-2">
                <input className="input" type={showBright ? 'text' : 'password'} placeholder="brd_xxx..." value={brightKey} onChange={(e) => setBrightKey(e.target.value)} />
                <button className="btn-outline" onClick={() => setShowBright(s => !s)}>{showBright ? 'Hide' : 'Show'}</button>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between text-sm mb-1">
                <span>Reddit Dataset ID</span>
                <a className="text-brand-600 hover:underline" href="https://brightdata.com/datasets" target="_blank" rel="noreferrer">Datasets</a>
              </div>
              <input className="input" placeholder="gd_..." value={redditDataset} onChange={(e) => setRedditDataset(e.target.value)} />
            </div>
            <div>
              <div className="flex items-center justify-between text-sm mb-1">
                <span>Reddit Comments Dataset ID</span>
                <a className="text-brand-600 hover:underline" href="https://brightdata.com/datasets" target="_blank" rel="noreferrer">Datasets</a>
              </div>
              <input className="input" placeholder="gd_..." value={commentsDataset} onChange={(e) => setCommentsDataset(e.target.value)} />
            </div>

            <div className="flex gap-3 pt-2">
              <button className="btn-outline" onClick={onSaveServer}>Save to server</button>
              <button className="btn-primary" onClick={onTest}>Test Settings</button>
            </div>
            <p className="text-xs text-slate-500">Settings save to your browser (localStorage) and can be saved to the server for this session. They are sent with your request to the local API.</p>
          </div>
        </div>
      </div>
    </div>
  )
}

