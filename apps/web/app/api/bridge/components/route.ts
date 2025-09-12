import { NextRequest, NextResponse } from 'next/server'

// Comprehensive seed data - Real-world component specifications
function generateComponentDatabase() {
  const components = []
  let idCounter = 1

  // Solar Panels (Generation) - Major manufacturers with real specs
  const solarPanels = [
    { brand: "SunPower", series: "SPR-X22", wattages: [360, 370, 380, 390, 400], efficiency: 0.224 },
    { brand: "LG", series: "LG-NeON-2", wattages: [365, 375, 385, 395, 405], efficiency: 0.217 },
    { brand: "Panasonic", series: "VBHN330", wattages: [330, 340, 350, 360], efficiency: 0.196 },
    { brand: "Canadian Solar", series: "CS3K", wattages: [300, 310, 320, 330, 340], efficiency: 0.188 },
    { brand: "JinkoSolar", series: "JKM", wattages: [400, 410, 420, 430, 440], efficiency: 0.203 },
    { brand: "First Solar", series: "FS-6", wattages: [420, 430, 440, 450, 460], efficiency: 0.186 },
    { brand: "Trina Solar", series: "TSM", wattages: [380, 390, 400, 410, 420], efficiency: 0.198 },
    { brand: "JA Solar", series: "JAM", wattages: [370, 380, 390, 400, 410], efficiency: 0.201 },
  ]

  solarPanels.forEach(panel => {
    panel.wattages.forEach((wattage) => {
      const voltage = 37.2 + (wattage - 360) * 0.05
      const current = wattage / voltage
      const lifecycleStages = ['active', 'mature', 'deprecated'] as const
      const complianceStatuses = ['compliant', 'pending_review'] as const
      
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
        efficiency: panel.efficiency,
        dimensions: {
          width_mm: 1046,
          height_mm: 1690,
          depth_mm: 35 + Math.random() * 10
        },
        weight_kg: 18.0 + Math.random() * 3,
        certification: ["IEC 61215", "IEC 61730", "UL 1703"],
        warranty_years: 25,
        lifecycle_stage: lifecycleStages[Math.floor(Math.random() * lifecycleStages.length)],
        inventory_managed: Math.random() > 0.3,
        compliance_status: complianceStatuses[Math.floor(Math.random() * complianceStatuses.length)],
        warranty_details: {
          coverage_type: 'full',
          warranty_provider: panel.brand,
          start_date: new Date(2024, 0, 1).toISOString(),
          end_date: new Date(2049, 0, 1).toISOString()
        },
        created_at: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString(),
        updated_at: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString()
      })
      idCounter++
    })
  })

  // String Inverters (Conversion) - Central inverters for large installations  
  const inverters = [
    { brand: "SMA", series: "STP", ratings: [15000, 20000, 25000, 30000, 50000] },
    { brand: "Fronius", series: "SYMO", ratings: [12500, 15000, 17000, 20000, 24000] },
    { brand: "SolarEdge", series: "SE", ratings: [7600, 10000, 11400, 12500, 25000] },
    { brand: "ABB", series: "UNO-DM", ratings: [3300, 4200, 5000, 6000] },
    { brand: "Huawei", series: "SUN", ratings: [33000, 36000, 40000, 50000, 60000] },
    { brand: "Power-One", series: "PVI", ratings: [10000, 12500, 15000, 17500, 20000] },
    { brand: "Schneider Electric", series: "XW", ratings: [6800, 8500] },
  ]

  inverters.forEach(inverter => {
    inverter.ratings.forEach(rating => {
      const voltage = rating > 10000 ? 480 : 240
      const efficiency = 0.96 + Math.random() * 0.02
      const lifecycleStages = ['active', 'mature', 'deprecated'] as const
      const complianceStatuses = ['compliant', 'pending_review'] as const
      const warrantyYears = 10 + Math.floor(Math.random() * 5)
      
      components.push({
        id: `comp_${String(idCounter).padStart(3, '0')}`,
        component_id: `${inverter.series}_${rating}W`,
        brand: inverter.brand,
        part_number: `${inverter.series}-${rating}TL-${voltage === 480 ? '30' : '10'}`,
        category: "conversion", 
        status: Math.random() > 0.15 ? "available" : "draft",
        domain: "PV",
        rating_w: rating,
        voltage_v: voltage,
        current_a: parseFloat((rating / voltage).toFixed(1)),
        efficiency: parseFloat(efficiency.toFixed(3)),
        dimensions: {
          width_mm: rating > 20000 ? 665 : 460,
          height_mm: rating > 20000 ? 761 : 610,
          depth_mm: rating > 20000 ? 334 : 254
        },
        weight_kg: rating > 20000 ? 61 : 41,
        certification: ["IEEE 1547", "UL 1741", "IEC 62109"],
        warranty_years: warrantyYears,
        lifecycle_stage: lifecycleStages[Math.floor(Math.random() * lifecycleStages.length)],
        inventory_managed: Math.random() > 0.4,
        compliance_status: complianceStatuses[Math.floor(Math.random() * complianceStatuses.length)],
        warranty_details: {
          coverage_type: Math.random() > 0.5 ? 'full' : 'limited',
          warranty_provider: inverter.brand,
          start_date: new Date(2024, 0, 1).toISOString(),
          end_date: new Date(2024 + warrantyYears, 0, 1).toISOString()
        },
        created_at: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString(),
        updated_at: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString()
      })
      idCounter++
    })
  })

  // Battery Energy Storage (BESS)
  const batteries = [
    { brand: "Tesla", series: "Powerwall", models: [{w: 11500, kwh: 13.5}, {w: 5800, kwh: 13.5}] },
    { brand: "LG Chem", series: "RESU", models: [{w: 5000, kwh: 9.8}, {w: 7000, kwh: 13.1}, {w: 9600, kwh: 16.0}] },
    { brand: "Enphase", series: "Encharge", models: [{w: 1280, kwh: 3.36}, {w: 3840, kwh: 10.08}] },
    { brand: "sonnen", series: "sonnenBatterie", models: [{w: 8000, kwh: 10}, {w: 10000, kwh: 15}, {w: 20000, kwh: 20}] },
    { brand: "BYD", series: "Battery-Box Premium", models: [{w: 2560, kwh: 2.56}, {w: 5120, kwh: 5.12}, {w: 10240, kwh: 10.24}] },
    { brand: "Pylontech", series: "US3000C", models: [{w: 2400, kwh: 3.552}, {w: 4800, kwh: 7.1}, {w: 9600, kwh: 14.2}] },
  ]

  batteries.forEach(battery => {
    battery.models.forEach(model => {
      const voltage = 51.2 + Math.random() * 350
      const lifecycleStages = ['active', 'mature'] as const
      const complianceStatuses = ['compliant', 'pending_review'] as const
      
      components.push({
        id: `comp_${String(idCounter).padStart(3, '0')}`,
        component_id: `${battery.series}_${model.kwh}kWh`,
        brand: battery.brand,
        part_number: `${battery.series}-${model.kwh}`,
        category: "storage",
        status: Math.random() > 0.2 ? "available" : "draft", 
        domain: "BESS",
        rating_w: model.w,
        voltage_v: parseFloat(voltage.toFixed(1)),
        current_a: parseFloat((model.w / voltage).toFixed(1)),
        energy_kwh: model.kwh,
        dimensions: {
          width_mm: model.kwh > 10 ? 1150 : 442,
          height_mm: model.kwh > 10 ? 1924 : 705,
          depth_mm: model.kwh > 10 ? 147 : 307
        },
        weight_kg: model.kwh * 8 + 20,
        certification: ["UL 1973", "UL 9540A", "NFPA 855"],
        warranty_years: 10,
        lifecycle_stage: lifecycleStages[Math.floor(Math.random() * lifecycleStages.length)],
        inventory_managed: Math.random() > 0.5,
        compliance_status: complianceStatuses[Math.floor(Math.random() * complianceStatuses.length)],
        warranty_details: {
          coverage_type: 'full',
          warranty_provider: battery.brand,
          start_date: new Date(2024, 0, 1).toISOString(),
          end_date: new Date(2034, 0, 1).toISOString()
        },
        created_at: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString(),
        updated_at: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString()
      })
      idCounter++
    })
  })

  // Monitoring & Communication
  const monitoring = [
    { brand: "SolarEdge", series: "SE-MTR", ratings: [240, 480] },
    { brand: "Enphase", series: "Envoy-S", ratings: [230] },
    { brand: "SMA", series: "Webbox", ratings: [50] },
    { brand: "Fronius", series: "Smart Card", ratings: [25] },
    { brand: "ABB", series: "VSN300", ratings: [75] },
    { brand: "Huawei", series: "SmartLogger", ratings: [150] },
    { brand: "Tigo", series: "TS4-A-O", ratings: [15] },
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
          width_mm: 90,
          height_mm: 70,
          depth_mm: 65
        },
        weight_kg: 0.5,
        certification: ["FCC Part 15", "UL 2089"],
        warranty_years: 5,
        created_at: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString(),
        updated_at: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString()
      })
      idCounter++
    })
  })

  // Protection Equipment - Surge protectors, fuses, breakers
  const protection = [
    { brand: "ABB", series: "OVR-PV", ratings: [600, 1000, 1500] },
    { brand: "Phoenix Contact", series: "VAL-MS", ratings: [600, 1000] },
    { brand: "DEHN", series: "DG M TNS", ratings: [1000, 1200] },
    { brand: "Littelfuse", series: "SPIKESHIELD", ratings: [600, 1000, 1500] },
    { brand: "Schneider Electric", series: "PRD1", ratings: [1000] },
    { brand: "Eaton", series: "CHSPT2", ratings: [600] },
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
          width_mm: 70,
          height_mm: 90,
          depth_mm: 65
        },
        weight_kg: 0.3,
        certification: ["IEC 61643-31", "UL 1449"],
        warranty_years: 3,
        created_at: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString(),
        updated_at: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString()
      })
      idCounter++
    })
  })

  return components
}

