import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    console.log('Logout requested')
    
    // For mock implementation, just return success
    return NextResponse.json({ message: 'Logged out successfully' })
  } catch (error) {
    console.error('Logout error:', error)
    return NextResponse.json(
      { detail: 'Logout failed' },
      { status: 500 }
    )
  }
}