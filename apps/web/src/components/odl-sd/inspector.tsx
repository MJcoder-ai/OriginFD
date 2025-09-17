'use client'

import * as React from 'react'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@originfd/ui'
import { InspectorContext } from '../ai/ai-copilot'

export function Inspector() {
  const { focusId } = React.useContext(InspectorContext)
  const [activeTab, setActiveTab] = React.useState('details')
  const [validation, setValidation] = React.useState<any | null>(null)
  const [bom, setBom] = React.useState<any | null>(null)

  React.useEffect(() => {
    if (!focusId) {
      setValidation(null)
      setBom(null)
      return
    }
    async function load() {
      try {
        const [vRes, bRes] = await Promise.all([
          fetch(`/api/validation?id=${focusId}`),
          fetch(`/api/bom?id=${focusId}`)
        ])
        if (vRes.ok) setValidation(await vRes.json())
        if (bRes.ok) setBom(await bRes.json())
      } catch (e) {
        console.error('Failed to load inspector data', e)
      }
    }
    load()
  }, [focusId])

  return (
    <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
      <TabsList className="mb-2">
        <TabsTrigger value="details">Details</TabsTrigger>
        <TabsTrigger value="connections">Connections</TabsTrigger>
        <TabsTrigger value="validation">Validation</TabsTrigger>
        <TabsTrigger value="bom">BOM</TabsTrigger>
      </TabsList>
      <TabsContent value="details">
        {focusId ? (
          <pre className="text-xs overflow-x-auto">{focusId}</pre>
        ) : (
          <p>No selection</p>
        )}
      </TabsContent>
      <TabsContent value="connections">
        {focusId ? <p>Connections for {focusId}</p> : <p>No selection</p>}
      </TabsContent>
      <TabsContent value="validation">
        {validation ? (
          <pre className="text-xs overflow-x-auto">{JSON.stringify(validation, null, 2)}</pre>
        ) : (
          <p>No data</p>
        )}
      </TabsContent>
      <TabsContent value="bom">
        {bom ? (
          <pre className="text-xs overflow-x-auto">{JSON.stringify(bom, null, 2)}</pre>
        ) : (
          <p>No data</p>
        )}
      </TabsContent>
    </Tabs>
  )
}
