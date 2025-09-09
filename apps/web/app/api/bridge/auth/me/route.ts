import { NextResponse } from 'next/server'

export async function GET() {
  return NextResponse.json({
    id: 'user-1',
    email: 'demo@originfd.com',
    full_name: 'Demo User',
    role: 'admin',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: new Date().toISOString(),
  })
}