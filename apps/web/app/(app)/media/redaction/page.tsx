'use client'

import RedactionOverlay from '@/components/media/redaction-overlay'

export default function RedactionPage() {
  const sample = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PvXHiwAAAABJRU5ErkJggg=='
  return (
    <div className="p-4 flex justify-center">
      <RedactionOverlay src={sample} type="image" docType="sld" />
    </div>
  )
}
