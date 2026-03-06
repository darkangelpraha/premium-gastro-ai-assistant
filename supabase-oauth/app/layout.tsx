import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Premium Gastro — Autorizace přístupu',
  description: 'Supabase OAuth Authorization Server',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="cs">
      <body className="min-h-screen bg-gray-50 flex items-center justify-center">
        {children}
      </body>
    </html>
  )
}
