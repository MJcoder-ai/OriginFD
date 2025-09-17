import { NextRequest, NextResponse } from "next/server";
import { RFQBid, BidStatus } from "@/lib/types";

// Mock function to find RFQ by ID (in real implementation, this would query database)
function findRFQById(rfqId: string) {
  // This would typically be a database query
  // For now, we'll simulate finding the RFQ
  return {
    id: rfqId,
    status: "receiving_bids",
    response_deadline: "2025-02-15T17:00:00Z",
  };
}

export async function POST(
  request: NextRequest,
  { params }: { params: { rfqId: string } },
) {
  try {
    const { rfqId } = params;
    const bidData = await request.json();

    // Validate RFQ exists and is accepting bids
    const rfq = findRFQById(rfqId);
    if (!rfq) {
      return NextResponse.json({ error: "RFQ not found" }, { status: 404 });
    }

    if (rfq.status !== "receiving_bids") {
      return NextResponse.json(
        { error: "RFQ is not accepting bids" },
        { status: 400 },
      );
    }

    // Check if deadline has passed
    const deadline = new Date(rfq.response_deadline);
    const now = new Date();
    if (now > deadline) {
      return NextResponse.json(
        { error: "Bid submission deadline has passed" },
        { status: 400 },
      );
    }

    const newBid: RFQBid = {
      id: `bid_${Date.now()}`,
      rfq_id: rfqId,
      ...bidData,
      status: bidData.status || "submitted",
      submitted_at: new Date().toISOString(),
    };

    // In real implementation, save to database
    console.log("Created new bid:", newBid.id, "for RFQ:", rfqId);

    return NextResponse.json(newBid, { status: 201 });
  } catch (error) {
    console.error("Error creating bid:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: { rfqId: string } },
) {
  try {
    const { rfqId } = params;
    const { searchParams } = new URL(request.url);
    const status = searchParams.get("status");
    const supplierId = searchParams.get("supplier_id");

    // In real implementation, query database for bids
    // For now, return mock data
    let mockBids: RFQBid[] = [
      {
        id: "bid_001",
        rfq_id: rfqId,
        supplier_id: "sup_longi_001",
        supplier_name: "LONGi Solar",
        unit_price: 0.42,
        total_price: 105000,
        currency: "USD",
        delivery_date: "2025-03-10",
        delivery_terms: "FOB Phoenix, AZ",
        validity_period_days: 30,
        specifications_compliance: [],
        certifications: ["IEC 61215", "UL 1703"],
        status: "submitted",
        submitted_at: "2025-01-20T14:30:00Z",
        evaluation_score: 88.5,
      },
    ];

    // Apply filters
    if (status) {
      mockBids = mockBids.filter((bid) => bid.status === status);
    }

    if (supplierId) {
      mockBids = mockBids.filter((bid) => bid.supplier_id === supplierId);
    }

    return NextResponse.json(mockBids);
  } catch (error) {
    console.error("Error fetching bids:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
