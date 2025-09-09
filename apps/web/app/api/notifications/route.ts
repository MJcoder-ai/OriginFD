import { NextRequest, NextResponse } from 'next/server'
import { addNotification, getNotifications } from '../bridge/shared-data'

export async function GET() {
  return NextResponse.json(getNotifications())
}

export async function POST(request: NextRequest) {
  const body = await request.json()
  const notification = addNotification({
    id: `note_${crypto.randomUUID()}`,
    ...body,
    created_at: new Date().toISOString(),
  })
  return NextResponse.json(notification, { status: 201 })
}
