'use client'
import { useEffect, useState } from 'react'
import { Shield, Users, Briefcase, BarChart2, Loader2, UserX, UserCheck, Trash2 } from 'lucide-react'
import { getToken } from '@/lib/auth'
import DashboardLayout from '@/components/layout/DashboardLayout'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Stats {
  users: { total: number; total_candidates: number; total_recruiters: number; verified: number; active: number }
  jobs: { total: number; active: number }
  matches: { total: number; avg_score: number }
}

interface User {
  id: number
  email: string
  full_name: string
  role: string
  is_verified: boolean
  is_active: boolean
  is_admin: boolean
}

const cardStyle = {
  background: 'rgba(255,255,255,0.03)',
  border: '1px solid rgba(255,255,255,0.07)',
  borderRadius: 12,
  padding: 20,
}

export default function AdminPage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'stats' | 'users'>('stats')
  const token = getToken()

  useEffect(() => {
    Promise.all([
      fetch(`${API}/admin/stats`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()),
      fetch(`${API}/admin/users`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()),
    ]).then(([statsData, usersData]) => {
      setStats(statsData)
      setUsers(usersData.results || [])
    }).catch(console.error)
    .finally(() => setLoading(false))
  }, [])

  const toggleUser = async (userId: number, isActive: boolean) => {
    const action = isActive ? 'deactivate' : 'activate'
    await fetch(`${API}/admin/users/${userId}/${action}`, {
      method: 'PUT',
      headers: { Authorization: `Bearer ${token}` },
    })
    setUsers(prev => prev.map(u => u.id === userId ? { ...u, is_active: !isActive } : u))
  }

  if (loading) return (
    <DashboardLayout>
      <div className="flex justify-center py-32">
        <Loader2 size={28} className="animate-spin" style={{ color: '#6366f1' }} />
      </div>
    </DashboardLayout>
  )

  return (
    <DashboardLayout>
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <Shield size={22} style={{ color: '#6366f1' }} />
          <h1 className="text-2xl font-bold text-white">Admin Panel</h1>
        </div>

        {/* Tabs */}
        <div
          className="flex gap-1 p-1 rounded-lg w-fit"
          style={{ background: 'rgba(255,255,255,0.05)' }}
        >
          {(['stats', 'users'] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className="px-4 py-1.5 rounded-md text-sm font-medium transition capitalize"
              style={{
                background: tab === t ? 'rgba(99,102,241,0.3)' : 'transparent',
                color: tab === t ? '#a5b4fc' : '#64748b',
              }}
            >
              {t}
            </button>
          ))}
        </div>

        {/* ── Stats tab ── */}
        {tab === 'stats' && stats && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <StatCard label="Total Users" value={stats.users.total} icon={<Users size={16} />} />
              <StatCard label="Candidates" value={stats.users.total_candidates} icon={<Users size={16} />} color="#a78bfa" />
              <StatCard label="Recruiters" value={stats.users.total_recruiters} icon={<Users size={16} />} color="#38bdf8" />
              <StatCard label="Total Jobs" value={stats.jobs.total} icon={<Briefcase size={16} />} color="#f59e0b" />
              <StatCard label="Active Jobs" value={stats.jobs.active} icon={<Briefcase size={16} />} color="#10b981" />
              <StatCard label="Total Matches" value={stats.matches.total} icon={<BarChart2 size={16} />} color="#ec4899" />
            </div>
            <div style={cardStyle}>
              <p className="text-sm text-slate-400 mb-1">Average Match Score</p>
              <p className="text-3xl font-bold text-white">{stats.matches.avg_score}%</p>
            </div>
          </div>
        )}

        {/* ── Users tab ── */}
        {tab === 'users' && (
          <div style={cardStyle}>
            <p className="text-sm text-slate-400 mb-4">{users.length} users</p>
            <div className="space-y-2">
              {users.map(u => (
                <div
                  key={u.id}
                  className="flex items-center justify-between p-3 rounded-lg"
                  style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}
                >
                  <div>
                    <p className="text-sm font-medium text-white">{u.full_name || u.email}</p>
                    <p className="text-xs text-slate-500">{u.email} · {u.role}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className="text-xs px-2 py-0.5 rounded-full"
                      style={{
                        background: u.is_active ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
                        color: u.is_active ? '#10b981' : '#ef4444',
                      }}
                    >
                      {u.is_active ? 'Active' : 'Inactive'}
                    </span>
                    {!u.is_admin && (
                      <button
                        onClick={() => toggleUser(u.id, u.is_active)}
                        className="p-1.5 rounded-lg transition"
                        style={{ color: u.is_active ? '#ef4444' : '#10b981' }}
                        title={u.is_active ? 'Deactivate' : 'Activate'}
                      >
                        {u.is_active ? <UserX size={15} /> : <UserCheck size={15} />}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}

function StatCard({ label, value, icon, color = '#6366f1' }: {
  label: string; value: number; icon: React.ReactNode; color?: string
}) {
  return (
    <div style={cardStyle}>
      <div className="flex items-center gap-2 mb-2" style={{ color }}>
        {icon}
        <span className="text-xs text-slate-500">{label}</span>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  )
}
