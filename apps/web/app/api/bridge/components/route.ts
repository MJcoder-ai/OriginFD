import { NextRequest, NextResponse } from 'next/server'

// Generic component seed data aligned with ODL-SD v4.1 Component Management Supplement
function generateODLCompliantComponents() {
  const components = []
  let idCounter = 1

  // PV Module Components (Generation)
  const pvModules = [
    { brand: "Generic", series: "PV", wattages: [300, 350, 400, 450, 500], classification: { unspsc: "26111704" } },
    { brand: "SolarTech", series: "ST", wattages: [320, 380, 420, 460], classification: { unspsc: "26111704" } },
    { brand: "PowerPanel", series: "PP", wattages: [310, 360, 410], classification: { unspsc: "26111704" } }
  ]

  pvModules.forEach(module => {
    module.wattages.forEach((wattage) => {
      const componentId = `CMP:${module.brand.toUpperCase()}:${module.series}-${wattage}:${wattage}W:V1.0`
      const name = `${module.brand}_${module.series}-${wattage}_${wattage}W`
      
      components.push({
        id: `comp_${String(idCounter).padStart(3, '0')}`,
        component_management: {
          version: "1.0",
          status: Math.random() > 0.7 ? "draft" : "available",
          component_identity: {
            component_id: componentId,
            brand: module.brand,
            part_number: `${module.series}-${wattage}`,
            rating_w: wattage,
            name: name,
            classification: {
              unspsc: module.classification.unspsc,
              eclass: "27-01-02-01",
              hs_code: "854140"
            }
          },
          source_documents: {
            datasheet: {
              type: "datasheet",
              url: `https://docs.example.com/${componentId.replace(/:/g, '_')}.pdf`,
              hash: `sha256:${Math.random().toString(36).substring(2, 66)}`,
              parsed_at: new Date().toISOString()
            },
            additional: []
          },
          tracking_policy: {
            level: "serial",
            auto_rules: {
              regulatory_serial_required: true,
              warranty_sn_required: true,
              safety_critical: false
            }
          },
          supplier_chain: {
            suppliers: [
              {
                supplier_id: `SUP_${module.brand.toUpperCase()}_001`,
                name: `${module.brand} Manufacturing`,
                gln: "1234567890123",
                status: "approved",
                contact: {
                  email: `sales@${module.brand.toLowerCase()}.com`,
                  phone: "+1-555-0100"
                }
              }
            ]
          },
          order_management: {
            rfq_enabled: true,
            orders: [],
            shipments: []
          },
          inventory: {
            stocks: [
              {
                location: { name: "Main Warehouse", gln: "1234567890456" },
                status: "in_stock",
                uom: "pcs",
                on_hand_qty: Math.floor(Math.random() * 100) + 10,
                lots: [],
                serials: []
              }
            ]
          },
          warranty: {
            terms: {
              type: "product",
              duration_years: 25,
              coverage_min_pct: 80
            },
            claims: []
          },
          returns: {
            policies: {
              return_window_days: 30,
              restocking_fee_pct: 15,
              return_rate_pct: 2
            },
            records: []
          },
          traceability: {
            dpp: {
              enabled: true,
              uri: `https://dpp.example.com/${componentId}`,
              mandatory_fields: ["manufacturer", "model", "capacity_rating", "hazardous_substances"]
            },
            serialization: {
              format: "^PV[0-9]{10}$",
              generation_rule: "sequential"
            }
          },
          compliance: {
            certificates: [
              {
                standard: "IEC 61215",
                number: `IEC-${idCounter}-2024`,
                issuer: "TUV Rheinland",
                valid_until: "2029-12-31",
                scope: "Design qualification and type approval"
              },
              {
                standard: "IEC 61730",
                number: `IEC-${idCounter}-2024-S`,
                issuer: "TUV Rheinland", 
                valid_until: "2029-12-31",
                scope: "Safety qualification"
              }
            ],
            sustainability: {
              embodied_co2e_kg: wattage * 0.5, // Approximate embodied carbon
              recyclable_pct: 85,
              hazardous_substances: []
            }
          },
          ai_logs: {
            classification_confidence: Math.random() * 0.3 + 0.7,
            last_enrichment: new Date().toISOString(),
            auto_actions: []
          },
          audit: {
            created_by: "system",
            created_at: new Date().toISOString(),
            updated_by: "system", 
            updated_at: new Date().toISOString(),
            version: 1
          },
          analytics: {
            procurement_stats: {
              avg_lead_time_days: 14 + Math.floor(Math.random() * 21),
              price_trend_3m: Math.random() > 0.5 ? "stable" : "declining",
              quality_score_pct: 85 + Math.floor(Math.random() * 15)
            }
          }
        }
      })
      idCounter++
    })
  })

  // String Inverters (Conversion)
  const inverters = [
    { brand: "InverTech", series: "IT", ratings: [10000, 15000, 20000, 25000], classification: { unspsc: "26111705" } },
    { brand: "PowerConv", series: "PC", ratings: [12000, 18000, 24000], classification: { unspsc: "26111705" } }
  ]

  inverters.forEach(inverter => {
    inverter.ratings.forEach(rating => {
      const componentId = `CMP:${inverter.brand.toUpperCase()}:${inverter.series}-${rating}:${rating}W:V1.0`
      const name = `${inverter.brand}_${inverter.series}-${rating}_${rating}W`
      
      components.push({
        id: `comp_${String(idCounter).padStart(3, '0')}`,
        component_management: {
          version: "1.0",
          status: Math.random() > 0.8 ? "draft" : "available",
          component_identity: {
            component_id: componentId,
            brand: inverter.brand,
            part_number: `${inverter.series}-${rating}`,
            rating_w: rating,
            name: name,
            classification: {
              unspsc: inverter.classification.unspsc,
              eclass: "27-02-01-01",
              hs_code: "850440"
            }
          },
          source_documents: {
            datasheet: {
              type: "datasheet",
              url: `https://docs.example.com/${componentId.replace(/:/g, '_')}.pdf`,
              hash: `sha256:${Math.random().toString(36).substring(2, 66)}`,
              parsed_at: new Date().toISOString()
            },
            additional: []
          },
          tracking_policy: {
            level: "serial",
            auto_rules: {
              regulatory_serial_required: true,
              warranty_sn_required: true,
              safety_critical: true
            }
          },
          supplier_chain: {
            suppliers: [
              {
                supplier_id: `SUP_${inverter.brand.toUpperCase()}_001`,
                name: `${inverter.brand} Electronics`,
                gln: "1234567890789",
                status: "approved",
                contact: {
                  email: `sales@${inverter.brand.toLowerCase()}.com`,
                  phone: "+1-555-0200"
                }
              }
            ]
          },
          order_management: {
            rfq_enabled: true,
            orders: [],
            shipments: []
          },
          inventory: {
            stocks: [
              {
                location: { name: "Main Warehouse", gln: "1234567890456" },
                status: "in_stock",
                uom: "pcs",
                on_hand_qty: Math.floor(Math.random() * 50) + 5,
                lots: [],
                serials: []
              }
            ]
          },
          warranty: {
            terms: {
              type: "combined",
              duration_years: 10,
              coverage_min_pct: 90
            },
            claims: []
          },
          returns: {
            policies: {
              return_window_days: 60,
              restocking_fee_pct: 20,
              return_rate_pct: 1
            },
            records: []
          },
          traceability: {
            dpp: {
              enabled: false,
              uri: "",
              mandatory_fields: []
            },
            serialization: {
              format: "^INV[0-9]{8}$",
              generation_rule: "sequential"
            }
          },
          compliance: {
            certificates: [
              {
                standard: "IEC 62109",
                number: `IEC-INV-${idCounter}-2024`,
                issuer: "UL LLC",
                valid_until: "2029-12-31",
                scope: "Safety of power converters"
              },
              {
                standard: "IEEE 1547",
                number: `IEEE-${idCounter}-2024`,
                issuer: "IEEE Standards", 
                valid_until: "2029-12-31",
                scope: "Grid interconnection requirements"
              }
            ],
            sustainability: {
              embodied_co2e_kg: rating * 0.3,
              recyclable_pct: 75,
              hazardous_substances: []
            }
          },
          ai_logs: {
            classification_confidence: Math.random() * 0.3 + 0.7,
            last_enrichment: new Date().toISOString(),
            auto_actions: []
          },
          audit: {
            created_by: "system",
            created_at: new Date().toISOString(),
            updated_by: "system",
            updated_at: new Date().toISOString(),
            version: 1
          },
          analytics: {
            procurement_stats: {
              avg_lead_time_days: 21 + Math.floor(Math.random() * 14),
              price_trend_3m: Math.random() > 0.6 ? "stable" : "increasing",
              quality_score_pct: 90 + Math.floor(Math.random() * 10)
            }
          }
        }
      })
      idCounter++
    })
  })

  // Battery Storage Systems (BESS)
  const batteries = [
    { brand: "BatteryTech", series: "BT", models: [{w: 5000, kwh: 10.0}, {w: 10000, kwh: 20.0}], classification: { unspsc: "26111706" } },
    { brand: "EnergyStore", series: "ES", models: [{w: 7500, kwh: 15.0}, {w: 12500, kwh: 25.0}], classification: { unspsc: "26111706" } }
  ]

  batteries.forEach(battery => {
    battery.models.forEach(model => {
      const componentId = `CMP:${battery.brand.toUpperCase()}:${battery.series}-${model.kwh}:${model.w}W:V1.0`
      const name = `${battery.brand}_${battery.series}-${model.kwh}_${model.w}W`
      
      components.push({
        id: `comp_${String(idCounter).padStart(3, '0')}`,
        component_management: {
          version: "1.0",
          status: Math.random() > 0.75 ? "draft" : "available",
          component_identity: {
            component_id: componentId,
            brand: battery.brand,
            part_number: `${battery.series}-${model.kwh}`,
            rating_w: model.w,
            name: name,
            classification: {
              unspsc: battery.classification.unspsc,
              eclass: "27-01-03-01",
              hs_code: "850760"
            }
          },
          source_documents: {
            datasheet: {
              type: "datasheet",
              url: `https://docs.example.com/${componentId.replace(/:/g, '_')}.pdf`,
              hash: `sha256:${Math.random().toString(36).substring(2, 66)}`,
              parsed_at: new Date().toISOString()
            },
            additional: []
          },
          tracking_policy: {
            level: "serial",
            auto_rules: {
              regulatory_serial_required: true,
              warranty_sn_required: true,
              safety_critical: true
            }
          },
          supplier_chain: {
            suppliers: [
              {
                supplier_id: `SUP_${battery.brand.toUpperCase()}_001`,
                name: `${battery.brand} Energy Systems`,
                gln: "1234567890012",
                status: "approved",
                contact: {
                  email: `sales@${battery.brand.toLowerCase()}.com`,
                  phone: "+1-555-0300"
                }
              }
            ]
          },
          order_management: {
            rfq_enabled: true,
            orders: [],
            shipments: []
          },
          inventory: {
            stocks: [
              {
                location: { name: "Main Warehouse", gln: "1234567890456" },
                status: "in_stock",
                uom: "pcs",
                on_hand_qty: Math.floor(Math.random() * 20) + 2,
                lots: [],
                serials: []
              }
            ]
          },
          warranty: {
            terms: {
              type: "combined",
              duration_years: 10,
              coverage_min_pct: 70
            },
            claims: []
          },
          returns: {
            policies: {
              return_window_days: 30,
              restocking_fee_pct: 25,
              return_rate_pct: 0.5
            },
            records: []
          },
          traceability: {
            dpp: {
              enabled: true,
              uri: `https://dpp.example.com/${componentId}`,
              mandatory_fields: ["manufacturer", "model", "capacity_rating", "hazardous_substances", "recycling_instructions"]
            },
            serialization: {
              format: "^BAT[0-9]{9}$",
              generation_rule: "sequential"
            }
          },
          compliance: {
            certificates: [
              {
                standard: "UL 1973",
                number: `UL-BAT-${idCounter}-2024`,
                issuer: "UL LLC",
                valid_until: "2029-12-31",
                scope: "Batteries for use in stationary applications"
              },
              {
                standard: "IEC 62619",
                number: `IEC-BAT-${idCounter}-2024`,
                issuer: "TUV Sud",
                valid_until: "2029-12-31",
                scope: "Secondary lithium cells and batteries"
              }
            ],
            sustainability: {
              embodied_co2e_kg: model.kwh * 50,
              recyclable_pct: 95,
              hazardous_substances: ["Lithium", "Cobalt", "Nickel"]
            }
          },
          ai_logs: {
            classification_confidence: Math.random() * 0.3 + 0.7,
            last_enrichment: new Date().toISOString(),
            auto_actions: []
          },
          audit: {
            created_by: "system",
            created_at: new Date().toISOString(),
            updated_by: "system",
            updated_at: new Date().toISOString(),
            version: 1
          },
          analytics: {
            procurement_stats: {
              avg_lead_time_days: 28 + Math.floor(Math.random() * 21),
              price_trend_3m: "increasing",
              quality_score_pct: 88 + Math.floor(Math.random() * 12)
            }
          }
        }
      })
      idCounter++
    })
  })

  return components
}

