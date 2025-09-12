import { writeFileSync } from 'fs'
import { join } from 'path'

// Component data generator
function generateComponents() {
  const components = []
  let idCounter = 1

  // Solar Panels (Generation)
  const solarPanels = [
    { brand: "SunPower", series: "SPR-X22", wattages: [360, 370, 380, 390, 400] },
    { brand: "LG", series: "LG-NeON", wattages: [365, 375, 385, 395, 405] },
    { brand: "Panasonic", series: "VBHN", wattages: [330, 340, 350, 360] },
    { brand: "Canadian Solar", series: "CS3K", wattages: [300, 310, 320, 330, 340] },
    { brand: "JinkoSolar", series: "JKM", wattages: [400, 410, 420, 430, 440] },
    { brand: "First Solar", series: "FS-6", wattages: [420, 430, 440, 450, 460] },
    { brand: "Trina Solar", series: "TSM", wattages: [380, 390, 400, 410, 420] },
    { brand: "JA Solar", series: "JAM", wattages: [370, 380, 390, 400, 410] },
  ]

  solarPanels.forEach(panel => {
    panel.wattages.forEach((wattage, index) => {
      const voltage = 35 + (wattage - 300) * 0.02 + Math.random() * 5
      const current = wattage / voltage
      components.push({
        id: `comp_${String(idCounter).padStart(3, '0')}`,
        component_id: `${panel.series}_${wattage}W`,
        brand: panel.brand,
        part_number: `${panel.series}-${wattage}`,
        category: "generation",
        status: Math.random() > 0.1 ? "available" : "draft",
        domain: "PV",
        rating_w: wattage,
        voltage_v: parseFloat(voltage.toFixed(1)),
        current_a: parseFloat(current.toFixed(2)),
        efficiency: 0.20 + Math.random() * 0.05,
        dimensions: {
          width_mm: 1000 + Math.random() * 200,
          height_mm: 1600 + Math.random() * 200,
          depth_mm: 35 + Math.random() * 15
        },
        weight_kg: 18 + Math.random() * 8,
        certification: ["IEC 61215", "IEC 61730", "UL 1703"],
        warranty_years: 20 + Math.floor(Math.random() * 6),
        created_at: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString(),
        updated_at: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString()
      })
      idCounter++
    })
  })

  // Inverters (Conversion)
  const inverters = [
    { brand: "SMA", series: "STP", ratings: [15000, 20000, 25000, 30000] },
    { brand: "Fronius", series: "SYMO", ratings: [12000, 15000, 17000, 20000] },
    { brand: "SolarEdge", series: "SE", ratings: [7600, 10000, 11400, 12500] },
    { brand: "ABB", series: "UNO-DM", ratings: [3300, 4200, 5000, 6000] },
    { brand: "Huawei", series: "SUN", ratings: [33000, 36000, 40000, 50000] },
    { brand: "Enphase", series: "IQ", ratings: [290, 320, 350, 380] },
    { brand: "Power-One", series: "PVI", ratings: [10000, 12500, 15000, 17500] },
  ]

  inverters.forEach(inverter => {
    inverter.ratings.forEach(rating => {
      const voltage = rating > 10000 ? 480 : 240
      components.push({
        id: `comp_${String(idCounter).padStart(3, '0')}`,
        component_id: `${inverter.series}_${rating}W`,
        brand: inverter.brand,
        part_number: `${inverter.series}-${rating}TL`,
        category: "conversion", 
        status: Math.random() > 0.15 ? "available" : "draft",
        domain: "PV",
        rating_w: rating,
        voltage_v: voltage,
        current_a: parseFloat((rating / voltage).toFixed(1)),
        efficiency: 0.95 + Math.random() * 0.04,
        dimensions: {
          width_mm: 400 + Math.random() * 400,
          height_mm: 600 + Math.random() * 300,
          depth_mm: 200 + Math.random() * 200
        },
        weight_kg: 25 + Math.random() * 40,
        certification: ["IEEE 1547", "UL 1741", "IEC 62109"],
        warranty_years: 5 + Math.floor(Math.random() * 10),
        created_at: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString(),
        updated_at: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString()
      })
      idCounter++
    })
  })

  // Batteries (Storage)
  const batteries = [
    { brand: "Tesla", series: "Powerwall", ratings: [11500, 13500] },
    { brand: "LG Chem", series: "RESU", ratings: [9800, 13100, 16000] },
    { brand: "Enphase", series: "Encharge", ratings: [3360, 10080] },
    { brand: "Sonnen", series: "sonnenBatterie", ratings: [5000, 10000, 15000, 20000] },
    { brand: "BYD", series: "Battery-Box", ratings: [2560, 5120, 7680, 10240] },
    { brand: "Pylontech", series: "US", ratings: [2400, 4800, 7200, 9600] },
    { brand: "SimpliPhi", series: "PHI", ratings: [3400, 6800, 10200] },
  ]

  batteries.forEach(battery => {
    battery.ratings.forEach(rating => {
      const voltage = 48 + Math.random() * 400
      const energyKwh = rating * 0.9 / 1000 + Math.random() * 5
      components.push({
        id: `comp_${String(idCounter).padStart(3, '0')}`,
        component_id: `${battery.series}_${rating}W`,
        brand: battery.brand,
        part_number: `${battery.series}-${Math.floor(rating/1000)}`,
        category: "storage",
        status: Math.random() > 0.2 ? "available" : "draft", 
        domain: "BESS",
        rating_w: rating,
        voltage_v: parseFloat(voltage.toFixed(1)),
        current_a: parseFloat((rating / voltage).toFixed(1)),
        energy_kwh: parseFloat(energyKwh.toFixed(1)),
        dimensions: {
          width_mm: 600 + Math.random() * 600,
          height_mm: 800 + Math.random() * 1200,
          depth_mm: 150 + Math.random() * 200
        },
        weight_kg: 50 + Math.random() * 100,
        certification: ["UL 1973", "UL 9540A", "NFPA 855"],
        warranty_years: 8 + Math.floor(Math.random() * 5),
        created_at: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString(),
        updated_at: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString()
      })
      idCounter++
    })
  })

  // Monitoring Systems
  const monitoring = [
    { brand: "SolarEdge", series: "SE-MTR", ratings: [240, 480] },
    { brand: "Enphase", series: "Envoy", ratings: [100, 200] },
    { brand: "SMA", series: "Webbox", ratings: [50] },
    { brand: "Fronius", series: "Smart Card", ratings: [25] },
    { brand: "ABB", series: "VSN300", ratings: [75] },
    { brand: "Huawei", series: "SmartLogger", ratings: [150] },
  ]

  monitoring.forEach(monitor => {
    monitor.ratings.forEach(rating => {
      components.push({
        id: `comp_${String(idCounter).padStart(3, '0')}`,
        component_id: `${monitor.series}_${rating}W`,
        brand: monitor.brand,
        part_number: `${monitor.series}-${rating}-0`,
        category: "monitoring",
        status: "available",
        domain: "PV",
        rating_w: rating,
        voltage_v: 240,
        current_a: parseFloat((rating / 240).toFixed(2)),
        dimensions: {
          width_mm: 80 + Math.random() * 50,
          height_mm: 60 + Math.random() * 40,
          depth_mm: 50 + Math.random() * 30
        },
        weight_kg: 0.3 + Math.random() * 0.7,
        certification: ["FCC Part 15", "UL 2089"],
        warranty_years: 3 + Math.floor(Math.random() * 5),
        created_at: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString(),
        updated_at: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString()
      })
      idCounter++
    })
  })

  // Protection Equipment
  const protection = [
    { brand: "ABB", series: "OVR-PV", ratings: [1000, 1500] },
    { brand: "Phoenix Contact", series: "VAL-MS", ratings: [600, 1000] },
    { brand: "DEHN", series: "DG M", ratings: [1000, 1200] },
    { brand: "Littelfuse", series: "SPIK", ratings: [600, 1000, 1500] },
    { brand: "Schneider Electric", series: "PRD", ratings: [1000] },
  ]

  protection.forEach(protector => {
    protector.ratings.forEach(rating => {
      components.push({
        id: `comp_${String(idCounter).padStart(3, '0')}`,
        component_id: `${protector.series}_${rating}V`,
        brand: protector.brand,
        part_number: `${protector.series}-40-${rating}-P`,
        category: "protection",
        status: "available", 
        domain: "PV",
        rating_w: rating,
        voltage_v: rating,
        current_a: 40,
        dimensions: {
          width_mm: 60 + Math.random() * 20,
          height_mm: 80 + Math.random() * 20,
          depth_mm: 55 + Math.random() * 20
        },
        weight_kg: 0.2 + Math.random() * 0.3,
        certification: ["IEC 61643-31", "UL 1449"],
        warranty_years: 2 + Math.floor(Math.random() * 3),
        created_at: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString(),
        updated_at: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString()
      })
      idCounter++
    })
  })

  return components
}

// Generate all components
const allComponents = generateComponents()

// Calculate stats
const stats = {
  total_components: allComponents.length,
  active_components: allComponents.filter(c => c.status === "available").length,
  draft_components: allComponents.filter(c => c.status === "draft").length,
  categories: {}
}

// Count categories
allComponents.forEach(component => {
  stats.categories[component.category] = (stats.categories[component.category] || 0) + 1
})

console.log(`Generated ${allComponents.length} components:`)
console.log(`- ${stats.active_components} available`)
console.log(`- ${stats.draft_components} draft`)
console.log('Categories:', stats.categories)

// Export data for use in API
export const componentSeedData = {
  components: allComponents,
  stats
}

// Write to files for inspection
writeFileSync(
  join(process.cwd(), 'components-seed.json'),
  JSON.stringify({ components: allComponents, stats }, null, 2)
)

console.log('✅ Component seed data generated and saved to components-seed.json')