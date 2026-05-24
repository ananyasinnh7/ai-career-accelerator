'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { isLoggedIn, getRole } from '@/lib/auth'
import Link from 'next/link'
import { Zap, ArrowRight, Brain, Users, Target } from 'lucide-react'

export default function LandingPage() {
  const router = useRouter()

  useEffect(() => {
    if (isLoggedIn()) {
      router.push(getRole() === 'recruiter' ? '/recruiter/dashboard' : '/dashboard')
    }
  }, [router])

  return (
    <div className="min-h-screen flex flex-col">
      {/* Navbar */}
      <nav style={{ background: 'rgba(10,10,15,0.9)', borderBottom: '1px solid rgba(99,102,241,0.2)' }} className="px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div style={{ background: 'linear-gradient(135deg, #7c3aed, #2563eb)', borderRadius: 8, padding: 6 }}>
            <Zap size={18} color="white" />
          </div>
          <span className="font-display font-bold text-lg gradient-text">CareerAI</span>
        </div>
        <div className="flex gap-3">
          <Link href="/login" className="px-4 py-2 rounded-lg text-sm text-slate-400 hover:text-white transition-all">Login</Link>
          <Link href="/register" className="btn-primary" style={{ width: 'auto', padding: '0.5rem 1.25rem', fontSize: '0.875rem' }}>Get Started</Link>
        </div>
      </nav>

      {/* Hero */}
      <div className="flex-1 flex flex-col items-center justify-center text-center px-4 py-24">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-8" style={{ background: 'rgba(167,139,250,0.1)', border: '1px solid rgba(167,139,250,0.3)' }}>
          <Brain size={14} color="#a78bfa" />
          {/* AI Model Corrected Here */}
          <span className="text-xs text-purple-300 font-medium">Powered by Google Gemini 3.0</span>
        </div>
        
        <h1 className="font-display font-extrabold text-5xl md:text-7xl mb-6 leading-tight">
          <span className="gradient-text">AI-Powered</span><br />
          <span className="text-white">Career Matching</span>
        </h1>
        
        <p className="text-slate-400 text-lg md:text-xl max-w-2xl mb-12 leading-relaxed">
          Upload your resume, get an AI match score against any job, discover your skill gaps, and receive a personalized project roadmap.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4">
          <Link href="/register" className="flex items-center gap-2 justify-center btn-primary" style={{ width: 'auto', padding: '0.875rem 2rem', fontSize: '1rem' }}>
            Get Started Free <ArrowRight size={18} />
          </Link>
          <Link href="/register?role=recruiter" className="flex items-center gap-2 justify-center px-8 py-3 rounded-xl text-slate-300 hover:text-white transition-all" style={{ border: '1px solid rgba(99,102,241,0.3)', background: 'rgba(15,15,30,0.5)' }}>
            I am a Recruiter <ArrowRight size={18} />
          </Link>
        </div>

        {/* Feature cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-24 w-full max-w-5xl">
          {[
            { icon: Target, title: 'AI Match Score', desc: 'Get an instant 1-100 score showing how well your resume matches any job description.' },
            { icon: Brain, title: 'Skill Gap Analysis', desc: 'Discover exactly which skills you are missing and get a personalized project to build them.' },
            { icon: Users, title: 'Two-Sided Platform', desc: 'Recruiters post jobs and get ranked candidate lists. Candidates match themselves to opportunities.' },
          ].map(({ icon: Icon, title, desc }) => (
            <div key={title} className="card text-left">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-4" style={{ background: 'linear-gradient(135deg, rgba(124,58,237,0.2), rgba(37,99,235,0.2))', border: '1px solid rgba(167,139,250,0.3)' }}>
                <Icon size={20} color="#a78bfa" />
              </div>
              <h3 className="font-display font-semibold text-white mb-2">{title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}