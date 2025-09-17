import { NextRequest, NextResponse } from 'next/server'
import path from 'path'
import { promises as fs } from 'fs'

export async function GET(
  request: NextRequest,
  { params }: { params: { runId: string } }
) {
  const filePath = path.join(process.cwd(), 'services', 'orchestrator', 'planner', 'mock_trace.json')
  const raw = await fs.readFile(filePath, 'utf-8')
  const data = JSON.parse(raw)
  return NextResponse.json(data)
}
