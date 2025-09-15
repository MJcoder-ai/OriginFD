import { NextRequest, NextResponse } from 'next/server'

// Mock user data for authentication
const MOCK_USER = {
  id: 'user-1',
  email: 'admin@originfd.com',
  full_name: 'System Administrator',
  is_active: true,
  roles: ['admin', 'user'],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: new Date().toISOString(),
}

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization')

    // Check for valid token (mock validation)
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    const token = authHeader.replace('Bearer ', '')

    // Mock token validation - accept any mock token
    if (!token.startsWith('mock-access-token-')) {
      return NextResponse.json(
        { detail: 'Invalid token' },
        { status: 401 }
      )
    }

    console.log('User info requested for token:', token.substring(0, 20) + '...')

    return NextResponse.json(MOCK_USER)
  } catch (error) {
    console.error('Get user error:', error)
    return NextResponse.json(
      { detail: 'Failed to get user info' },
      { status: 500 }
    )
  }
}