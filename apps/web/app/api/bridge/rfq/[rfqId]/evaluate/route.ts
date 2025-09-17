import { NextRequest, NextResponse } from "next/server";
import { RFQBid, EvaluationCriteria } from "@/lib/types";

interface BidEvaluation {
  bid_id: string;
  price_score: number;
  delivery_score: number;
  quality_score: number;
  experience_score: number;
  sustainability_score: number;
  total_score: number;
  ranking: number;
  recommendation: "award" | "shortlist" | "reject";
  notes?: string;
}

interface EvaluationRequest {
  criteria: EvaluationCriteria;
  bids: RFQBid[];
  evaluator_notes?: Record<string, string>;
}

function calculateBidScore(
  bid: RFQBid,
  criteria: EvaluationCriteria,
  allBids: RFQBid[],
): BidEvaluation {
  // Price scoring (lower is better, normalized 0-100)
  const prices = allBids.map((b) => b.unit_price);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const priceScore =
    maxPrice === minPrice
      ? 100
      : ((maxPrice - bid.unit_price) / (maxPrice - minPrice)) * 100;

  // Delivery scoring (earlier is better)
  const deliveryDates = allBids.map((b) => new Date(b.delivery_date).getTime());
  const earliestDelivery = Math.min(...deliveryDates);
  const latestDelivery = Math.max(...deliveryDates);
  const bidDeliveryTime = new Date(bid.delivery_date).getTime();
  const deliveryScore =
    latestDelivery === earliestDelivery
      ? 100
      : ((latestDelivery - bidDeliveryTime) /
          (latestDelivery - earliestDelivery)) *
        100;

  // Quality scoring (based on certifications and compliance)
  const complianceRate =
    bid.specifications_compliance.filter((s) => s.compliant).length /
    Math.max(bid.specifications_compliance.length, 1);
  const certificationBonus = Math.min(bid.certifications.length * 10, 30);
  const qualityScore = Math.min(complianceRate * 70 + certificationBonus, 100);

  // Experience scoring (based on supplier history - mock scoring)
  const experienceScore = 75 + Math.random() * 25; // Mock: 75-100

  // Sustainability scoring (use provided score or calculate)
  const sustainabilityScore =
    bid.sustainability_score || 60 + Math.random() * 40;

  // Calculate weighted total
  const totalScore =
    (priceScore * criteria.price_weight +
      deliveryScore * criteria.delivery_weight +
      qualityScore * criteria.quality_weight +
      experienceScore * criteria.experience_weight +
      sustainabilityScore * criteria.sustainability_weight) /
    100;

  // Recommendation logic
  let recommendation: "award" | "shortlist" | "reject" = "reject";
  if (totalScore >= 85) recommendation = "award";
  else if (totalScore >= 70) recommendation = "shortlist";

  return {
    bid_id: bid.id,
    price_score: Math.round(priceScore * 100) / 100,
    delivery_score: Math.round(deliveryScore * 100) / 100,
    quality_score: Math.round(qualityScore * 100) / 100,
    experience_score: Math.round(experienceScore * 100) / 100,
    sustainability_score: Math.round(sustainabilityScore * 100) / 100,
    total_score: Math.round(totalScore * 100) / 100,
    ranking: 0, // Will be set after sorting
    recommendation,
    notes: `Price: $${bid.unit_price}, Delivery: ${bid.delivery_date}`,
  };
}

export async function POST(
  request: NextRequest,
  { params }: { params: { rfqId: string } },
) {
  try {
    const { rfqId } = params;
    const evaluationData: EvaluationRequest = await request.json();

    // Validate evaluation criteria weights sum to 100
    const totalWeight =
      Object.values(evaluationData.criteria).reduce(
        (sum, weight) => sum + weight,
        0,
      ) - evaluationData.criteria.total_weight;
    if (Math.abs(totalWeight - 100) > 0.01) {
      return NextResponse.json(
        { error: "Evaluation criteria weights must sum to 100" },
        { status: 400 },
      );
    }

    // Calculate scores for all bids
    const evaluations = evaluationData.bids.map((bid) =>
      calculateBidScore(bid, evaluationData.criteria, evaluationData.bids),
    );

    // Sort by total score (highest first) and assign rankings
    evaluations.sort((a, b) => b.total_score - a.total_score);
    evaluations.forEach((evaluation, index) => {
      evaluation.ranking = index + 1;
    });

    const evaluationResult = {
      rfq_id: rfqId,
      evaluated_at: new Date().toISOString(),
      evaluator_id: "user_procurement_001", // Mock user
      criteria: evaluationData.criteria,
      evaluations,
      summary: {
        total_bids: evaluations.length,
        recommended_awards: evaluations.filter(
          (e) => e.recommendation === "award",
        ).length,
        shortlisted: evaluations.filter((e) => e.recommendation === "shortlist")
          .length,
        rejected: evaluations.filter((e) => e.recommendation === "reject")
          .length,
        winning_bid_id: evaluations[0]?.bid_id,
        winning_score: evaluations[0]?.total_score,
      },
    };

    console.log("Completed bid evaluation for RFQ:", rfqId);
    return NextResponse.json(evaluationResult);
  } catch (error) {
    console.error("Error evaluating bids:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
