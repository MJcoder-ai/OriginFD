"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  RFQRequest,
  RFQBid,
  BidStatus,
  SpecificationCompliance,
} from "@/lib/types";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Textarea,
  Label,
  Separator,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@originfd/ui";
import {
  FileText,
  Send,
  Clock,
  CheckCircle,
  XCircle,
  DollarSign,
  Calendar,
  Package,
  Award,
  AlertTriangle,
  Eye,
  Edit2,
} from "lucide-react";

interface SupplierPortalProps {
  supplierId?: string;
  supplierName?: string;
}

const getStatusBadgeVariant = (status: BidStatus) => {
  switch (status) {
    case "draft":
      return "secondary";
    case "submitted":
      return "default";
    case "under_review":
      return "secondary";
    case "shortlisted":
      return "default";
    case "awarded":
      return "default";
    case "rejected":
      return "destructive";
    case "withdrawn":
      return "outline";
    default:
      return "outline";
  }
};

const getRFQStatusBadgeVariant = (status: RFQRequest["status"]) => {
  switch (status) {
    case "draft":
      return "secondary";
    case "published":
      return "outline";
    case "receiving_bids":
      return "default";
    case "evaluation":
      return "secondary";
    case "awarded":
      return "default";
    case "completed":
      return "default";
    case "cancelled":
      return "destructive";
    default:
      return "outline";
  }
};

