'use client'
import { useEffect, useState } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { jobsApi, JobPosting } from '@/lib/api'
import { Search, Briefcase, MapPin, DollarSign, Zap, ChevronLeft, ChevronRight } from 'lucide-react'
import toast from 'react-hot-toast'

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobPosting[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [query, setQuery] = useState('')
  const [matching, setMatching] = useState<number | null>(null)
  const size = 10

  useEffect(() => {
    jobsApi.list(page, size, query)
      .then(r => { setJobs(r.data.results); setTotal(r.data.total) })
      .catch(() => {})
  }, [page, query])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setQuery(search)
    setPage(1)
  }

  const handleMatch = async (jobId: number) => {
    setMatching(jobId)
    try {
      const { data } = await jobsApi.matchMe(jobId)
      toast.success(`Matched! Score: ${data.score}/100`)
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Match failed — score a resume first')
    } finally { setMatching(null) }
  }

  const totalPages = Math.ceil(total / size)

  return (
    <DashboardLayout requiredRole="candidate">
      <div className="mb-8">
        <h1 className="font-display font-bold text-3xl text-white mb-1">Browse Jobs</h1>
        <p className="text-slate-400">{total} active opportunities</p>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-3 mb-6">
        <div className="flex-1 relative">
          <Search size={16} color="#475569" className="absolute left-3 top-1/2 -translate-y-1/2" />
          <input className="input-field pl-9" placeholder="Search jobs, companies, skills..."
            value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <button type="submit" className="btn-primary" style={{ width: 'auto', padding: '0.75rem 1.5rem' }}>
          Search
        </button>
      </form>

      {jobs.length === 0 ? (
        <div className="card text-center py-16">
          <Briefcase size={48} color="#1e293b" className="mx-auto mb-4" />
          <p className="text-slate-500 font-display font-semibold">No jobs found</p>
          <p className="text-slate-600 text-sm mt-1">Try a different search term</p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {jobs.map(job => (
            <div key={job.id} className="card flex flex-col md:flex-row md:items-start gap-4">
              <div className="flex-1">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="font-display font-semibold text-white text-lg">{job.title}</h3>
                    <p className="text-purple-400 font-medium">{job.company}</p>
                  </div>
                  <span className={`status-badge status-${job.status}`}>{job.status}</span>
                </div>
                <div className="flex flex-wrap gap-3 mb-3 text-sm text-slate-400">
                  {job.location && <span className="flex items-center gap-1"><MapPin size={13} />{job.location}</span>}
                  {job.salary_range && <span className="flex items-center gap-1"><DollarSign size={13} />{job.salary_range}</span>}
                  {job.job_type && <span className="capitalize">{job.job_type}</span>}
                  {job.experience_level && <span className="capitalize">{job.experience_level}</span>}
                </div>
                <p className="text-slate-400 text-sm leading-relaxed mb-3">
                  {(job.description || '').slice(0, 200)}...
                </p>
                <div className="flex flex-wrap gap-1">
                  {(job.required_skills || []).slice(0, 6).map(s => (
                    <span key={s} className="px-2 py-0.5 rounded-full text-xs"
                      style={{ background: 'rgba(167,139,250,0.1)', border: '1px solid rgba(167,139,250,0.3)', color: '#a78bfa' }}>
                      {s}
                    </span>
                  ))}
                  {job.required_skills.length > 6 && (
                    <span className="text-xs text-slate-500 self-center">+{job.required_skills.length - 6} more</span>
                  )}
                </div>
              </div>
              <div className="flex flex-col gap-2 md:min-w-32">
                <button onClick={() => handleMatch(job.id)} disabled={matching === job.id}
                  className="btn-primary flex items-center justify-center gap-1.5"
                  style={{ padding: '0.6rem 1rem' }}>
                  <Zap size={14} />
                  {matching === job.id ? 'Matching...' : 'Match Me'}
                </button>
                <span className="text-xs text-slate-500 text-center">
                  {new Date(job.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))}

          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-4 mt-4">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                className="p-2 rounded-lg text-slate-400 hover:text-white disabled:opacity-30"
                style={{ border: '1px solid rgba(99,102,241,0.2)' }}>
                <ChevronLeft size={18} />
              </button>
              <span className="text-slate-400 text-sm">Page {page} of {totalPages}</span>
              <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                className="p-2 rounded-lg text-slate-400 hover:text-white disabled:opacity-30"
                style={{ border: '1px solid rgba(99,102,241,0.2)' }}>
                <ChevronRight size={18} />
              </button>
            </div>
          )}
        </div>
      )}
    </DashboardLayout>
  )
}