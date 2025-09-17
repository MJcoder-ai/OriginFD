export interface PatchOperation {
  op: 'add' | 'remove' | 'replace'
  path: string
  value?: any
}

function isObject(value: any): value is Record<string, any> {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

export function computeJsonPatch(
  source: any,
  target: any,
  basePath = ''
): PatchOperation[] {
  const patch: PatchOperation[] = []
  const keys = new Set([
    ...Object.keys(source || {}),
    ...Object.keys(target || {}),
  ])

  for (const key of keys) {
    const src = source ? source[key] : undefined
    const tgt = target ? target[key] : undefined
    const path = `${basePath}/${key}`

    if (src === undefined && tgt !== undefined) {
      patch.push({ op: 'add', path, value: tgt })
    } else if (src !== undefined && tgt === undefined) {
      patch.push({ op: 'remove', path })
    } else if (isObject(src) && isObject(tgt)) {
      patch.push(...computeJsonPatch(src, tgt, path))
    } else if (src !== tgt) {
      patch.push({ op: 'replace', path, value: tgt })
    }
  }

  return patch
}

export function getValueByPath(obj: any, path: string): any {
  return path
    .split('/')
    .slice(1)
    .reduce((acc: any, key: string) => (acc ? acc[key] : undefined), obj)
}

export function groupDiffsBySection(
  patch: PatchOperation[]
): Record<string, PatchOperation[]> {
  return patch.reduce((acc, op) => {
    const [, section] = op.path.split('/')
    if (!section) return acc
    acc[section] = acc[section] || []
    acc[section].push(op)
    return acc
  }, {} as Record<string, PatchOperation[]>)
}
