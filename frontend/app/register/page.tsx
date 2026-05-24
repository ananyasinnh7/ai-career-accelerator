import { Suspense } from 'react'
import RegisterForm from './RegisterForm'

export default function RegisterPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      <Suspense fallback={<div className="text-slate-400">Loading...</div>}>
        <RegisterForm />
      </Suspense>
    </div>
  )
}