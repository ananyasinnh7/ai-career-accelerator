'use client'

import { useEffect, useState } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { candidateApi, authApi, CandidateProfile } from '@/lib/api'
import toast from 'react-hot-toast'
import { User, Lock, Save } from 'lucide-react'

export default function ProfilePage() {
  const [profile, setProfile] = useState<Partial<CandidateProfile>>({})
  const [loading, setLoading] = useState(false)
  
  const [pwForm, setPwForm] = useState({ current_password: '', new_password: '' })
  const [pwLoading, setPwLoading] = useState(false)

  useEffect(() => { 
    candidateApi.getProfile()
      .then(r => setProfile(r.data))
      .catch(() => {}) 
  }, [])

  const handleProfileSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await candidateApi.updateProfile({ 
        full_name: profile.full_name, 
        headline: profile.headline, 
        bio: profile.bio, 
        location: profile.location, 
        linkedin_url: profile.linkedin_url, 
        github_url: profile.github_url 
      })
      setProfile(data)
      toast.success('Profile updated!')
    } catch { 
      toast.error('Update failed') 
    } finally { 
      setLoading(false) 
    }
  }

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault()
    setPwLoading(true)
    try {
      await authApi.changePassword(pwForm)
      toast.success('Password changed!')
      setPwForm({ current_password: '', new_password: '' })
    } catch (err: any) { 
      toast.error(err.response?.data?.detail || 'Failed') 
    } finally { 
      setPwLoading(false) 
    }
  }

  const field = (label: string, key: keyof CandidateProfile, type = 'text', placeholder = '') => (
    <div key={key}>
      <label className="text-xs text-slate-400 mb-1 block uppercase tracking-wider">{label}</label>
      <input 
        className="input-field" 
        type={type} 
        placeholder={placeholder} 
        value={(profile[key] as string) || ''} 
        onChange={e => setProfile(p => ({ ...p, [key]: e.target.value }))} 
      />
    </div>
  )

  return (
    <DashboardLayout requiredRole="candidate">
      
      <div className="mb-8">
        <h1 className="font-display font-bold text-3xl text-white mb-1">My Profile</h1>
        <p className="text-slate-400">Update your professional information</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        
        {/* Profile form */}
        <div className="card">
          <div className="flex items-center gap-2 mb-6">
            <User size={18} color="#a78bfa" />
            <h2 className="font-display font-semibold text-white">Profile Info</h2>
          </div>
          
          <form onSubmit={handleProfileSave} className="flex flex-col gap-4">
            {field('Full Name', 'full_name', 'text', 'Your full name')}
            {field('Headline', 'headline', 'text', 'e.g. Senior Python Developer')}
            <div>
              <label className="text-xs text-slate-400 mb-1 block uppercase tracking-wider">Bio</label>
              <textarea 
                className="input-field" 
                rows={4} 
                placeholder="Tell recruiters about yourself..." 
                value={profile.bio || ''} 
                onChange={e => setProfile(p => ({ ...p, bio: e.target.value }))} 
              />
            </div>
            {field('Location', 'location', 'text', 'e.g. Indore, India')}
            {field('LinkedIn URL', 'linkedin_url', 'url', 'https://linkedin.com/in/...')}
            {field('GitHub URL', 'github_url', 'url', 'https://github.com/...')}
            
            <button type="submit" disabled={loading} className="btn-primary flex items-center justify-center gap-2 mt-2">
              <Save size={16} />
              {loading ? 'Saving...' : 'Save Profile'}
            </button>
          </form>
        </div>

        {/* Password form */}
        <div className="card h-fit">
          <div className="flex items-center gap-2 mb-6">
            <Lock size={18} color="#a78bfa" />
            <h2 className="font-display font-semibold text-white">Change Password</h2>
          </div>
          
          <form onSubmit={handlePasswordChange} className="flex flex-col gap-4">
            <div>
              <label className="text-xs text-slate-400 mb-1 block uppercase tracking-wider">Current Password</label>
              <input 
                className="input-field" 
                type="password" 
                placeholder="••••••••" 
                value={pwForm.current_password} 
                onChange={e => setPwForm(p => ({ ...p, current_password: e.target.value }))} 
                required 
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block uppercase tracking-wider">New Password</label>
              <input 
                className="input-field" 
                type="password" 
                placeholder="Min 8 chars, 1 uppercase, 1 number" 
                value={pwForm.new_password} 
                onChange={e => setPwForm(p => ({ ...p, new_password: e.target.value }))} 
                required 
              />
            </div>
            
            <button type="submit" disabled={pwLoading} className="btn-primary flex items-center justify-center gap-2">
              <Lock size={16} />
              {pwLoading ? 'Updating...' : 'Update Password'}
            </button>
          </form>
        </div>

      </div>
    </DashboardLayout>
  )
}