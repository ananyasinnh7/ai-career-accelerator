'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { jobsApi, Match, JobPosting } from '@/lib/api'
import toast from 'react-hot-toast'
import { Users, User, Briefcase, MapPin, ChevronDown } from 'lucide-react'

export default function JobCandidatesPage() {
  const { id } = useParams()
  const jobId = Number(id)
  
  const [job, setJob] = useState<JobPosting | null>(null)
  const [matches, setMatches] = useState<Match[]>([])
  const [total, setTotal] = useState(0)
  const [updating, setUpdating] = useState<number | null>(null)

  useEffect(() => {
    jobsApi.get(jobId)
      .then(r => setJob(r.data))
      .catch(() => {})
      
    jobsApi.getCandidates(jobId, 1, 50)
      .then(r => { 
        setMatches(r.data.results); 
        setTotal(r.data.total) 
      })
      .catch(() => {})
  }, [jobId])

  const handleStatusUpdate = async (matchId: number, status: string, notes?: string) => {
    setUpdating(matchId)
    try {
      const updated = await jobsApi.updateMatch(jobId, matchId, { status, recruiter_notes: notes })
      setMatches(ms => ms.map(m => m.id === matchId ? updated.data : m))
      toast.success(`Candidate ${status}`)
    } catch { 
      toast.error('Update failed') 
    } finally { 
      setUpdating(null) 
    }
  }

  return (
    <DashboardLayout requiredRole="recruiter">
      
      <div className="mb-8">
        {job && (
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className={`status-badge status-${job.status}`}>{job.status}</span>
            </div>
            <h1 className="font-display font-bold text-3xl text-white">{job.title}</h1>
            <div className="flex items-center gap-3 mt-1 text-slate-400 text-sm">
              <span className="text-purple-400 font-medium">{job.company}</span>
              {job.location && <span className="flex items-center gap-1"><MapPin size={12} />{job.location}</span>}
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 mb-6">
        <Users size={18} color="#a78bfa" />
        <h2 className="font-display font-semibold text-white text-xl">{total} Candidates Applied</h2>
        <span className="text-slate-400 text-sm">(ranked by AI match score)</span>
      </div>

      {matches.length === 0 ? (
        <div className="card text-center py-16">
          <Users size={48} color="#1e293b" className="mx-auto mb-4" />
          <p className="text-slate-500 font-display font-semibold text-lg">No candidates yet</p>
          <p className="text-slate-600 text-sm mt-1">Candidates appear here when they match themselves to this job</p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {matches.map((m, i) => {
            const color = m.score >= 75 ? '#4ade80' : m.score >= 50 ? '#fbbf24' : '#f87171'
            return (
              <div key={m.id} className="card">
                
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full flex items-center justify-center font-display font-bold text-sm" style={{ background: 'linear-gradient(135deg, rgba(124,58,237,0.3), rgba(37,99,235,0.3))', border: '1px solid rgba(167,139,250,0.3)', color: '#a78bfa' }}>
                      #{i + 1}
                    </div>
                    <div>
                      <p className="text-white font-medium">{m.candidate_name || `Candidate #${m.candidate_id}`}</p>
                      {m.candidate_email && <p className="text-slate-400 text-sm">{m.candidate_email}</p>}
                      {m.candidate_headline && <p className="text-purple-400 text-xs">{m.candidate_headline}</p>}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-display font-extrabold text-3xl" style={{ color }}>{m.score}</div>
                    <p className="text-xs text-slate-500">/ 100</p>
                  </div>
                </div>

                <div style={{ background: 'rgba(255,255,255,0.04)', borderRadius: 100, height: 6, marginBottom: 12 }}>
                  <div style={{ width: `${m.score}%`, height: '100%', borderRadius: 100, background: `linear-gradient(90deg, ${color}, #38bdf8)` }} />
                </div>

                <p className="text-slate-400 text-sm leading-relaxed mb-3">{m.summary}</p>
                <div className="flex flex-wrap gap-1 mb-4">
                  {m.missing_skills.map(s => <span key={s} className="skill-chip">⚡ {s}</span>)}
                </div>

                <div className="flex items-center justify-between">
                  <span className={`status-badge status-${m.status}`}>{m.status}</span>
                  <div className="flex gap-2">
                    {m.status !== 'shortlisted' && (
                      <button 
                        disabled={updating === m.id} 
                        onClick={() => handleStatusUpdate(m.id, 'shortlisted', 'Strong candidate — invited to interview.')}
                        className="px-3 py-1.5 rounded-lg text-sm font-medium transition-all" 
                        style={{ background: 'rgba(74,222,128,0.15)', border: '1px solid rgba(74,222,128,0.3)', color: '#4ade80' }}
                      >
                        ✓ Shortlist
                      </button>
                    )}
                    {m.status !== 'rejected' && (
                      <button 
                        disabled={updating === m.id} 
                        onClick={() => handleStatusUpdate(m.id, 'rejected')}
                        className="px-3 py-1.5 rounded-lg text-sm font-medium transition-all" 
                        style={{ background: 'rgba(248,113,113,0.15)', border: '1px solid rgba(248,113,113,0.3)', color: '#f87171' }}
                      >
                        ✕ Reject
                      </button>
                    )}
                  </div>
                </div>

              </div>
            )
          })}
        </div>
      )}
      
    </DashboardLayout>
  )
}