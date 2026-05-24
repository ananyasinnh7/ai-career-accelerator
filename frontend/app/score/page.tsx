'use client'

import { useState, useRef } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { resumeApi, ResumeScoreResponse } from '@/lib/api'
import toast from 'react-hot-toast'
import { Upload, Zap, CheckCircle } from 'lucide-react'

export default function ScorePage() {
  const [file, setFile] = useState<File | null>(null)
  const [jd, setJd] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ResumeScoreResponse | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) { 
      toast.error('Please upload a PDF'); 
      return 
    }
    if (jd.trim().length < 50) { 
      toast.error('Job description must be at least 50 characters'); 
      return 
    }
    
    setLoading(true)
    try {
      const { data } = await resumeApi.score(file, jd)
      setResult(data)
      toast.success('Resume scored successfully!')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Scoring failed')
    } finally { 
      setLoading(false) 
    }
  }

  const scoreColor = result 
    ? (result.score >= 75 ? '#4ade80' : result.score >= 50 ? '#fbbf24' : '#f87171') 
    : '#a78bfa'

  return (
    <DashboardLayout requiredRole="candidate">
      
      <div className="mb-8">
        <h1 className="font-display font-bold text-3xl text-white mb-1">Score Your Resume</h1>
        <p className="text-slate-400">Upload your PDF and paste a job description to get your AI match score</p>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        
        {/* Form */}
        <div className="card">
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            
            {/* File upload */}
            <div>
              <label className="text-xs text-slate-400 mb-2 block uppercase tracking-wider">Resume PDF</label>
              <div 
                onClick={() => fileRef.current?.click()} 
                className="flex flex-col items-center justify-center p-8 rounded-xl cursor-pointer transition-all"
                style={{ 
                  border: `2px dashed ${file ? '#a78bfa' : 'rgba(99,102,241,0.3)'}`, 
                  background: file ? 'rgba(167,139,250,0.05)' : 'transparent' 
                }}
              >
                <input 
                  ref={fileRef} 
                  type="file" 
                  accept=".pdf" 
                  className="hidden" 
                  onChange={e => e.target.files?.[0] && setFile(e.target.files[0])} 
                />
                
                {file ? (
                  <>
                    <CheckCircle size={28} color="#a78bfa" className="mb-2" />
                    <p className="text-purple-300 font-medium text-sm">{file.name}</p>
                    <p className="text-slate-500 text-xs mt-1">{(file.size / 1024).toFixed(1)} KB</p>
                  </>
                ) : (
                  <>
                    <Upload size={28} color="#475569" className="mb-2" />
                    <p className="text-slate-400 text-sm">Click to upload PDF</p>
                    <p className="text-slate-600 text-xs mt-1">Max 10 MB</p>
                  </>
                )}
              </div>
            </div>

            {/* Job description */}
            <div>
              <label className="text-xs text-slate-400 mb-2 block uppercase tracking-wider">Job Description</label>
              <textarea 
                className="input-field" 
                rows={10} 
                placeholder="Paste the full job description here..." 
                value={jd} 
                onChange={e => setJd(e.target.value)} 
              />
              <p className="text-xs text-slate-500 mt-1">{jd.length} chars (min 50)</p>
            </div>

            <button type="submit" disabled={loading} className="btn-primary flex items-center justify-center gap-2">
              <Zap size={16} />
              {loading ? 'Analysing with AI...' : 'Analyse Match'}
            </button>
            
          </form>
        </div>

        {/* Result */}
        <div>
          {!result ? (
            <div className="card flex flex-col items-center justify-center h-full min-h-64 text-center">
              <Zap size={40} color="#1e293b" className="mb-4" />
              <p className="text-slate-600 font-display font-semibold">Your results will appear here</p>
              <p className="text-slate-700 text-sm mt-1">Fill the form and click Analyse</p>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              
              {/* Score */}
              <div className="card text-center">
                <div 
                  className="font-display font-extrabold mb-1" 
                  style={{ 
                    fontSize: '5rem', 
                    lineHeight: 1, 
                    background: `linear-gradient(135deg, ${scoreColor}, #38bdf8)`, 
                    WebkitBackgroundClip: 'text', 
                    WebkitTextFillColor: 'transparent' 
                  }}
                >
                  {result.score}
                </div>
                <p className="text-slate-400 text-xs uppercase tracking-widest">Match Score out of 100</p>
                
                <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: 100, height: 8, marginTop: 12 }}>
                  <div style={{ width: `${result.score}%`, height: '100%', borderRadius: 100, background: `linear-gradient(90deg, ${scoreColor}, #38bdf8)` }} />
                </div>
              </div>

              {/* Summary */}
              <div className="card">
                <p className="text-xs text-purple-400 uppercase tracking-wider mb-2">AI Summary</p>
                <p className="text-slate-300 text-sm leading-relaxed">{result.summary}</p>
              </div>

              {/* Missing skills */}
              <div className="card">
                <p className="text-xs text-red-400 uppercase tracking-wider mb-3">Missing Skills</p>
                <div>
                  {result.missing_skills.map(s => (
                    <span key={s} className="skill-chip">⚡ {s}</span>
                  ))}
                </div>
              </div>

              {/* Project */}
              <div className="card">
                <p className="text-xs text-blue-400 uppercase tracking-wider mb-2">Recommended Project</p>
                <div style={{ background: 'rgba(56,189,248,0.07)', borderLeft: '3px solid #38bdf8', borderRadius: '0 12px 12px 0', padding: '1rem' }}>
                  <p className="text-slate-300 text-sm leading-relaxed">{result.recommended_project}</p>
                </div>
              </div>

              <button 
                onClick={() => { setResult(null); setFile(null); setJd('') }} 
                className="btn-primary" 
                style={{ background: 'rgba(15,15,30,0.8)', border: '1px solid rgba(99,102,241,0.3)' }}
              >
                Score Another Resume
              </button>
              
            </div>
          )}
        </div>

      </div>
    </DashboardLayout>
  )
}