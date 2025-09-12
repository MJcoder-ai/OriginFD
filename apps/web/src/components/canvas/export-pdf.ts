"use client"
import { jsPDF } from 'jspdf'

export async function exportCanvasSVGToPDF(container: HTMLElement, filename = 'canvas.pdf') {
  const svg = container.querySelector('svg') as SVGSVGElement | null
  if (!svg) throw new Error('No <svg> found in canvas container')
  const bbox = svg.getBBox()
  const w = Math.max(800, bbox.width + 40)
  const h = Math.max(600, bbox.height + 40)
  const pdf = new jsPDF({ orientation: w > h ? 'landscape' : 'portrait', unit: 'pt', format: [w, h] })
  // jsPDF v2.5+ supports inline SVG rendering via .svg()
  // @ts-ignore - types may miss svg plugin
  await pdf.svg(svg, { x: 20, y: 20, width: w - 40, height: h - 40 })
  pdf.save(filename)
}