import type { Metadata } from 'next'
import './globals.css'
import { Toaster } from 'react-hot-toast'

export const metadata: Metadata = {
  title: 'AI Career Accelerator',
  description: 'Two-sided talent matchmaking platform powered by AI',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {children}
        <Toaster 
          position="top-right" 
          toastOptions={{
            style: { 
              background: '#0f0f1a', 
              color: '#e2e8f0', 
              border: '1px solid rgba(99,102,241,0.3)' 
            },
          }} 
        />
      </body>
    </html>
  )
}