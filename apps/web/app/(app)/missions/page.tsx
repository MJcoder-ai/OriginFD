'use client'

import React from 'react'

type Task = {
  id: number
  title: string
  completed: boolean
  qr?: string
  photo?: string
  reading?: string
}

const DB_NAME = 'missions-db'
const STORE_NAME = 'tasks'

async function getDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1)
    req.onupgradeneeded = () => {
      req.result.createObjectStore(STORE_NAME, { keyPath: 'id' })
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

async function loadTasks(): Promise<Task[]> {
  const db = await getDB()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly')
    const store = tx.objectStore(STORE_NAME)
    const req = store.getAll()
    req.onsuccess = () => resolve((req.result as Task[]) || [])
    req.onerror = () => reject(req.error)
  })
}

async function saveTask(task: Task): Promise<void> {
  const db = await getDB()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite')
    tx.objectStore(STORE_NAME).put(task)
    tx.oncomplete = () => resolve()
    tx.onerror = () => reject(tx.error)
  })
}

export default function MissionsPage() {
  const [tasks, setTasks] = React.useState<Task[]>([])
  const [newTask, setNewTask] = React.useState('')
  const [currentTask, setCurrentTask] = React.useState<Task | null>(null)
  const [step, setStep] = React.useState(0)
  const [scan, setScan] = React.useState('')
  const [photo, setPhoto] = React.useState<string | null>(null)
  const [reading, setReading] = React.useState('')
  const videoRef = React.useRef<HTMLVideoElement | null>(null)

  React.useEffect(() => {
    loadTasks().then((t) => setTasks(t))
  }, [])

  React.useEffect(() => {
    let stream: MediaStream | null = null
    let raf: number
    if (step === 0 && currentTask && 'BarcodeDetector' in window) {
      const detector = new (window as any).BarcodeDetector({ formats: ['qr_code'] })
      navigator.mediaDevices
        .getUserMedia({ video: { facingMode: 'environment' } })
        .then((s) => {
          stream = s
          if (videoRef.current) {
            videoRef.current.srcObject = s
            videoRef.current.play()
          }
          const detect = () => {
            if (!videoRef.current) return
            detector
              .detect(videoRef.current)
              .then((codes: any) => {
                if (codes.length > 0) {
                  setScan(codes[0].rawValue)
                  stream?.getTracks().forEach((t) => t.stop())
                } else {
                  raf = requestAnimationFrame(detect)
                }
              })
              .catch(() => {
                raf = requestAnimationFrame(detect)
              })
          }
          raf = requestAnimationFrame(detect)
        })
    }
    return () => {
      if (stream) stream.getTracks().forEach((t) => t.stop())
      if (raf) cancelAnimationFrame(raf)
    }
  }, [step, currentTask])

  async function addTask() {
    if (!newTask.trim()) return
    const task: Task = { id: Date.now(), title: newTask, completed: false }
    await saveTask(task)
    setTasks((prev) => [...prev, task])
    setNewTask('')
  }

  function startTask(task: Task) {
    setCurrentTask(task)
    setStep(0)
    setScan('')
    setPhoto(null)
    setReading('')
  }

  function handlePhoto(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => setPhoto(reader.result as string)
    reader.readAsDataURL(file)
  }

  async function finishTask() {
    if (!currentTask) return
    const updated: Task = {
      ...currentTask,
      qr: scan,
      photo: photo || undefined,
      reading,
      completed: true,
    }
    await saveTask(updated)
    setTasks((prev) => prev.map((t) => (t.id === updated.id ? updated : t)))
    setCurrentTask(null)
  }

  if (!currentTask) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Missions</h1>
        <div className="flex gap-2">
          <input
            value={newTask}
            onChange={(e) => setNewTask(e.target.value)}
            placeholder="New task"
            className="border p-2 flex-1"
          />
          <button className="px-4 py-2 bg-primary text-primary-foreground rounded" onClick={addTask}>
            Add
          </button>
        </div>
        <ul className="space-y-2">
          {tasks.map((task) => (
            <li key={task.id} className="flex justify-between items-center border p-2">
              <span>
                {task.title} {task.completed && '(done)'}
              </span>
              {!task.completed && (
                <button
                  className="px-2 py-1 bg-secondary text-secondary-foreground rounded"
                  onClick={() => startTask(task)}
                >
                  Start
                </button>
              )}
            </li>
          ))}
        </ul>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">{currentTask.title}</h1>
      {step === 0 && (
        <div className="space-y-2">
          {'BarcodeDetector' in window ? (
            <video ref={videoRef} className="w-full h-64 border" />
          ) : (
            <input
              value={scan}
              onChange={(e) => setScan(e.target.value)}
              placeholder="Enter QR code"
              className="border p-2 w-full"
            />
          )}
          {scan && <p>QR: {scan}</p>}
          <button
            className="px-4 py-2 bg-primary text-primary-foreground rounded"
            onClick={() => setStep(1)}
            disabled={!scan}
          >
            Next
          </button>
        </div>
      )}
      {step === 1 && (
        <div className="space-y-2">
          <input type="file" accept="image/*" capture="environment" onChange={handlePhoto} />
          {photo && <img src={photo} alt="preview" className="w-48" />}
          <button
            className="px-4 py-2 bg-primary text-primary-foreground rounded"
            onClick={() => setStep(2)}
            disabled={!photo}
          >
            Next
          </button>
        </div>
      )}
      {step === 2 && (
        <div className="space-y-2">
          <input
            value={reading}
            onChange={(e) => setReading(e.target.value)}
            placeholder="Enter reading"
            className="border p-2 w-full"
          />
          <button
            className="px-4 py-2 bg-primary text-primary-foreground rounded"
            onClick={() => setStep(3)}
            disabled={!reading}
          >
            Next
          </button>
        </div>
      )}
      {step === 3 && (
        <div className="space-y-2">
          <button
            className="px-4 py-2 bg-primary text-primary-foreground rounded"
            onClick={finishTask}
          >
            Finish
          </button>
        </div>
      )}
    </div>
  )
}

