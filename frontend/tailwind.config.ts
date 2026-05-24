import type { Config } from 'tailwindcss'
const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['DM Sans', 'sans-serif'],
        display: ['Syne', 'sans-serif'],
      },
      colors: {
        brand: {
          purple: '#a78bfa',
          blue: '#38bdf8',
          dark: '#0a0a0f',
          card: '#0f0f1a',
          border: 'rgba(99,102,241,0.2)',
        },
      },
    },
  },plugins: [],
}
export default config
