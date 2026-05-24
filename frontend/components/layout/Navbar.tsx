'use client'

import Link from 'next/link'
import { useRouter, usePathname } from 'next/navigation'
import { logout, getRole } from '@/lib/auth'
import { Zap, LogOut, User, Briefcase, FileText, Star, Home, PlusCircle } from 'lucide-react'

export default function Navbar() {
  const router = useRouter()
  const role = getRole()

  const candidateLinks = [
    { href: '/dashboard', label: 'Dashboard', icon: Home },
    { href: '/score', label: 'Score Resume', icon: FileText },
    { href: '/jobs', label: 'Browse Jobs', icon: Briefcase },
    { href: '/matches', label: 'My Matches', icon: Star },
    { href: '/history', label: 'History', icon: FileText },
    { href: '/profile', label: 'Profile', icon: User },
  ]

  const recruiterLinks = [
    { href: '/recruiter/dashboard', label: 'Dashboard', icon: Home },
    { href: '/recruiter/jobs', label: 'My Jobs', icon: Briefcase },
    { href: '/recruiter/jobs/new', label: 'Post Job', icon: PlusCircle },
  ]

  const links = role === 'recruiter' ? recruiterLinks : candidateLinks

  return (
    <nav style={{ background: 'rgba(10,10,15,0.9)', borderBottom: '1px solid rgba(99,102,241,0.2)', backdropFilter: 'blur(10px)' }} className="sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-16">
        
        <Link href={role === 'recruiter' ? '/recruiter/dashboard' : '/dashboard'} className="flex items-center gap-2">
          <div style={{ background: 'linear-gradient(135deg, #7c3aed, #2563eb)', borderRadius: 8, padding: 6 }}>
            <Zap size={18} color="white" />
          </div>
          <span className="font-display font-bold text-lg gradient-text">CareerAI</span>
        </Link>

        <div className="hidden md:flex items-center gap-1">
          {links.map(({ href, label, icon: Icon }) => (
            <Link key={href} href={href}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-all">
              <Icon size={15} />
              {label}
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs px-2 py-1 rounded-full" style={{ 
            background: role === 'recruiter' ? 'rgba(56,189,248,0.15)' : 'rgba(167,139,250,0.15)', 
            color: role === 'recruiter' ? '#38bdf8' : '#a78bfa', 
            border: `1px solid ${role === 'recruiter' ? 'rgba(56,189,248,0.3)' : 'rgba(167,139,250,0.3)'}` 
          }}>
            {role}
          </span>
          <button onClick={() => { logout() }} className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-red-400 transition-all">
            <LogOut size={15} />
            <span className="hidden md:inline">Logout</span>
          </button>
        </div>

      </div>
    </nav>
  )
}