import { NextRequest, NextResponse } from 'next/server'

// Types for inventory management
interface LocationDetails {
  building: string;
  room: string;
  shelf: string;
  bin: string;
}

interface InventoryRecord {
  component_id: string;
  warehouse_location: string;
  quantity_available: number;
  quantity_reserved: number;
  quantity_on_order: number;
  reorder_level: number;
  reorder_quantity: number;
  unit_cost: number;
  last_updated: string;
  location_details: LocationDetails;
}

interface InventoryTransaction {
  id: string;
  component_id: string;
  transaction_type: 'receipt' | 'issue' | 'transfer' | 'adjustment' | 'return';
  quantity: number;
  unit_cost: number;
  from_location?: string;
  to_location?: string;
  reference_number: string;
  notes: string;
  created_by: string;
  created_at: string;
}

// Mock inventory data generator
function generateInventoryData(componentIds: string[]) {
  const warehouses = ['Main Warehouse', 'Site Storage A', 'Site Storage B', 'Field Office']
  const inventoryRecords: InventoryRecord[] = []

  componentIds.forEach(componentId => {
    // Not all components have inventory records (some are catalog-only)
    if (Math.random() > 0.3) {
      const warehouse = warehouses[Math.floor(Math.random() * warehouses.length)]
      const available = Math.floor(Math.random() * 100) + 1
      const reserved = Math.floor(Math.random() * 20)
      const onOrder = Math.floor(Math.random() * 50)

      inventoryRecords.push({
        component_id: componentId,
        warehouse_location: warehouse,
        quantity_available: available,
        quantity_reserved: reserved,
        quantity_on_order: onOrder,
        reorder_level: Math.floor(available * 0.2),
        reorder_quantity: Math.floor(available * 0.5),
        unit_cost: Math.floor(Math.random() * 1000) + 100,
        last_updated: new Date().toISOString(),
        location_details: {
          building: warehouse.includes('Site') ? 'Storage Building' : 'Main Building',
          room: `Room ${Math.floor(Math.random() * 10) + 1}`,
          shelf: `Shelf ${String.fromCharCode(65 + Math.floor(Math.random() * 5))}`,
          bin: `Bin ${Math.floor(Math.random() * 20) + 1}`
        }
      })
    }
  })

  return inventoryRecords
}

// Mock transaction data
function generateTransactionData() {
  const transactionTypes = ['receipt', 'issue', 'transfer', 'adjustment', 'return'] as const
  const transactions: InventoryTransaction[] = []

  for (let i = 0; i < 50; i++) {
    const transactionType = transactionTypes[Math.floor(Math.random() * transactionTypes.length)]
    transactions.push({
      id: `txn_${Date.now()}_${i}`,
      component_id: `comp_${String(Math.floor(Math.random() * 115) + 1).padStart(3, '0')}`,
      transaction_type: transactionType,
      quantity: Math.floor(Math.random() * 50) + 1,
      unit_cost: Math.floor(Math.random() * 500) + 50,
      from_location: transactionType === 'transfer' ? 'Main Warehouse' : undefined,
      to_location: transactionType === 'transfer' ? 'Site Storage A' : undefined,
      reference_number: `REF-${Date.now()}-${i}`,
      notes: `${transactionType} transaction for component`,
      created_by: 'system_user',
      created_at: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString()
    })
  }

  return transactions.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
}

