'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { isLoggedIn, getRole } from '@/lib/auth'
import Navbar from './Navbar'

interface Props { 
  children: React.ReactNode; 
  requiredRole?: 'candidate' | 'recruiter' 
}

export default function DashboardLayout({ children, requiredRole }: Props) {
  const router = useRouter()

  useEffect(() => {
    if (!isLoggedIn()) { 
      router.push('/login'); 
      return 
    }
    
    if (requiredRole && getRole() !== requiredRole) {
      router.push(getRole() === 'recruiter' ? '/recruiter/dashboard' : '/dashboard')
    }
  }, [requiredRole, router])

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  )
}