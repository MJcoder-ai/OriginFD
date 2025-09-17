"use client"
import * as React from 'react'

type Selection = { instanceId?: string }

class Bus {
  private sel: Selection = {}
  private subs = new Set<() => void>()
  select(id?: string) { this.sel = { instanceId: id }; this.subs.forEach(fn => fn()) }
  clear() { this.select(undefined) }
  subscribe(fn: () => void) { this.subs.add(fn); return () => this.subs.delete(fn) }
  snapshot() { return this.sel }
}

const bus = new Bus()
const Ctx = React.createContext(bus)

export function useCanvasBus() { return React.useContext(Ctx) }

export function CanvasBusProvider({ children }: { children: React.ReactNode }) {
  return <Ctx.Provider value={bus}>{children}</Ctx.Provider>
}

export function useSelection() {
  const b = useCanvasBus()
  const subscribe = React.useCallback((fn: () => void) => b.subscribe(fn), [b])
  const get = React.useCallback(() => b.snapshot(), [b])
  return React.useSyncExternalStore(subscribe, get, get)
}