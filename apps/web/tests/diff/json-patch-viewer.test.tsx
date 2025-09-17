import { strict as assert } from 'node:assert'
import test from 'node:test'
import { groupDiffsBySection, PatchOperation } from '../../src/components/diff/utils'

test('groups patch operations by top-level section', () => {
  const patch: PatchOperation[] = [
    { op: 'replace', path: '/meta/title', value: 'New' },
    { op: 'add', path: '/details/age', value: 42 },
    { op: 'replace', path: '/meta/author', value: 'Jane' },
  ]

  const grouped = groupDiffsBySection(patch)
  assert.deepEqual(Object.keys(grouped).sort(), ['details', 'meta'])
  assert.equal(grouped.meta.length, 2)
  assert.equal(grouped.details[0].path, '/details/age')
})
