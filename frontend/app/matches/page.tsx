'use client'

import { useEffect, useState } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { jobsApi, Match } from '@/lib/api'
import { Star, Briefcase, MapPin } from 'lucide-react'

export default function MatchesPage() {
  const [matches, setMatches] = useState<Match[]>([])
  const [total, setTotal] = useState(0)

  useEffect(() => { 
    jobsApi.myMatches(1, 50)
      .then(r => { 
        setMatches(r.data.results); 
        setTotal(r.data.total) 
      })
      .catch(() => {}) 
  }, [])

  return (
    <DashboardLayout requiredRole="candidate">
      
      <div className="mb-8">
        <h1 className="font-display font-bold text-3xl text-white mb-1">My Matches</h1>
        <p className="text-slate-400">{total} jobs matched</p>
      </div>

      {matches.length === 0 ? (
        <div className="card text-center py-16">
          <Star size={48} color="#1e293b" className="mx-auto mb-4" />
          <p className="text-slate-500 font-display font-semibold text-lg">No matches yet</p>
          <p className="text-slate-600 text-sm mt-1">Score your resume first, then browse jobs and click Match Me</p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {matches.map(m => {
            const color = m.score >= 75 ? '#4ade80' : m.score >= 50 ? '#fbbf24' : '#f87171'
            return (
              <div key={m.id} className="card">
                
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="font-display font-semibold text-white text-lg">{m.job_title || `Job #${m.job_id}`}</h3>
                    <div className="flex items-center gap-3 mt-1 text-sm text-slate-400">
                      {m.job_company && <span className="text-purple-400 font-medium">{m.job_company}</span>}
                      {m.job_location && <span className="flex items-center gap-1"><MapPin size={12} />{m.job_location}</span>}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-display font-extrabold text-4xl" style={{ color }}>{m.score}</div>
                    <p className="text-xs text-slate-500">/ 100</p>
                  </div>
                </div>

                <div style={{ background: 'rgba(255,255,255,0.04)', borderRadius: 100, height: 6, marginBottom: 16 }}>
                  <div style={{ width: `${m.score}%`, height: '100%', borderRadius: 100, background: `linear-gradient(90deg, ${color}, #38bdf8)` }} />
                </div>

                <p className="text-slate-400 text-sm leading-relaxed mb-3">{m.summary}</p>
                
                <div className="flex flex-wrap gap-1 mb-3">
                  {m.missing_skills.map(s => <span key={s} className="skill-chip">⚡ {s}</span>)}
                </div>

                <div style={{ background: 'rgba(56,189,248,0.07)', borderLeft: '3px solid #38bdf8', borderRadius: '0 8px 8px 0', padding: '0.75rem 1rem', marginBottom: 12 }}>
                  <p className="text-xs text-blue-400 mb-1 uppercase tracking-wider">Recommended Project</p>
                  <p className="text-slate-300 text-sm">{m.recommended_project}</p>
                </div>

                <div className="flex items-center justify-between">
                  <span className={`status-badge status-${m.status}`}>{m.status}</span>
                  <span className="text-xs text-slate-500">{new Date(m.created_at).toLocaleDateString()}</span>
                </div>

                {m.recruiter_notes && (
                  <div className="mt-3 p-3 rounded-lg" style={{ background: 'rgba(167,139,250,0.05)', border: '1px solid rgba(167,139,250,0.2)' }}>
                    <p className="text-xs text-purple-400 mb-1">Recruiter Note</p>
                    <p className="text-slate-300 text-sm">{m.recruiter_notes}</p>
                  </div>
                )}
                
              </div>
            )
          })}
        </div>
      )}
      
    </DashboardLayout>
  )
}