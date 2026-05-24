'use client'

import { useEffect, useState } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { jobsApi, authApi, JobPosting, User } from '@/lib/api'
import { Briefcase, Users, PlusCircle, ArrowRight, TrendingUp } from 'lucide-react'
import Link from 'next/link'

export default function RecruiterDashboard() {
  const [user, setUser] = useState<User | null>(null)
  const [jobs, setJobs] = useState<JobPosting[]>([])
  const [total, setTotal] = useState(0)

  useEffect(() => {
    authApi.me()
      .then(r => setUser(r.data))
      .catch(() => {})
      
    jobsApi.mine(1, 5)
      .then(r => { 
        setJobs(r.data.results); 
        setTotal(r.data.total) 
      })
      .catch(() => {})
  }, [])

  const activeJobs = jobs.filter(j => j.status === 'active').length

  return (
    <DashboardLayout requiredRole="recruiter">
      
      <div className="mb-8">
        <h1 className="font-display font-bold text-3xl text-white mb-1">
          Welcome, {user?.full_name?.split(' ')[0] || 'Recruiter'} 👋
        </h1>
        <p className="text-slate-400">Manage your job postings and review candidates</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
        {[
          { label: 'Total Jobs', value: total, icon: Briefcase, color: '#a78bfa' },
          { label: 'Active Jobs', value: activeJobs, icon: TrendingUp, color: '#4ade80' },
          { label: 'Post New Job', value: '+', icon: PlusCircle, color: '#38bdf8', href: '/recruiter/jobs/new' },
        ].map(({ label, value, icon: Icon, color, href }) => (
          href ? (
            <Link key={label} href={href} className="card flex items-center gap-4 hover:border-purple-500 transition-all cursor-pointer">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${color}20` }}>
                <Icon size={20} color={color} />
              </div>
              <div>
                <p className="text-xs text-slate-400 uppercase tracking-wider">{label}</p>
                <p className="font-display font-bold text-2xl text-white">{value}</p>
              </div>
            </Link>
          ) : (
            <div key={label} className="card flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${color}20` }}>
                <Icon size={20} color={color} />
              </div>
              <div>
                <p className="text-xs text-slate-400 uppercase tracking-wider">{label}</p>
                <p className="font-display font-bold text-2xl text-white">{value}</p>
              </div>
            </div>
          )
        ))}
      </div>

      {/* Recent jobs */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h2 className="font-display font-semibold text-white">Recent Job Postings</h2>
          <Link href="/recruiter/jobs" className="text-purple-400 text-sm hover:text-purple-300 flex items-center gap-1">
            View all <ArrowRight size={14} />
          </Link>
        </div>
        
        {jobs.length === 0 ? (
          <div className="text-center py-8">
            <Briefcase size={32} color="#334155" className="mx-auto mb-3" />
            <p className="text-slate-500 text-sm">No jobs posted yet</p>
            <Link href="/recruiter/jobs/new" className="text-purple-400 text-sm hover:text-purple-300">
              Post your first job →
            </Link>
          </div>
        ) : jobs.map(job => (
          <div key={job.id} className="flex items-center justify-between py-3" style={{ borderBottom: '1px solid rgba(99,102,241,0.1)' }}>
            <div>
              <p className="text-white font-medium">{job.title}</p>
              <p className="text-slate-400 text-sm">{job.company} · {job.location || 'Remote'}</p>
            </div>
            <div className="flex items-center gap-3">
              <span className={`status-badge status-${job.status}`}>{job.status}</span>
              <Link href={`/recruiter/jobs/${job.id}`} className="text-purple-400 hover:text-purple-300">
                <ArrowRight size={16} />
              </Link>
            </div>
          </div>
        ))}
      </div>
      
    </DashboardLayout>
  )
}