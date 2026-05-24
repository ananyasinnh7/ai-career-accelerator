import axios from 'axios'
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
export const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.clear()
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export interface User { id: number; email: string; full_name: string; role: 'candidate' | 'recruiter' | 'admin'; is_active: boolean; is_verified: boolean }
export interface CandidateProfile extends User { headline?: string; bio?: string; location?: string; linkedin_url?: string; github_url?: string; created_at: string }
export interface TokenResponse { access_token: string; refresh_token: string; token_type: string; expires_in: number }
export interface ResumeScoreResponse { score: number; missing_skills: string[]; recommended_project: string; summary: string }
export interface AnalysisSummary { id: number; original_filename?: string; score: number; missing_skills: string[]; recommended_project: string; summary: string; created_at: string }
export interface JobPosting { id: number; recruiter_id: number; title: string; company: string; location?: string; description: string; required_skills: string[]; salary_range?: string; job_type?: string; experience_level?: string; status: 'active' | 'closed' | 'draft'; created_at: string; updated_at: string }
export interface Match { id: number; candidate_id: number; job_id: number; score: number; missing_skills: string[]; recommended_project: string; summary: string; status: 'pending' | 'reviewed' | 'shortlisted' | 'rejected'; recruiter_notes?: string; created_at: string; job_title?: string; job_company?: string; job_location?: string; candidate_name?: string; candidate_email?: string; candidate_headline?: string }
export interface PaginatedResponse<T> { total: number; page: number; size: number; results: T[] }

export const authApi = {
  register: (data: { email: string; password: string; full_name: string; role: string }) => api.post('/auth/register', data),
  login: (data: { email: string; password: string }) => api.post<TokenResponse>('/auth/login', data),
  me: () => api.get<User>('/auth/me'),
  changePassword: (data: { current_password: string; new_password: string }) => api.put('/auth/me/password', data),
}
export const candidateApi = {
  getProfile: () => api.get<CandidateProfile>('/candidates/me'),
  updateProfile: (data: Partial<CandidateProfile>) => api.put<CandidateProfile>('/candidates/me', data),
  getHistory: (page = 1, size = 10) => api.get<PaginatedResponse<AnalysisSummary>>(`/candidates/me/history?page=${page}&size=${size}`),
  getAnalysis: (id: number) => api.get<AnalysisSummary>(`/candidates/me/history/${id}`),
}
export const resumeApi = {
  score: (file: File, jobDescription: string) => {
    const form = new FormData()
    form.append('resume', file)
    form.append('job_description', jobDescription)
    return api.post<ResumeScoreResponse>('/api/v1/score-resume', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
}
export const jobsApi = {
  list: (page = 1, size = 10, search?: string) => { const q = search ? `&search=${encodeURIComponent(search)}` : ''; return api.get<PaginatedResponse<JobPosting>>(`/jobs?page=${page}&size=${size}${q}`) },
  get: (id: number) => api.get<JobPosting>(`/jobs/${id}`),
  mine: (page = 1, size = 10) => api.get<PaginatedResponse<JobPosting>>(`/jobs/mine?page=${page}&size=${size}`),
  create: (data: Partial<JobPosting>) => api.post<JobPosting>('/jobs', data),
  update: (id: number, data: Partial<JobPosting>) => api.put<JobPosting>(`/jobs/${id}`, data),
  close: (id: number) => api.delete(`/jobs/${id}`),
  matchMe: (id: number) => api.post<Match>(`/jobs/${id}/match-me`),
  getCandidates: (id: number, page = 1, size = 10) => api.get<PaginatedResponse<Match>>(`/jobs/${id}/candidates?page=${page}&size=${size}`),
  updateMatch: (jobId: number, matchId: number, data: { status: string; recruiter_notes?: string }) => api.put<Match>(`/jobs/${jobId}/matches/${matchId}`, data),
  myMatches: (page = 1, size = 10) => api.get<PaginatedResponse<Match>>(`/jobs/matches/mine?page=${page}&size=${size}`),
}