// Generate comprehensive component database
const mockComponents = generateComponentDatabase()

// Calculate stats dynamically
const mockStats = {
  total_components: mockComponents.length,
  active_components: mockComponents.filter(c => c.status === "available").length,
  draft_components: mockComponents.filter(c => c.status === "draft").length,
  categories: {}
}

// Count categories
mockComponents.forEach(component => {
  mockStats.categories[component.category] = (mockStats.categories[component.category] || 0) + 1
})

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    
    // Check if this is a stats request
    if (request.url.includes('/stats')) {
      console.log('Fetching component stats - returning', mockStats.total_components, 'total components')
      return NextResponse.json(mockStats)
    }
    
    // Parse query parameters
    const page = parseInt(searchParams.get('page') || '1', 10)
    const pageSize = parseInt(searchParams.get('page_size') || '20', 10)
    const search = searchParams.get('search')
    const category = searchParams.get('category')
    const domain = searchParams.get('domain') 
    const status = searchParams.get('status')
    
    let filteredComponents = [...mockComponents]
    
    // Apply filters
    if (search) {
      filteredComponents = filteredComponents.filter(comp => 
        comp.brand.toLowerCase().includes(search.toLowerCase()) ||
        comp.part_number.toLowerCase().includes(search.toLowerCase()) ||
        comp.component_id.toLowerCase().includes(search.toLowerCase())
      )
    }
    
    if (category) {
      filteredComponents = filteredComponents.filter(comp => comp.category === category)
    }
    
    if (domain) {
      filteredComponents = filteredComponents.filter(comp => comp.domain === domain)
    }
    
    if (status) {
      filteredComponents = filteredComponents.filter(comp => comp.status === status)
    }
    
    // Pagination
    const start = (page - 1) * pageSize
    const end = start + pageSize
    const paginatedComponents = filteredComponents.slice(start, end)
    
    console.log(`Fetching components list: ${paginatedComponents.length} components (page ${page})`)
    
    return NextResponse.json({
      components: paginatedComponents,
      total: filteredComponents.length,
      page,
      page_size: pageSize,
      total_pages: Math.ceil(filteredComponents.length / pageSize)
    })
    
  } catch (error) {
    console.error('Error fetching components:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Mock component creation
    const newComponent = {
      id: `comp_${Date.now()}`,
      component_id: body.component_id || `AUTO_${Date.now()}`,
      brand: body.brand,
      part_number: body.part_number, 
      category: body.category,
      status: "draft",
      domain: body.domain,
      rating_w: body.rating_w,
      voltage_v: body.voltage_v,
      current_a: body.current_a,
      dimensions: body.dimensions,
      weight_kg: body.weight_kg,
      certification: body.certification || [],
      warranty_years: body.warranty_years || 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
    
    console.log('Created new component:', newComponent.component_id)
    
    return NextResponse.json(newComponent, { status: 201 })
    
  } catch (error) {
    console.error('Error creating component:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}