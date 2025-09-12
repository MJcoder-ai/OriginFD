"use client"
import * as React from 'react'
import { Button } from '@originfd/ui'

export type LayerKey = 'ac' | 'dc' | 'routes' | 'equipment' | 'civil'

export function LayersPanel({
  active,
  onChange,
}: { active: LayerKey[]; onChange: (layers: LayerKey[]) => void }) {
  const toggle = (k: LayerKey) => {
    onChange(active.includes(k) ? active.filter(x => x !== k) : [...active, k])
  }
  const Chip = ({ k, label }: { k: LayerKey; label: string }) => (
    <Button 
      size="sm" 
      variant={active.includes(k) ? 'default' : 'outline'} 
      onClick={() => toggle(k)} 
      className="h-6 px-2 text-xs"
    >
      {label}
    </Button>
  )
  return (
    <div className="flex flex-wrap gap-2">
      <Chip k="ac" label="AC" />
      <Chip k="dc" label="DC" />
      <Chip k="routes" label="Routes" />
      <Chip k="equipment" label="Equipment" />
      <Chip k="civil" label="Civil" />
    </div>
  )
}

export default LayersPanel