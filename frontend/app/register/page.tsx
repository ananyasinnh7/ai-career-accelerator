'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import toast from 'react-hot-toast'
import { authApi } from '@/lib/api'
import { Zap, User, Briefcase } from 'lucide-react'

export default function RegisterPage() {
  const router = useRouter()
  const params = useSearchParams()
  
  const [form, setForm] = useState({ email: '', password: '', full_name: '', role: 'candidate' })
  const [loading, setLoading] = useState(false)

  // Auto-select recruiter if they clicked the recruiter button on the landing page
  useEffect(() => { 
    if (params.get('role') === 'recruiter') {
      setForm(f => ({ ...f, role: 'recruiter' })) 
    }
  }, [params])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await authApi.register(form)
      toast.success('Account created! Please login.')
      router.push('/login')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Registration failed')
    } finally { 
      setLoading(false) 
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-4">
            <div style={{ background: 'linear-gradient(135deg, #7c3aed, #2563eb)', borderRadius: 8, padding: 8 }}>
              <Zap size={20} color="white" />
            </div>
            <span className="font-display font-bold text-xl gradient-text">CareerAI</span>
          </div>
          <h1 className="font-display font-bold text-3xl text-white mb-2">Create account</h1>
          <p className="text-slate-400 text-sm">Join the AI-powered talent platform</p>
        </div>

        <div className="card">
          {/* Role selector */}
          <div className="grid grid-cols-2 gap-3 mb-6">
            {(['candidate', 'recruiter'] as const).map(role => (
              <button 
                key={role} 
                type="button" 
                onClick={() => setForm(f => ({ ...f, role }))}
                className="flex flex-col items-center gap-2 p-4 rounded-xl transition-all"
                style={{ 
                  border: `1px solid ${form.role === role ? '#a78bfa' : 'rgba(99,102,241,0.2)'}`, 
                  background: form.role === role ? 'rgba(167,139,250,0.1)' : 'transparent' 
                }}
              >
                {role === 'candidate' ? (
                  <User size={20} color={form.role === role ? '#a78bfa' : '#475569'} />
                ) : (
                  <Briefcase size={20} color={form.role === role ? '#a78bfa' : '#475569'} />
                )}
                <span className="text-sm font-medium capitalize" style={{ color: form.role === role ? '#a78bfa' : '#475569' }}>
                  {role}
                </span>
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div>
              <label className="text-xs text-slate-400 mb-1 block uppercase tracking-wider">Full Name</label>
              <input 
                className="input-field" 
                placeholder="Your full name" 
                value={form.full_name} 
                onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))} 
                required 
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block uppercase tracking-wider">Email</label>
              <input 
                className="input-field" 
                type="email" 
                placeholder="you@example.com" 
                value={form.email} 
                onChange={e => setForm(f => ({ ...f, email: e.target.value }))} 
                required 
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block uppercase tracking-wider">Password</label>
              <input 
                className="input-field" 
                type="password" 
                placeholder="Min 8 chars, 1 uppercase, 1 number" 
                value={form.password} 
                onChange={e => setForm(f => ({ ...f, password: e.target.value }))} 
                required 
              />
            </div>
            <button type="submit" disabled={loading} className="btn-primary mt-2">
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          <p className="text-center text-slate-400 text-sm mt-4">
            Already have an account? <Link href="/login" className="text-purple-400 hover:text-purple-300">Sign in</Link>
          </p>
        </div>

      </div>
    </div>
  )
}