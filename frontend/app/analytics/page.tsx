'use client'
import { useEffect, useState } from 'react'
import { BarChart2, Loader2, TrendingUp, Users, Briefcase, Star } from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar,
} from 'recharts'
import { getToken, getRole } from '@/lib/auth'
import DashboardLayout from '@/components/layout/DashboardLayout'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function AnalyticsPage() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const role = getRole()

  useEffect(() => {
    const endpoint = role === 'recruiter'
      ? '/analytics/recruiter/dashboard'
      : '/analytics/candidate/dashboard'

    fetch(`${API}${endpoint}`, {
      headers: { Authorization: `Bearer ${getToken()}` },
    })
      .then(r => r.json())
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <DashboardLayout>
      <div className="flex justify-center py-32">
        <Loader2 size={28} className="animate-spin" style={{ color: '#6366f1' }} />
      </div>
    </DashboardLayout>
  )

  return (
    <DashboardLayout>
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center gap-3">
          <BarChart2 size={22} style={{ color: '#6366f1' }} />
          <h1 className="text-2xl font-bold text-white">Analytics</h1>
        </div>

        {/* ── Candidate view ── */}
        {role === 'candidate' && data && (
          <>
            {/* Stat cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard label="Applications" value={data.applications?.total_applications ?? 0} icon={<Briefcase size={16} />} />
              <StatCard label="Avg Score" value={`${data.applications?.avg_match_score?.toFixed(1) ?? 0}%`} icon={<Star size={16} />} />
              <StatCard label="Shortlisted" value={data.applications?.total_shortlisted ?? 0} icon={<TrendingUp size={16} />} color="#10b981" />
              <StatCard label="New This Week" value={data.new_matches_this_week ?? 0} icon={<Star size={16} />} color="#f59e0b" />
            </div>

            {/* Skill gaps */}
            {data.top_missing_skills?.length > 0 && (
              <ChartCard title="Top Skill Gaps — improve these to score higher">
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={data.top_missing_skills.map((s: string, i: number) => ({ skill: s, count: data.top_missing_skills.length - i }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="skill" tick={{ fill: '#64748b', fontSize: 12 }} />
                    <YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
                    <Tooltip contentStyle={{ background: '#0f0f18', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 8 }} />
                    <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
            )}
          </>
        )}

        {/* ── Recruiter view ── */}
        {role === 'recruiter' && data && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard label="Jobs Posted" value={data.total_jobs_posted ?? 0} icon={<Briefcase size={16} />} />
              <StatCard label="Active Jobs" value={data.active_jobs ?? 0} icon={<TrendingUp size={16} />} color="#10b981" />
              <StatCard label="Total Applicants" value={data.total_applicants ?? 0} icon={<Users size={16} />} color="#f59e0b" />
              <StatCard label="Shortlisted" value={data.total_shortlisted ?? 0} icon={<Star size={16} />} color="#a78bfa" />
            </div>

            {/* Top jobs table */}
            {data.top_jobs?.length > 0 && (
              <ChartCard title="Top Jobs by Applications">
                <div className="space-y-3">
                  {data.top_jobs.map((job: any, i: number) => (
                    <div key={i} className="flex items-center justify-between py-2"
                      style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                      <span className="text-sm text-slate-300">{job.title || job.job_title}</span>
                      <span className="text-sm font-semibold" style={{ color: '#6366f1' }}>
                        {job.applicants ?? job.count ?? 0} applicants
                      </span>
                    </div>
                  ))}
                </div>
              </ChartCard>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  )
}

function StatCard({ label, value, icon, color = '#6366f1' }: {
  label: string; value: string | number; icon: React.ReactNode; color?: string
}) {
  return (
    <div className="p-4 rounded-xl" style={{
      background: 'rgba(255,255,255,0.03)',
      border: '1px solid rgba(255,255,255,0.07)',
    }}>
      <div className="flex items-center gap-2 mb-2" style={{ color }}>
        {icon}
        <span className="text-xs text-slate-500">{label}</span>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  )
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="p-6 rounded-xl" style={{
      background: 'rgba(255,255,255,0.03)',
      border: '1px solid rgba(255,255,255,0.07)',
    }}>
      <h2 className="text-sm font-semibold text-slate-400 mb-5">{title}</h2>
      {children}
    </div>
  )
}
