import { createSupabaseServerClient } from '@/lib/supabase'
import { redirect } from 'next/navigation'

interface ConsentPageProps {
  searchParams: {
    authorization_id?: string
  }
}

const SCOPE_DESCRIPTIONS: Record<string, string> = {
  openid: 'Ověření identity',
  email: 'E-mailová adresa',
  profile: 'Základní informace o profilu',
  offline_access: 'Přístup i po odhlášení',
  'read:data': 'Čtení vašich dat',
  'write:data': 'Úprava vašich dat',
}

export default async function ConsentPage({ searchParams }: ConsentPageProps) {
  const authorizationId = searchParams.authorization_id

  if (!authorizationId) {
    return (
      <div className="w-full max-w-md text-center">
        <p className="text-red-600 font-medium">Chybí authorization_id</p>
      </div>
    )
  }

  const supabase = createSupabaseServerClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    const currentUrl = `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}/oauth/consent?authorization_id=${authorizationId}`
    const loginUrl = new URL(`${process.env.NEXT_PUBLIC_SUPABASE_URL}/auth/v1/authorize`)
    loginUrl.searchParams.set('provider', 'email')
    loginUrl.searchParams.set('redirect_to', currentUrl)
    redirect(loginUrl.toString())
  }

  // Načti detaily autorizace ze Supabase
  const { data: authDetails, error } = await (supabase.auth as any).oauth.getAuthorizationDetails(authorizationId)

  if (error || !authDetails) {
    return (
      <div className="w-full max-w-md text-center">
        <p className="text-red-600 font-medium">Neplatný nebo expirovaný authorization request</p>
        <p className="text-gray-500 text-sm mt-1">{error?.message}</p>
      </div>
    )
  }

  const clientName = authDetails?.client?.name ?? authDetails?.client_id ?? 'Neznámý klient'
  const scopeString: string = authDetails?.scopes ?? authDetails?.scope ?? ''
  const scopes = scopeString.split(' ').filter(Boolean)

  return (
    <div className="w-full max-w-md">
      {/* Logo + branding */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-emerald-600 rounded-2xl mb-4">
          <span className="text-3xl">🍽️</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Premium Gastro</h1>
        <p className="text-gray-500 text-sm mt-1">Systém pro správu restaurací</p>
      </div>

      {/* Consent card */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-5 border-b border-gray-100">
          <p className="text-gray-600 text-sm">
            Aplikace <span className="font-semibold text-gray-900 font-mono text-xs bg-gray-100 px-2 py-0.5 rounded">{clientName}</span> požaduje přístup k vašemu účtu.
          </p>
          <p className="text-xs text-gray-400 mt-1">Přihlášen jako: {user.email}</p>
        </div>

        {/* Scopes */}
        {scopes.length > 0 && (
          <div className="px-6 py-4 border-b border-gray-100">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Požadovaná oprávnění</p>
            <ul className="space-y-2">
              {scopes.map(scope => (
                <li key={scope} className="flex items-center gap-3">
                  <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0">
                    <svg className="w-3 h-3 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <span className="text-sm text-gray-700">
                    {SCOPE_DESCRIPTIONS[scope] ?? scope}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Actions */}
        <div className="px-6 py-4 bg-gray-50">
          <form className="flex flex-col gap-3">
            <input type="hidden" name="authorization_id" value={authorizationId} />

            <button
              formAction="/api/oauth/approve"
              type="submit"
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-3 px-4 rounded-xl transition-colors"
            >
              Povolit přístup
            </button>
            <button
              formAction="/api/oauth/deny"
              type="submit"
              className="w-full bg-white hover:bg-gray-50 text-gray-700 font-medium py-3 px-4 rounded-xl border border-gray-200 transition-colors"
            >
              Odmítnout
            </button>
          </form>
        </div>
      </div>

      <p className="text-center text-xs text-gray-400 mt-4">
        Povolením přístupu souhlasíte s podmínkami Premium Gastro
      </p>
    </div>
  )
}
