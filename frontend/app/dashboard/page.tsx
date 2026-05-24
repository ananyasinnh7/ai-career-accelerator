'use client'

import { useEffect, useState } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { candidateApi, jobsApi, CandidateProfile, AnalysisSummary, Match } from '@/lib/api'
import { FileText, Briefcase, Star, TrendingUp, ArrowRight } from 'lucide-react'
import Link from 'next/link'

function ScoreBar({ score }: { score: number }) {
  const color = score >= 75 ? '#4ade80' : score >= 50 ? '#fbbf24' : '#f87171'
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-sm text-slate-400">Match Score</span>
        <span className="font-display font-bold text-lg" style={{ color }}>{score}</span>
      </div>
      <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: 100, height: 6 }}>
        <div style={{ width: `${score}%`, height: '100%', borderRadius: 100, background: `linear-gradient(90deg, ${color}, #38bdf8)`, transition: 'width 1s ease' }} />
      </div>
    </div>
  )
}

export default function CandidateDashboard() {
  const [profile, setProfile] = useState<CandidateProfile | null>(null)
  const [history, setHistory] = useState<AnalysisSummary[]>([])
  const [matches, setMatches] = useState<Match[]>([])
  const [jobCount, setJobCount] = useState(0)

  useEffect(() => {
    candidateApi.getProfile().then(r => setProfile(r.data)).catch(() => {})
    candidateApi.getHistory(1, 3).then(r => setHistory(r.data.results)).catch(() => {})
    jobsApi.myMatches(1, 3).then(r => setMatches(r.data.results)).catch(() => {})
    jobsApi.list(1, 1).then(r => setJobCount(r.data.total)).catch(() => {})
  }, [])

  const avgScore = history.length ? Math.round(history.reduce((a, h) => a + h.score, 0) / history.length) : 0

  return (
    <DashboardLayout requiredRole="candidate">
      
      <div className="mb-8">
        <h1 className="font-display font-bold text-3xl text-white mb-1">
          Welcome back, {profile?.full_name?.split(' ')[0] || 'there'} 👋
        </h1>
        <p className="text-slate-400">{profile?.headline || 'Complete your profile to get better matches'}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { label: 'Analyses Done', value: history.length, icon: FileText, color: '#a78bfa' },
          { label: 'Average Score', value: avgScore || '—', icon: TrendingUp, color: '#4ade80' },
          { label: 'Jobs Available', value: jobCount, icon: Briefcase, color: '#38bdf8' },
          { label: 'My Matches', value: matches.length, icon: Star, color: '#fbbf24' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${color}20` }}>
                <Icon size={16} color={color} />
              </div>
              <span className="text-xs text-slate-400 uppercase tracking-wider">{label}</span>
            </div>
            <div className="font-display font-bold text-2xl text-white">{value}</div>
          </div>
        ))}
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        
        {/* Recent analyses */}
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="font-display font-semibold text-white">Recent Scores</h2>
            <Link href="/score" className="text-purple-400 text-sm hover:text-purple-300 flex items-center gap-1">
              Score Resume <ArrowRight size={14} />
            </Link>
          </div>
          
          {history.length === 0 ? (
            <div className="text-center py-8">
              <FileText size={32} color="#334155" className="mx-auto mb-3" />
              <p className="text-slate-500 text-sm">No analyses yet</p>
              <Link href="/score" className="text-purple-400 text-sm hover:text-purple-300">Score your first resume →</Link>
            </div>
          ) : history.map(h => (
            <div key={h.id} className="mb-4 pb-4" style={{ borderBottom: '1px solid rgba(99,102,241,0.1)' }}>
              <div className="flex justify-between mb-2">
                <span className="text-sm text-slate-300 truncate">{h.original_filename || 'Resume'}</span>
                <span className="text-xs text-slate-500">{new Date(h.created_at).toLocaleDateString()}</span>
              </div>
              <ScoreBar score={h.score} />
            </div>
          ))}
          
          {history.length > 0 && (
            <Link href="/history" className="text-purple-400 text-sm hover:text-purple-300 flex items-center gap-1 mt-2">
              View all history <ArrowRight size={14} />
            </Link>
          )}
        </div>

        {/* Recent matches */}
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="font-display font-semibold text-white">My Matches</h2>
            <Link href="/jobs" className="text-purple-400 text-sm hover:text-purple-300 flex items-center gap-1">
              Browse Jobs <ArrowRight size={14} />
            </Link>
          </div>
          
          {matches.length === 0 ? (
            <div className="text-center py-8">
              <Briefcase size={32} color="#334155" className="mx-auto mb-3" />
              <p className="text-slate-500 text-sm">No matches yet</p>
              <Link href="/jobs" className="text-purple-400 text-sm hover:text-purple-300">Browse jobs and match →</Link>
            </div>
          ) : matches.map(m => (
            <div key={m.id} className="flex items-center justify-between mb-3 pb-3" style={{ borderBottom: '1px solid rgba(99,102,241,0.1)' }}>
              <div>
                <p className="text-sm text-white font-medium">{m.job_title || `Job #${m.job_id}`}</p>
                <p className="text-xs text-slate-400">{m.job_company || ''}</p>
              </div>
              <div className="text-right">
                <div className="font-display font-bold" style={{ color: m.score >= 75 ? '#4ade80' : m.score >= 50 ? '#fbbf24' : '#f87171' }}>
                  {m.score}
                </div>
                <span className={`status-badge status-${m.status}`}>{m.status}</span>
              </div>
            </div>
          ))}
          
          {matches.length > 0 && (
            <Link href="/matches" className="text-purple-400 text-sm hover:text-purple-300 flex items-center gap-1 mt-2">
              View all matches <ArrowRight size={14} />
            </Link>
          )}
        </div>

      </div>
    </DashboardLayout>
  )
}