export default function SupplierPortal({
  supplierId = "sup_example_001",
  supplierName = "Example Solar Co.",
}: SupplierPortalProps) {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("open_rfqs");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedRFQ, setSelectedRFQ] = useState<RFQRequest | null>(null);
  const [bidDialogOpen, setBidDialogOpen] = useState(false);
  const [bidForm, setBidForm] = useState({
    unit_price: "",
    total_price: "",
    delivery_date: "",
    delivery_terms: "",
    validity_period_days: 30,
    notes: "",
    certifications: [] as string[],
    sustainability_score: "",
  });

  // Fetch available RFQs for bidding
  const { data: availableRFQs = [], isLoading: rfqsLoading } = useQuery({
    queryKey: ["supplier-rfqs", "receiving_bids"],
    queryFn: async () => {
      const response = await fetch("/api/bridge/rfq?status=receiving_bids");
      if (!response.ok) throw new Error("Failed to fetch RFQs");
      return response.json();
    },
  });

  // Fetch supplier's submitted bids
  const { data: supplierBids = [], isLoading: bidsLoading } = useQuery({
    queryKey: ["supplier-bids", supplierId],
    queryFn: async () => {
      // In real implementation, this would fetch bids by supplier_id
      // For now, we'll filter from available RFQs
      const allRFQs = await fetch("/api/bridge/rfq").then((r) => r.json());
      const bids: RFQBid[] = [];

      allRFQs.forEach((rfq: RFQRequest) => {
        rfq.bids.forEach((bid) => {
          if (bid.supplier_id === supplierId) {
            bids.push({
              ...bid,
              rfq_title: rfq.title,
              rfq_status: rfq.status,
            } as any); // Extended bid type with additional properties
          }
        });
      });

      return bids;
    },
  });

  // Submit bid mutation
  const submitBidMutation = useMutation({
    mutationFn: async (data: { rfqId: string; bidData: any }) => {
      const response = await fetch(`/api/bridge/rfq/${data.rfqId}/bids`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          supplier_id: supplierId,
          supplier_name: supplierName,
          unit_price: parseFloat(data.bidData.unit_price),
          total_price: parseFloat(data.bidData.total_price),
          currency: "USD",
          delivery_date: data.bidData.delivery_date,
          delivery_terms: data.bidData.delivery_terms,
          validity_period_days: data.bidData.validity_period_days,
          specifications_compliance: getSpecificationCompliance(selectedRFQ),
          certifications: data.bidData.certifications,
          sustainability_score: parseFloat(data.bidData.sustainability_score),
          notes: data.bidData.notes,
          status: "submitted",
        }),
      });
      if (!response.ok) throw new Error("Failed to submit bid");
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["supplier-bids"] });
      queryClient.invalidateQueries({ queryKey: ["supplier-rfqs"] });
      setBidDialogOpen(false);
      setSelectedRFQ(null);
      setBidForm({
        unit_price: "",
        total_price: "",
        delivery_date: "",
        delivery_terms: "",
        validity_period_days: 30,
        notes: "",
        certifications: [],
        sustainability_score: "",
      });
    },
  });

  const getSpecificationCompliance = (
    rfq: RFQRequest | null,
  ): SpecificationCompliance[] => {
    if (!rfq) return [];

    return rfq.specifications.map((spec, index) => ({
      specification_id: `spec_${index}`,
      compliant: true, // In real implementation, this would be based on form inputs
      value: spec.mandatory ? "Compliant" : "N/A",
      notes: "Meets all requirements",
    }));
  };

  const handleSubmitBid = () => {
    if (!selectedRFQ) return;

    submitBidMutation.mutate({
      rfqId: selectedRFQ.id,
      bidData: bidForm,
    });
  };

  const formatCurrency = (amount: number, currency: string = "USD") => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const getDaysRemaining = (deadline: string) => {
    const deadlineDate = new Date(deadline);
    const now = new Date();
    const diffTime = deadlineDate.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  if (rfqsLoading || bidsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Loading supplier portal...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Supplier Portal</h1>
          <p className="text-muted-foreground mt-2">
            Welcome back, {supplierName}
          </p>
        </div>
        <Badge variant="outline" className="text-lg px-4 py-2">
          {supplierName}
        </Badge>
      </div>

      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="space-y-4"
      >
        <TabsList>
          <TabsTrigger value="open_rfqs">Open RFQs</TabsTrigger>
          <TabsTrigger value="my_bids">My Bids</TabsTrigger>
          <TabsTrigger value="awards">Awards</TabsTrigger>
        </TabsList>

        <TabsContent value="open_rfqs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Available RFQs for Bidding
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="mb-4">
                <Input
                  placeholder="Search RFQs..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="max-w-sm"
                />
              </div>

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>Component</TableHead>
                    <TableHead>Quantity</TableHead>
                    <TableHead>Budget Range</TableHead>
                    <TableHead>Deadline</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {availableRFQs
                    .filter(
                      (rfq: RFQRequest) =>
                        rfq.title
                          .toLowerCase()
                          .includes(searchTerm.toLowerCase()) ||
                        rfq.description
                          .toLowerCase()
                          .includes(searchTerm.toLowerCase()),
                    )
                    .map((rfq: RFQRequest) => {
                      const daysRemaining = getDaysRemaining(
                        rfq.response_deadline,
                      );
                      const hasExistingBid = supplierBids.some(
                        (bid) => bid.rfq_id === rfq.id,
                      );

                      return (
                        <TableRow key={rfq.id}>
                          <TableCell>
                            <div>
                              <p className="font-medium">{rfq.title}</p>
                              <p className="text-sm text-muted-foreground truncate max-w-xs">
                                {rfq.description}
                              </p>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">{rfq.component_id}</Badge>
                          </TableCell>
                          <TableCell>
                            {rfq.quantity.toLocaleString()}{" "}
                            {rfq.unit_of_measure}
                          </TableCell>
                          <TableCell>
                            {rfq.budget_range ? (
                              <div className="text-sm">
                                {formatCurrency(rfq.budget_range.min)} -{" "}
                                {formatCurrency(rfq.budget_range.max)}
                                <span className="text-muted-foreground block">
                                  per unit
                                </span>
                              </div>
                            ) : (
                              <span className="text-muted-foreground">
                                Not specified
                              </span>
                            )}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Calendar className="h-4 w-4" />
                              <div>
                                <p className="text-sm">
                                  {formatDate(rfq.response_deadline)}
                                </p>
                                <p
                                  className={`text-xs ${
                                    daysRemaining <= 3
                                      ? "text-red-600"
                                      : daysRemaining <= 7
                                        ? "text-yellow-600"
                                        : "text-green-600"
                                  }`}
                                >
                                  {daysRemaining > 0
                                    ? `${daysRemaining} days left`
                                    : "Expired"}
                                </p>
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={getRFQStatusBadgeVariant(rfq.status)}
                            >
                              {rfq.status.replace("_", " ")}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setSelectedRFQ(rfq)}
                              >
                                <Eye className="h-4 w-4" />
                                View
                              </Button>
                              {!hasExistingBid && daysRemaining > 0 && (
                                <Button
                                  size="sm"
                                  onClick={() => {
                                    setSelectedRFQ(rfq);
                                    setBidDialogOpen(true);
                                  }}
                                >
                                  <Send className="h-4 w-4 mr-2" />
                                  Submit Bid
                                </Button>
                              )}
                              {hasExistingBid && (
                                <Badge variant="secondary">Bid Submitted</Badge>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="my_bids" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                My Submitted Bids
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>RFQ Title</TableHead>
                    <TableHead>My Bid</TableHead>
                    <TableHead>Delivery Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>RFQ Status</TableHead>
                    <TableHead>Submitted</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {supplierBids.map((bid: any) => (
                    <TableRow key={bid.id}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{bid.rfq_title}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium">
                            {formatCurrency(bid.unit_price)}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            Total: {formatCurrency(bid.total_price)}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>{formatDate(bid.delivery_date)}</TableCell>
                      <TableCell>
                        <Badge variant={getStatusBadgeVariant(bid.status)}>
                          {bid.status.replace("_", " ")}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={getRFQStatusBadgeVariant(bid.rfq_status)}
                        >
                          {bid.rfq_status?.replace("_", " ")}
                        </Badge>
                      </TableCell>
                      <TableCell>{formatDate(bid.submitted_at)}</TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm">
                            <Eye className="h-4 w-4" />
                            View
                          </Button>
                          {bid.status === "draft" && (
                            <Button variant="outline" size="sm">
                              <Edit2 className="h-4 w-4" />
                              Edit
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                  {supplierBids.length === 0 && (
                    <TableRow>
                      <TableCell
                        colSpan={7}
                        className="text-center py-8 text-muted-foreground"
                      >
                        No bids submitted yet. Check the Open RFQs tab to find
                        opportunities.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="awards" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Award className="h-5 w-5" />
                Awarded Contracts
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <Award className="h-16 w-16 mx-auto mb-4 text-muted-foreground/50" />
                <p>No awarded contracts yet.</p>
                <p className="text-sm">
                  Keep submitting competitive bids to win contracts!
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Bid Submission Dialog */}
      <Dialog open={bidDialogOpen} onOpenChange={setBidDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Submit Bid - {selectedRFQ?.title}</DialogTitle>
          </DialogHeader>

          {selectedRFQ && (
            <div className="space-y-6">
              {/* RFQ Summary */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">RFQ Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-sm font-medium text-muted-foreground">
                        Quantity
                      </Label>
                      <p>
                        {selectedRFQ.quantity.toLocaleString()}{" "}
                        {selectedRFQ.unit_of_measure}
                      </p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-muted-foreground">
                        Delivery Location
                      </Label>
                      <p>{selectedRFQ.delivery_location}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-muted-foreground">
                        Required Delivery
                      </Label>
                      <p>{formatDate(selectedRFQ.required_delivery_date)}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium text-muted-foreground">
                        Response Deadline
                      </Label>
                      <p className="text-red-600">
                        {formatDate(selectedRFQ.response_deadline)}
                      </p>
                    </div>
                  </div>

                  <div>
                    <Label className="text-sm font-medium text-muted-foreground">
                      Description
                    </Label>
                    <p className="text-sm mt-1">{selectedRFQ.description}</p>
                  </div>

                  {/* Specifications */}
                  <div>
                    <Label className="text-sm font-medium text-muted-foreground mb-2 block">
                      Specifications
                    </Label>
                    <div className="space-y-2">
                      {selectedRFQ.specifications.map((spec, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-2 bg-muted rounded"
                        >
                          <div>
                            <p className="font-medium">{spec.category}</p>
                            <p className="text-sm text-muted-foreground">
                              {spec.requirement}
                            </p>
                          </div>
                          {spec.mandatory && (
                            <Badge variant="destructive" className="text-xs">
                              Mandatory
                            </Badge>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Bid Form */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Your Bid</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="unit_price">Unit Price (USD)</Label>
                      <Input
                        id="unit_price"
                        type="number"
                        step="0.01"
                        placeholder="0.00"
                        value={bidForm.unit_price}
                        onChange={(e) => {
                          const unitPrice = parseFloat(e.target.value) || 0;
                          const totalPrice = unitPrice * selectedRFQ.quantity;
                          setBidForm((prev) => ({
                            ...prev,
                            unit_price: e.target.value,
                            total_price: totalPrice.toString(),
                          }));
                        }}
                      />
                    </div>
                    <div>
                      <Label htmlFor="total_price">Total Price (USD)</Label>
                      <Input
                        id="total_price"
                        type="number"
                        step="0.01"
                        placeholder="0.00"
                        value={bidForm.total_price}
                        onChange={(e) =>
                          setBidForm((prev) => ({
                            ...prev,
                            total_price: e.target.value,
                          }))
                        }
                      />
                    </div>
                    <div>
                      <Label htmlFor="delivery_date">Delivery Date</Label>
                      <Input
                        id="delivery_date"
                        type="date"
                        value={bidForm.delivery_date}
                        onChange={(e) =>
                          setBidForm((prev) => ({
                            ...prev,
                            delivery_date: e.target.value,
                          }))
                        }
                      />
                    </div>
                    <div>
                      <Label htmlFor="validity_period">
                        Bid Validity (Days)
                      </Label>
                      <Input
                        id="validity_period"
                        type="number"
                        value={bidForm.validity_period_days}
                        onChange={(e) =>
                          setBidForm((prev) => ({
                            ...prev,
                            validity_period_days:
                              parseInt(e.target.value) || 30,
                          }))
                        }
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="delivery_terms">Delivery Terms</Label>
                    <Input
                      id="delivery_terms"
                      placeholder="FOB Origin, CIF Destination, etc."
                      value={bidForm.delivery_terms}
                      onChange={(e) =>
                        setBidForm((prev) => ({
                          ...prev,
                          delivery_terms: e.target.value,
                        }))
                      }
                    />
                  </div>

                  <div>
                    <Label htmlFor="sustainability_score">
                      Sustainability Score (0-100)
                    </Label>
                    <Input
                      id="sustainability_score"
                      type="number"
                      min="0"
                      max="100"
                      placeholder="85"
                      value={bidForm.sustainability_score}
                      onChange={(e) =>
                        setBidForm((prev) => ({
                          ...prev,
                          sustainability_score: e.target.value,
                        }))
                      }
                    />
                  </div>

                  <div>
                    <Label htmlFor="notes">Additional Notes</Label>
                    <Textarea
                      id="notes"
                      placeholder="Any additional information about your bid..."
                      value={bidForm.notes}
                      onChange={(e) =>
                        setBidForm((prev) => ({
                          ...prev,
                          notes: e.target.value,
                        }))
                      }
                      rows={3}
                    />
                  </div>
                </CardContent>
              </Card>

              <div className="flex justify-end gap-4">
                <Button
                  variant="outline"
                  onClick={() => setBidDialogOpen(false)}
                  disabled={submitBidMutation.isPending}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSubmitBid}
                  disabled={
                    submitBidMutation.isPending ||
                    !bidForm.unit_price ||
                    !bidForm.delivery_date
                  }
                >
                  {submitBidMutation.isPending ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Submitting...
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4 mr-2" />
                      Submit Bid
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* RFQ Detail Dialog */}
      {selectedRFQ && !bidDialogOpen && (
        <Dialog open={!!selectedRFQ} onOpenChange={() => setSelectedRFQ(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>{selectedRFQ.title}</DialogTitle>
            </DialogHeader>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">
                    Quantity
                  </Label>
                  <p>
                    {selectedRFQ.quantity.toLocaleString()}{" "}
                    {selectedRFQ.unit_of_measure}
                  </p>
                </div>
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">
                    Budget Range
                  </Label>
                  <p>
                    {selectedRFQ.budget_range
                      ? `${formatCurrency(selectedRFQ.budget_range.min)} - ${formatCurrency(selectedRFQ.budget_range.max)}`
                      : "Not specified"}
                  </p>
                </div>
              </div>

              <div>
                <Label className="text-sm font-medium text-muted-foreground">
                  Description
                </Label>
                <p className="text-sm mt-1">{selectedRFQ.description}</p>
              </div>

              <div className="flex justify-end gap-4">
                <Button variant="outline" onClick={() => setSelectedRFQ(null)}>
                  Close
                </Button>
                <Button onClick={() => setBidDialogOpen(true)}>
                  Submit Bid
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
