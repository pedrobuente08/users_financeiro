'use client'

import { useEffect } from 'react'
import { supabase } from '@/lib/supabase'

export default function DashboardRedirect() {

  useEffect(() => {
    const goToStreamlit = async () => {

      const { data, error } = await supabase.auth.getSession()

      if (error || !data.session) {
        window.location.href = '/'
        return
      }

      const token = data.session.access_token
      window.location.href = `http://rcoosc44s8ww0kos8goc448w.76.13.228.213.sslip.io/?token=${token}`
    }

    goToStreamlit()
  }, [])

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-indigo-600 mb-4 animate-pulse">
          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <p className="text-slate-300 text-sm">Carregando dashboard...</p>
      </div>
    </div>
  )
}
