'use client'

import { useEffect, useState } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { candidateApi, AnalysisSummary } from '@/lib/api'
import { FileText, ChevronLeft, ChevronRight } from 'lucide-react'

export default function HistoryPage() {
  const [data, setData] = useState<{ total: number; results: AnalysisSummary[] }>({ total: 0, results: [] })
  const [page, setPage] = useState(1)
  const size = 10

  useEffect(() => {
    candidateApi.getHistory(page, size)
      .then(r => setData(r.data))
      .catch(() => {})
  }, [page])

  const totalPages = Math.ceil(data.total / size)

  return (
    <DashboardLayout requiredRole="candidate">
      
      <div className="mb-8">
        <h1 className="font-display font-bold text-3xl text-white mb-1">Analysis History</h1>
        <p className="text-slate-400">{data.total} total analyses</p>
      </div>

      {data.results.length === 0 ? (
        <div className="card text-center py-16">
          <FileText size={48} color="#1e293b" className="mx-auto mb-4" />
          <p className="text-slate-500 font-display font-semibold text-lg">No analyses yet</p>
          <p className="text-slate-600 text-sm mt-1">Score your resume to see results here</p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {data.results.map(h => {
            const color = h.score >= 75 ? '#4ade80' : h.score >= 50 ? '#fbbf24' : '#f87171'
            return (
              <div key={h.id} className="card flex flex-col md:flex-row md:items-center gap-4">
                
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <FileText size={16} color="#a78bfa" />
                    <span className="text-white font-medium">{h.original_filename || 'Resume'}</span>
                    <span className="text-xs text-slate-500">{new Date(h.created_at).toLocaleString()}</span>
                  </div>
                  <p className="text-slate-400 text-sm leading-relaxed mb-3">{h.summary}</p>
                  <div className="flex flex-wrap gap-1">
                    {h.missing_skills.slice(0, 4).map(s => (
                      <span key={s} className="skill-chip">⚡ {s}</span>
                    ))}
                    {h.missing_skills.length > 4 && (
                      <span className="skill-chip">+{h.missing_skills.length - 4} more</span>
                    )}
                  </div>
                </div>

                <div className="text-center md:text-right">
                  <div className="font-display font-extrabold text-4xl" style={{ color }}>{h.score}</div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">score</p>
                </div>

              </div>
            )
          })}

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-4 mt-4">
              <button 
                onClick={() => setPage(p => Math.max(1, p - 1))} 
                disabled={page === 1} 
                className="p-2 rounded-lg text-slate-400 hover:text-white disabled:opacity-30" 
                style={{ border: '1px solid rgba(99,102,241,0.2)' }}
              >
                <ChevronLeft size={18} />
              </button>
              <span className="text-slate-400 text-sm">Page {page} of {totalPages}</span>
              <button 
                onClick={() => setPage(p => Math.min(totalPages, p + 1))} 
                disabled={page === totalPages} 
                className="p-2 rounded-lg text-slate-400 hover:text-white disabled:opacity-30" 
                style={{ border: '1px solid rgba(99,102,241,0.2)' }}
              >
                <ChevronRight size={18} />
              </button>
            </div>
          )}
        </div>
      )}
    </DashboardLayout>
  )
}