'use client'
import { useState } from 'react'
import { Search, Briefcase, MapPin, DollarSign, Loader2, Filter } from 'lucide-react'
import Link from 'next/link'
import { getToken, getRole } from '@/lib/auth'
import DashboardLayout from '@/components/layout/DashboardLayout'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Job {
  id: number
  title: string
  company_name: string
  location: string
  salary_min: number
  salary_max: number
  experience_level: string
  job_type: string
  created_at: string
}

interface SearchResults {
  total: number
  results: Job[]
}

const inputStyle = {
  background: 'rgba(255,255,255,0.05)',
  border: '1px solid rgba(99,102,241,0.2)',
  borderRadius: 8,
  color: 'white',
  padding: '8px 12px',
  fontSize: 14,
  width: '100%',
  outline: 'none',
}

const selectStyle = { ...inputStyle }

export default function SearchPage() {
  const role = getRole()
  const [q, setQ] = useState('')
  const [location, setLocation] = useState('')
  const [salaryMin, setSalaryMin] = useState('')
  const [salaryMax, setSalaryMax] = useState('')
  const [experienceLevel, setExperienceLevel] = useState('')
  const [jobType, setJobType] = useState('')
  const [results, setResults] = useState<SearchResults | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSearch = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (q) params.set('q', q)
      if (location) params.set('location', location)
      if (salaryMin) params.set('salary_min', salaryMin)
      if (salaryMax) params.set('salary_max', salaryMax)
      if (experienceLevel) params.set('experience_level', experienceLevel)
      if (jobType) params.set('job_type', jobType)

      const res = await fetch(`${API}/search/jobs?${params}`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      })
      const data = await res.json()
      setResults(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <Search size={22} style={{ color: '#6366f1' }} />
          <h1 className="text-2xl font-bold text-white">Search Jobs</h1>
        </div>

        {/* Search bar */}
        <div className="flex gap-3">
          <input
            style={inputStyle}
            placeholder="Search job title, company, keywords..."
            value={q}
            onChange={e => setQ(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
          />
          <button
            onClick={handleSearch}
            className="flex items-center gap-2 px-5 py-2 rounded-lg font-medium text-sm text-white transition-all shrink-0"
            style={{ background: 'linear-gradient(135deg, #7c3aed, #2563eb)' }}
          >
            <Search size={15} /> Search
          </button>
        </div>

        {/* Filters */}
        <div
          className="p-4 rounded-xl"
          style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}
        >
          <div className="flex items-center gap-2 mb-4">
            <Filter size={15} style={{ color: '#6366f1' }} />
            <span className="text-sm font-medium text-slate-400">Filters</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div>
              <label className="text-xs text-slate-500 mb-1 block">Location</label>
              <input
                style={inputStyle}
                placeholder="e.g. Remote, NYC"
                value={location}
                onChange={e => setLocation(e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">Min Salary</label>
              <input
                style={inputStyle}
                type="number"
                placeholder="e.g. 50000"
                value={salaryMin}
                onChange={e => setSalaryMin(e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">Experience</label>
              <select
                style={selectStyle}
                value={experienceLevel}
                onChange={e => setExperienceLevel(e.target.value)}
              >
                <option value="">Any</option>
                <option value="entry">Entry Level</option>
                <option value="mid">Mid Level</option>
                <option value="senior">Senior</option>
                <option value="lead">Lead</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">Job Type</label>
              <select
                style={selectStyle}
                value={jobType}
                onChange={e => setJobType(e.target.value)}
              >
                <option value="">Any</option>
                <option value="full-time">Full-time</option>
                <option value="part-time">Part-time</option>
                <option value="contract">Contract</option>
                <option value="remote">Remote</option>
              </select>
            </div>
          </div>
        </div>

        {/* Results */}
        {loading && (
          <div className="flex justify-center py-16">
            <Loader2 size={24} className="animate-spin" style={{ color: '#6366f1' }} />
          </div>
        )}

        {results && !loading && (
          <>
            <p className="text-sm text-slate-500">{results.total} job{results.total !== 1 ? 's' : ''} found</p>
            <div className="space-y-3">
              {results.results.length === 0 ? (
                <div className="text-center py-16 text-slate-500">
                  <Briefcase size={36} className="mx-auto mb-3 opacity-20" />
                  <p className="text-sm">No jobs match your filters</p>
                </div>
              ) : (
                results.results.map(job => (
                  <Link key={job.id} href={`/jobs/${job.id}`}>
                    <div
                      className="p-4 rounded-xl cursor-pointer transition-all hover:scale-[1.01]"
                      style={{
                        background: 'rgba(255,255,255,0.03)',
                        border: '1px solid rgba(255,255,255,0.07)',
                      }}
                      onMouseEnter={e => (e.currentTarget.style.border = '1px solid rgba(99,102,241,0.3)')}
                      onMouseLeave={e => (e.currentTarget.style.border = '1px solid rgba(255,255,255,0.07)')}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-semibold text-white text-sm">{job.title}</h3>
                          <p className="text-slate-400 text-sm mt-0.5">{job.company_name}</p>
                        </div>
                        {job.experience_level && (
                          <span
                            className="text-xs px-2 py-0.5 rounded-full"
                            style={{ background: 'rgba(99,102,241,0.15)', color: '#a5b4fc' }}
                          >
                            {job.experience_level}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
                        {job.location && (
                          <span className="flex items-center gap-1">
                            <MapPin size={12} /> {job.location}
                          </span>
                        )}
                        {(job.salary_min || job.salary_max) && (
                          <span className="flex items-center gap-1">
                            <DollarSign size={12} />
                            {job.salary_min ? `$${job.salary_min.toLocaleString()}` : ''}
                            {job.salary_min && job.salary_max ? ' – ' : ''}
                            {job.salary_max ? `$${job.salary_max.toLocaleString()}` : ''}
                          </span>
                        )}
                        {job.job_type && <span>{job.job_type}</span>}
                      </div>
                    </div>
                  </Link>
                ))
              )}
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  )
}
