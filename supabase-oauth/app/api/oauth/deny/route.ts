import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServerClient } from '@/lib/supabase'

export async function POST(request: NextRequest) {
  const supabase = createSupabaseServerClient()

  const formData = await request.formData()
  const authorizationId = formData.get('authorization_id') as string

  if (!authorizationId) {
    return NextResponse.json({ error: 'Missing authorization_id' }, { status: 400 })
  }

  const { data, error } = await (supabase.auth as any).oauth.denyAuthorization(authorizationId)

  if (error || !data?.redirect_to) {
    return NextResponse.json(
      { error: error?.message ?? 'Failed to deny authorization' },
      { status: 500 }
    )
  }

  return NextResponse.redirect(data.redirect_to)
}