let mockInventoryData: InventoryRecord[] = []
let mockTransactionData: InventoryTransaction[] = []

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)

    // Check if this is a transactions request
    if (request.url.includes('/transactions')) {
      if (!mockTransactionData.length) {
        mockTransactionData = generateTransactionData()
      }

      const componentId = searchParams.get('component_id')
      let filteredTransactions = mockTransactionData

      if (componentId) {
        filteredTransactions = mockTransactionData.filter(t => t.component_id === componentId)
      }

      const page = parseInt(searchParams.get('page') || '1', 10)
      const pageSize = parseInt(searchParams.get('page_size') || '20', 10)
      const start = (page - 1) * pageSize
      const end = start + pageSize

      return NextResponse.json({
        transactions: filteredTransactions.slice(start, end),
        total: filteredTransactions.length,
        page,
        page_size: pageSize,
        total_pages: Math.ceil(filteredTransactions.length / pageSize)
      })
    }

    // Generate inventory data if not exists
    if (!mockInventoryData.length) {
      const componentIds = Array.from({length: 115}, (_, i) => `comp_${String(i + 1).padStart(3, '0')}`)
      mockInventoryData = generateInventoryData(componentIds)
    }

    const componentId = searchParams.get('component_id')
    const warehouse = searchParams.get('warehouse')
    const lowStock = searchParams.get('low_stock') === 'true'

    let filteredInventory = mockInventoryData

    if (componentId) {
      filteredInventory = filteredInventory.filter(inv => inv.component_id === componentId)
    }

    if (warehouse) {
      filteredInventory = filteredInventory.filter(inv => inv.warehouse_location === warehouse)
    }

    if (lowStock) {
      filteredInventory = filteredInventory.filter(inv => inv.quantity_available <= inv.reorder_level)
    }

    const page = parseInt(searchParams.get('page') || '1', 10)
    const pageSize = parseInt(searchParams.get('page_size') || '20', 10)
    const start = (page - 1) * pageSize
    const end = start + pageSize

    console.log(`Fetching inventory: ${filteredInventory.length} records (page ${page})`)

    return NextResponse.json({
      inventory: filteredInventory.slice(start, end),
      total: filteredInventory.length,
      page,
      page_size: pageSize,
      total_pages: Math.ceil(filteredInventory.length / pageSize)
    })

  } catch (error) {
    console.error('Error fetching inventory:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // Check if this is a transaction creation
    if (body.transaction_type) {
      const newTransaction = {
        id: `txn_${Date.now()}`,
        component_id: body.component_id,
        transaction_type: body.transaction_type,
        quantity: body.quantity,
        unit_cost: body.unit_cost,
        from_location: body.from_location,
        to_location: body.to_location,
        reference_number: body.reference_number || `REF-${Date.now()}`,
        notes: body.notes || '',
        created_by: body.created_by || 'user',
        created_at: new Date().toISOString()
      }

      mockTransactionData.unshift(newTransaction)

      // Update inventory quantities based on transaction
      const inventoryRecord = mockInventoryData.find(inv => inv.component_id === body.component_id)
      if (inventoryRecord) {
        switch (body.transaction_type) {
          case 'receipt':
            inventoryRecord.quantity_available += body.quantity
            break
          case 'issue':
            inventoryRecord.quantity_available = Math.max(0, inventoryRecord.quantity_available - body.quantity)
            break
          case 'adjustment':
            inventoryRecord.quantity_available = Math.max(0, body.quantity)
            break
        }
        inventoryRecord.last_updated = new Date().toISOString()
      }

      console.log('Created inventory transaction:', newTransaction.id)
      return NextResponse.json(newTransaction, { status: 201 })
    }

    // Create new inventory record
    const newInventory = {
      component_id: body.component_id,
      warehouse_location: body.warehouse_location,
      quantity_available: body.quantity_available || 0,
      quantity_reserved: body.quantity_reserved || 0,
      quantity_on_order: body.quantity_on_order || 0,
      reorder_level: body.reorder_level || 10,
      reorder_quantity: body.reorder_quantity || 50,
      unit_cost: body.unit_cost || 0,
      last_updated: new Date().toISOString(),
      location_details: body.location_details || {}
    }

    mockInventoryData.push(newInventory)

    console.log('Created inventory record for component:', newInventory.component_id)
    return NextResponse.json(newInventory, { status: 201 })

  } catch (error) {
    console.error('Error creating inventory record:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function PUT(request: NextRequest) {
  try {
    const body = await request.json()
    const { searchParams } = new URL(request.url)
    const componentId = searchParams.get('component_id')
    const warehouse = searchParams.get('warehouse')

    if (!componentId) {
      return NextResponse.json({ error: 'Component ID required' }, { status: 400 })
    }

    const inventoryIndex = mockInventoryData.findIndex(inv =>
      inv.component_id === componentId &&
      (!warehouse || inv.warehouse_location === warehouse)
    )

    if (inventoryIndex === -1) {
      return NextResponse.json({ error: 'Inventory record not found' }, { status: 404 })
    }

    mockInventoryData[inventoryIndex] = {
      ...mockInventoryData[inventoryIndex],
      ...body,
      last_updated: new Date().toISOString()
    }

    console.log('Updated inventory record for component:', componentId)
    return NextResponse.json(mockInventoryData[inventoryIndex])

  } catch (error) {
    console.error('Error updating inventory:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}