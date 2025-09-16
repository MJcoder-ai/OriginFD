import { NextRequest, NextResponse } from 'next/server'

export async function GET(_req: NextRequest, { params }: { params: { id: string } }) {
  const { id } = params
  // List available canvases for this project
  return NextResponse.json([
    { id: 'sld-mv', name: 'SLD (MV)', type: 'sld' },
    { id: 'sld-dc', name: 'SLD (DC Strings)', type: 'sld' },
    { id: 'site-layout', name: 'Site Layout', type: 'site' },
  ])
}