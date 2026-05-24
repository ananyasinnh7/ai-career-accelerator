'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import toast from 'react-hot-toast'
import { authApi } from '@/lib/api'
import { saveTokens, getRole } from '@/lib/auth'
import { Zap, Eye, EyeOff } from 'lucide-react'

export default function LoginPage() {
  const router = useRouter()
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [show, setShow] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await authApi.login(form)
      saveTokens(data.access_token, data.refresh_token)
      toast.success('Welcome back!')
      
      const role = getRole()
      router.push(role === 'recruiter' ? '/recruiter/dashboard' : '/dashboard')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Invalid credentials')
    } finally { 
      setLoading(false) 
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-4">
            <div style={{ background: 'linear-gradient(135deg, #7c3aed, #2563eb)', borderRadius: 8, padding: 8 }}>
              <Zap size={20} color="white" />
            </div>
            <span className="font-display font-bold text-xl gradient-text">CareerAI</span>
          </div>
          <h1 className="font-display font-bold text-3xl text-white mb-2">Welcome back</h1>
          <p className="text-slate-400 text-sm">Sign in to your account</p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
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
              <div className="relative">
                <input 
                  className="input-field pr-10" 
                  type={show ? 'text' : 'password'} 
                  placeholder="••••••••" 
                  value={form.password} 
                  onChange={e => setForm(f => ({ ...f, password: e.target.value }))} 
                  required 
                />
                <button 
                  type="button" 
                  onClick={() => setShow(!show)} 
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400"
                >
                  {show ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading} className="btn-primary mt-2">
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
          
          <p className="text-center text-slate-400 text-sm mt-4">
            No account? <Link href="/register" className="text-purple-400 hover:text-purple-300">Create one</Link>
          </p>
        </div>
        
      </div>
    </div>
  )
}