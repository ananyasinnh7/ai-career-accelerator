'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { jobsApi } from '@/lib/api'
import toast from 'react-hot-toast'
import { PlusCircle, X } from 'lucide-react'

export default function NewJobPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [skillInput, setSkillInput] = useState('')
  const [form, setForm] = useState({
    title: '', company: '', location: '', description: '',
    required_skills: [] as string[],
    salary_range: '', job_type: 'full-time', experience_level: 'mid',
  })

  const addSkill = () => {
    const s = skillInput.trim()
    if (s && !form.required_skills.includes(s)) {
      setForm(f => ({ ...f, required_skills: [...f.required_skills, s] }))
      setSkillInput('')
    }
  }

  const removeSkill = (s: string) =>
    setForm(f => ({ ...f, required_skills: f.required_skills.filter(x => x !== s) }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (form.required_skills.length === 0) { toast.error('Add at least one required skill'); return }
    setLoading(true)
    try {
      await jobsApi.create(form)
      toast.success('Job posted successfully!')
      router.push('/recruiter/jobs')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to post job')
    } finally { setLoading(false) }
  }

  return (
    <DashboardLayout requiredRole="recruiter">
      <div className="mb-8">
        <h1 className="font-display font-bold text-3xl text-white mb-1">Post a New Job</h1>
        <p className="text-slate-400">Fill in the details to attract the right candidates</p>
      </div>

      <div className="max-w-2xl">
        <div className="card">
          <form onSubmit={handleSubmit} className="flex flex-col gap-5">

            <div>
              <label className="text-xs text-slate-400 mb-1 block uppercase tracking-wider">Job Title *</label>
              <input className="input-field" placeholder="e.g. Senior Python Developer"
                value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} required />
            </div>

            <div>
              <label className="text-xs text-slate-400 mb-1 block uppercase tracking-wider">Company *</label>
              <input className="input-field" placeholder="e.g. TechCorp India"
                value={form.company} onChange={e => setForm(f => ({ ...f, company: e.target.value }))} required />
            </div>

            <div>
              <label className="text-xs text-slate-400 mb-1 block uppercase tracking-wider">Location</label>
              <input className="input-field" placeholder="e.g. Bangalore / Remote"
                value={form.location} onChange={e => setForm(f => ({ ...f, location: e.target.value }))} />
            </div>

            <div>
              <label className="text-xs text-slate-400 mb-1 block uppercase tracking-wider">Salary Range</label>
              <input className="input-field" placeholder="e.g. 25-40 LPA"
                value={form.salary_range} onChange={e => setForm(f => ({ ...f, salary_range: e.target.value }))} />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-slate-400 mb-1 block uppercase tracking-wider">Job Type</label>
                <select className="input-field" value={form.job_type}
                  onChange={e => setForm(f => ({ ...f, job_type: e.target.value }))}>
                  {['full-time', 'part-time', 'contract', 'internship'].map(t =>
                    <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block uppercase tracking-wider">Experience Level</label>
                <select className="input-field" value={form.experience_level}
                  onChange={e => setForm(f => ({ ...f, experience_level: e.target.value }))}>
                  {['junior', 'mid', 'senior', 'lead'].map(l =>
                    <option key={l} value={l}>{l}</option>)}
                </select>
              </div>
            </div>

            <div>
              <label className="text-xs text-slate-400 mb-1 block uppercase tracking-wider">
                Job Description * (min 50 chars)
              </label>
              <textarea className="input-field" rows={8}
                placeholder="Describe the role, responsibilities, and requirements in detail..."
                value={form.description}
                onChange={e => setForm(f => ({ ...f, description: e.target.value }))} required />
              <p className="text-xs text-slate-500 mt-1">{form.description.length} chars</p>
            </div>

            <div>
              <label className="text-xs text-slate-400 mb-2 block uppercase tracking-wider">Required Skills *</label>
              <div className="flex gap-2 mb-3">
                <input className="input-field" placeholder="e.g. Python, FastAPI, Docker..."
                  value={skillInput} onChange={e => setSkillInput(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addSkill() } }} />
                <button type="button" onClick={addSkill} className="btn-primary"
                  style={{ width: 'auto', padding: '0.75rem 1rem' }}>
                  <PlusCircle size={16} />
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {form.required_skills.map(s => (
                  <span key={s} className="flex items-center gap-1 px-3 py-1 rounded-full text-sm"
                    style={{ background: 'rgba(167,139,250,0.15)', border: '1px solid rgba(167,139,250,0.3)', color: '#a78bfa' }}>
                    {s}
                    <button type="button" onClick={() => removeSkill(s)}><X size={12} /></button>
                  </span>
                ))}
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn-primary flex items-center justify-center gap-2 mt-2">
              <PlusCircle size={16} />
              {loading ? 'Posting...' : 'Post Job'}
            </button>
          </form>
        </div>
      </div>
    </DashboardLayout>
  )
}