// Performance optimization: Use lazy loading and caching
let odlComponents: any[] = []
let componentStats: any = null
let statsCalculated = false

// Function to ensure data is loaded
function ensureDataLoaded() {
  if (odlComponents.length === 0) {
    console.log('Loading ODL components data...')
    odlComponents = generateODLCompliantComponents()
  }
}

// Function to calculate stats only when needed with caching
function calculateStats() {
  if (!statsCalculated) {
    console.log('Calculating component statistics...')
    ensureDataLoaded()

    // Optimized: Calculate all stats in a single pass
    let activeCount = 0
    let draftCount = 0
    const categoryMap = { pv_modules: 0, inverters: 0, batteries: 0 }

    for (const component of odlComponents) {
      const status = component.component_management.status
      const unspsc = component.component_management.component_identity.classification?.unspsc

      if (status === "available") activeCount++
      if (status === "draft") draftCount++

      if (unspsc === "26111704") categoryMap.pv_modules++
      else if (unspsc === "26111705") categoryMap.inverters++
      else if (unspsc === "26111706") categoryMap.batteries++
    }

    componentStats = {
      total_components: odlComponents.length,
      active_components: activeCount,
      draft_components: draftCount,
      categories: categoryMap
    }

    statsCalculated = true
  }
  return componentStats
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    
    // Check if this is a stats request
    if (request.url.includes('/stats')) {
      const stats = calculateStats()
      console.log('Fetching ODL-SD v4.1 compliant component stats:', stats.total_components, 'components')
      return NextResponse.json(stats)
    }
    
    // Parse query parameters
    const page = parseInt(searchParams.get('page') || '1', 10)
    const pageSize = parseInt(searchParams.get('page_size') || '20', 10)
    const search = searchParams.get('search')
    const status = searchParams.get('status')
    const category = searchParams.get('category')
    
    // Ensure data is loaded before filtering
    ensureDataLoaded()
    let filteredComponents = odlComponents
    
    // Optimized filtering: Use single pass with early exits and pre-computed values
    const searchLower = search?.toLowerCase()
    const unspscMap = {
      'pv_modules': '26111704',
      'inverters': '26111705',
      'batteries': '26111706'
    }
    const targetUnspsc = category ? unspscMap[category as keyof typeof unspscMap] : null

    if (search || status || category) {
      filteredComponents = odlComponents.filter(comp => {
        const mgmt = comp.component_management
        const identity = mgmt.component_identity

        // Early exit if status doesn't match
        if (status && mgmt.status !== status) return false

        // Early exit if category doesn't match
        if (targetUnspsc && identity.classification?.unspsc !== targetUnspsc) return false

        // Check search terms only if search is provided
        if (searchLower) {
          const brand = identity.brand.toLowerCase()
          const partNumber = identity.part_number.toLowerCase()
          const componentId = identity.component_id.toLowerCase()

          if (!brand.includes(searchLower) &&
              !partNumber.includes(searchLower) &&
              !componentId.includes(searchLower)) {
            return false
          }
        }

        return true
      })
    }
    
    // Pagination
    const start = (page - 1) * pageSize
    const end = start + pageSize
    const paginatedComponents = filteredComponents.slice(start, end)
    
    console.log(`Fetching ODL-SD v4.1 components: ${paginatedComponents.length} components (page ${page})`)
    
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
    
    // Create new ODL-SD v4.1 compliant component
    const componentId = body.component_id || `CMP:${body.brand}:${body.part_number}:${body.rating_w}W:V1.0`
    const name = `${body.brand}_${body.part_number}_${body.rating_w}W`
    
    const newComponent = {
      id: `comp_${Date.now()}`,
      component_management: {
        version: "1.0",
        status: "draft",
        component_identity: {
          component_id: componentId,
          brand: body.brand,
          part_number: body.part_number,
          rating_w: body.rating_w,
          name: name,
          classification: body.classification || {}
        },
        source_documents: {
          datasheet: {
            type: "datasheet",
            url: body.datasheet_url || "",
            hash: `sha256:${Math.random().toString(36).substring(2, 66)}`,
            parsed_at: new Date().toISOString()
          },
          additional: []
        },
        tracking_policy: {
          level: "quantity",
          auto_rules: {
            regulatory_serial_required: false,
            warranty_sn_required: false,
            safety_critical: false
          }
        },
        supplier_chain: {
          suppliers: []
        },
        order_management: {
          rfq_enabled: true,
          orders: [],
          shipments: []
        },
        inventory: {
          stocks: []
        },
        warranty: {
          terms: {
            type: "product",
            duration_years: body.warranty_years || 1
          },
          claims: []
        },
        returns: {
          policies: {
            return_window_days: 30,
            restocking_fee_pct: 15,
            return_rate_pct: 5
          },
          records: []
        },
        traceability: {
          dpp: {
            enabled: false,
            uri: "",
            mandatory_fields: []
          },
          serialization: {
            format: "^[A-Z]{3}[0-9]{8}$",
            generation_rule: "sequential"
          }
        },
        compliance: {
          certificates: [],
          sustainability: {
            embodied_co2e_kg: 0,
            recyclable_pct: 0,
            hazardous_substances: []
          }
        },
        ai_logs: {
          classification_confidence: 0.0,
          last_enrichment: new Date().toISOString(),
          auto_actions: []
        },
        audit: {
          created_by: "user",
          created_at: new Date().toISOString(),
          updated_by: "user",
          updated_at: new Date().toISOString(),
          version: 1
        },
        analytics: {
          procurement_stats: {
            avg_lead_time_days: 0,
            price_trend_3m: "stable",
            quality_score_pct: 0
          }
        }
      }
    }
    
    console.log('Created new ODL-SD v4.1 component:', componentId)
    
    return NextResponse.json(newComponent, { status: 201 })
    
  } catch (error) {
    console.error('Error creating component:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}