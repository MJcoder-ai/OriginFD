import { NextRequest, NextResponse } from 'next/server'
import { mockDocuments } from '../../../documents/[id]/route'
import { spawn } from 'child_process'
import path from 'path'
import fs from 'fs'

function getPythonPath() {
  let pyPath = path.resolve(process.cwd(), '..', '..', 'packages', 'py')
  if (!fs.existsSync(pyPath)) {
    pyPath = path.resolve(process.cwd(), 'packages', 'py')
  }
  return pyPath
}

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const baseDoc = mockDocuments[params.id]
  if (!baseDoc) {
    return NextResponse.json({ error: 'Document not found' }, { status: 404 })
  }

  // Create a modified version to simulate pending changes
  const targetDoc = JSON.parse(JSON.stringify(baseDoc))
  targetDoc.finance = targetDoc.finance || {}
  const originalCapex = targetDoc.finance.capex || 0
  targetDoc.finance.capex = originalCapex + 10000

  const script = `
import json, sys
from odl_sd_patch import create_patch
from odl_sd_schema.document import OdlDocument
base = json.loads(sys.argv[1])
updated = json.loads(sys.argv[2])
patch_ops = create_patch(base, updated)
sections = {}
for op in patch_ops:
    path = op.get('path', '/').lstrip('/')
    section = path.split('/')[0] if path else 'root'
    sections.setdefault(section, []).append(op)
# KPI deltas using schema
base_doc = OdlDocument.parse_obj(base)
updated_doc = OdlDocument.parse_obj(updated)
deltas = {}
try:
    b_fin = getattr(base_doc, 'finance', None)
    u_fin = getattr(updated_doc, 'finance', None)
    if u_fin and u_fin.capex is not None:
        b_capex = b_fin.capex if b_fin and b_fin.capex is not None else 0
        deltas['capex'] = u_fin.capex - b_capex
    if u_fin and u_fin.opex is not None:
        b_opex = b_fin.opex if b_fin and b_fin.opex is not None else 0
        deltas['opex'] = u_fin.opex - b_opex
except Exception as e:
    deltas = {'error': str(e)}
print(json.dumps({'diff': sections, 'kpi_deltas': deltas}))
`

  const pyPath = getPythonPath()

  return new Promise<NextResponse>((resolve) => {
    const py = spawn(
      'python',
      ['-c', script, JSON.stringify(baseDoc), JSON.stringify(targetDoc)],
      { env: { ...process.env, PYTHONPATH: pyPath } }
    )
    let out = ''
    let err = ''
    py.stdout.on('data', (d) => (out += d.toString()))
    py.stderr.on('data', (d) => (err += d.toString()))
    py.on('close', () => {
      if (err) {
        console.error('Diff error:', err)
        resolve(
          NextResponse.json({ error: 'diff computation failed' }, { status: 500 })
        )
      } else {
        resolve(NextResponse.json(JSON.parse(out)))
      }
    })
  })
}
