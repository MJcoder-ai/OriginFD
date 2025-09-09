'use client'

import * as React from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardHeader, CardTitle, CardContent, Button } from '@originfd/ui'

interface AlarmTrend {
  id: string
  name: string
  values: number[]
}

/**
 * AlarmPanel renders live alarm trend cards using a WebSocket stream.
 * Each card includes a one-click action to create a work order.
 */
export default function AlarmPanel() {
  const [alarms, setAlarms] = React.useState<AlarmTrend[]>([])
  const router = useRouter()
  const wsRef = React.useRef<WebSocket | null>(null)

  React.useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/alarms/ws')
    wsRef.current = ws

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as { id: string; value: number }
      setAlarms((prev) => {
        const existing = prev.find((a) => a.id === data.id)
        if (existing) {
          const updatedValues = [...existing.values, data.value].slice(-20)
          return prev.map((a) =>
            a.id === data.id ? { ...a, values: updatedValues } : a
          )
        }
        return [...prev, { id: data.id, name: data.id, values: [data.value] }]
      })
    }

    return () => {
      ws.close()
    }
  }, [])

  const createWorkOrder = async (alarmId: string) => {
    try {
      await fetch('/api/bridge/work-orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alarm_id: alarmId }),
      })
      router.push('/missions')
    } catch (error) {
      console.error('Failed to create work order', error)
    }
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {alarms.map((alarm) => (
        <Card key={alarm.id}>
          <CardHeader>
            <CardTitle>Alarm {alarm.name}</CardTitle>
          </CardHeader>
          <CardContent>
            <svg viewBox="0 0 100 20" className="w-full h-8 text-primary">
              <polyline
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                points={alarm.values
                  .map((v, i) => `${(i / Math.max(alarm.values.length - 1, 1)) * 100},${
                    20 - v * 20
                  }`)
                  .join(' ')}
              />
            </svg>
            <Button
              className="mt-2 w-full"
              size="sm"
              onClick={() => createWorkOrder(alarm.id)}
            >
              Create Work Order
            </Button>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
