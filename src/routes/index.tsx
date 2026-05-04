import { createFileRoute, redirect, useNavigate } from '@tanstack/react-router'
import { supabase } from '../lib/supabase'

export const Route = createFileRoute('/')({
  beforeLoad: async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) throw redirect({ to: '/login' })
    } catch (e: unknown) {
      if (e && typeof e === 'object' && 'to' in e) throw e
      throw redirect({ to: '/login' })
    }
  },
  component: Index,
})

function Index() {
  const navigate = useNavigate()

  const handleLogout = async () => {
    await supabase.auth.signOut()
    navigate({ to: '/login' })
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard Ativuz</h1>
        <p className="text-sm text-gray-500 mt-2">Bem-vindo ao painel de gestão.</p>
        <button
          onClick={handleLogout}
          className="mt-6 px-4 py-2 rounded-md bg-orange-500 hover:bg-orange-600 text-white text-sm font-medium transition"
        >
          Sair
        </button>
      </div>
    </div>
  )
}
