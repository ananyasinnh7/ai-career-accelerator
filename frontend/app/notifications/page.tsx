'use client'
import { useEffect, useState } from 'react'
import { Bell, CheckCheck, Loader2 } from 'lucide-react'
import { getToken } from '@/lib/auth'
import DashboardLayout from '@/components/layout/DashboardLayout'

interface Notification {
  id: number
  type: string
  title: string
  message: string
  is_read: boolean
  created_at: string
}

const TYPE_ICONS: Record<string, string> = {
  new_match: '🎯',
  shortlisted: '⭐',
  rejected: '❌',
  score_ready: '📊',
  auto_match: '🤖',
  default: '🔔',
}

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'unread' | 'all'>('unread')

  const fetchNotifications = async () => {
    setLoading(true)
    try {
      const token = getToken()
      const endpoint = tab === 'unread' ? '/notifications/' : '/notifications/all'
      const res = await fetch(`${API}${endpoint}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json()
      setNotifications(data.results || [])
    } catch {}
    finally { setLoading(false) }
  }

  useEffect(() => { fetchNotifications() }, [tab])

  const markRead = async (id: number) => {
    const token = getToken()
    await fetch(`${API}/notifications/${id}/read`, {
      method: 'PUT',
      headers: { Authorization: `Bearer ${token}` },
    })
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n))
  }

  const markAllRead = async () => {
    const token = getToken()
    await fetch(`${API}/notifications/read-all`, {
      method: 'PUT',
      headers: { Authorization: `Bearer ${token}` },
    })
    setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
  }

  const unreadCount = notifications.filter(n => !n.is_read).length

  return (
    <DashboardLayout>
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Bell size={22} style={{ color: '#6366f1' }} />
            <h1 className="text-2xl font-bold text-white">Notifications</h1>
            {unreadCount > 0 && (
              <span
                className="text-xs font-bold px-2 py-0.5 rounded-full text-white"
                style={{ background: '#ef4444' }}
              >
                {unreadCount}
              </span>
            )}
          </div>
          {unreadCount > 0 && (
            <button
              onClick={markAllRead}
              className="flex items-center gap-1.5 text-sm text-indigo-400 hover:text-indigo-300 transition"
            >
              <CheckCheck size={15} /> Mark all read
            </button>
          )}
        </div>

        {/* Tabs */}
        <div
          className="flex gap-1 mb-6 p-1 rounded-lg w-fit"
          style={{ background: 'rgba(255,255,255,0.05)' }}
        >
          {(['unread', 'all'] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className="px-4 py-1.5 rounded-md text-sm font-medium transition"
              style={{
                background: tab === t ? 'rgba(99,102,241,0.3)' : 'transparent',
                color: tab === t ? '#a5b4fc' : '#64748b',
              }}
            >
              {t === 'unread' ? 'Unread' : 'All'}
            </button>
          ))}
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex justify-center py-20">
            <Loader2 size={24} className="animate-spin" style={{ color: '#6366f1' }} />
          </div>
        ) : notifications.length === 0 ? (
          <div className="text-center py-20 text-slate-500">
            <Bell size={36} className="mx-auto mb-3 opacity-20" />
            <p className="text-sm">
              {tab === 'unread' ? 'No unread notifications' : 'No notifications yet'}
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {notifications.map(n => (
              <div
                key={n.id}
                onClick={() => !n.is_read && markRead(n.id)}
                className="flex items-start gap-3 p-4 rounded-xl cursor-pointer transition-all"
                style={{
                  background: !n.is_read
                    ? 'rgba(99,102,241,0.08)'
                    : 'rgba(255,255,255,0.03)',
                  border: `1px solid ${!n.is_read ? 'rgba(99,102,241,0.2)' : 'rgba(255,255,255,0.06)'}`,
                }}
              >
                <span className="text-xl mt-0.5">
                  {TYPE_ICONS[n.type] || TYPE_ICONS.default}
                </span>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm ${!n.is_read ? 'font-semibold text-white' : 'text-slate-300'}`}>
                    {n.title}
                  </p>
                  {n.message && (
                    <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{n.message}</p>
                  )}
                  <p className="text-xs text-slate-600 mt-1">
                    {new Date(n.created_at).toLocaleString()}
                  </p>
                </div>
                {!n.is_read && (
                  <div
                    className="w-2 h-2 rounded-full mt-2 shrink-0"
                    style={{ background: '#6366f1' }}
                  />
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
