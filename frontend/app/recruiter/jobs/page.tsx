'use client'

import { useEffect, useState } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { jobsApi, JobPosting } from '@/lib/api'
import { Briefcase, PlusCircle, ArrowRight, Trash2, MapPin } from 'lucide-react'
import Link from 'next/link'
import toast from 'react-hot-toast'

export default function RecruiterJobsPage() {
  const [jobs, setJobs] = useState<JobPosting[]>([])
  const [total, setTotal] = useState(0)

  const load = () => jobsApi.mine(1, 50)
    .then(r => { 
      setJobs(r.data.results); 
      setTotal(r.data.total) 
    })
    .catch(() => {})

  useEffect(() => { load() }, [])

  const handleClose = async (id: number) => {
    if (!confirm('Close this job posting?')) return
    try { 
      await jobsApi.close(id)
      toast.success('Job closed')
      load() 
    } catch { 
      toast.error('Failed to close job') 
    }
  }

  return (
    <DashboardLayout requiredRole="recruiter">
      
      <div className="flex justify-between items-start mb-8">
        <div>
          <h1 className="font-display font-bold text-3xl text-white mb-1">My Job Postings</h1>
          <p className="text-slate-400">{total} total jobs</p>
        </div>
        <Link href="/recruiter/jobs/new" className="btn-primary flex items-center gap-2" style={{ width: 'auto', padding: '0.75rem 1.25rem' }}>
          <PlusCircle size={16} /> Post New Job
        </Link>
      </div>

      {jobs.length === 0 ? (
        <div className="card text-center py-16">
          <Briefcase size={48} color="#1e293b" className="mx-auto mb-4" />
          <p className="text-slate-500 font-display font-semibold text-lg">No jobs posted yet</p>
          <Link href="/recruiter/jobs/new" className="text-purple-400 hover:text-purple-300 text-sm mt-2 inline-block">
            Post your first job →
          </Link>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {jobs.map(job => (
            <div key={job.id} className="card">
              
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-display font-semibold text-white text-lg">{job.title}</h3>
                  <div className="flex items-center gap-3 mt-1 text-sm text-slate-400">
                    <span className="text-purple-400">{job.company}</span>
                    {job.location && <span className="flex items-center gap-1"><MapPin size={12} />{job.location}</span>}
                    {job.salary_range && <span>{job.salary_range}</span>}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`status-badge status-${job.status}`}>{job.status}</span>
                </div>
              </div>

              <div className="flex flex-wrap gap-1 mb-4">
                {job.required_skills.slice(0, 6).map(s => (
                  <span key={s} className="px-2 py-0.5 rounded-full text-xs" style={{ background: 'rgba(167,139,250,0.1)', border: '1px solid rgba(167,139,250,0.3)', color: '#a78bfa' }}>
                    {s}
                  </span>
                ))}
              </div>

              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">{new Date(job.created_at).toLocaleDateString()}</span>
                <div className="flex gap-2">
                  {job.status === 'active' && (
                    <button 
                      onClick={() => handleClose(job.id)} 
                      className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm text-red-400 hover:text-red-300 transition-all" 
                      style={{ border: '1px solid rgba(248,113,113,0.3)' }}
                    >
                      <Trash2 size={13} /> Close
                    </button>
                  )}
                  <Link 
                    href={`/recruiter/jobs/${job.id}`} 
                    className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm text-purple-400 hover:text-purple-300 transition-all" 
                    style={{ border: '1px solid rgba(167,139,250,0.3)' }}
                  >
                    View Candidates <ArrowRight size={13} />
                  </Link>
                </div>
              </div>

            </div>
          ))}
        </div>
      )}
      
    </DashboardLayout>
  )
}