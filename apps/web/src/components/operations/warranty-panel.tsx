"use client";

import * as React from "react";
import { useState } from "react";
import { apiClient } from "@/lib/api-client";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Button,
  Input,
  Label,
  Textarea,
  Separator,
} from "@originfd/ui";
import { cn } from "@/lib/utils";

interface WarrantyPanelProps {
  /** Device instance identifier */
  deviceInstanceId: string;
  /** Current warranty status for the device */
  warrantyStatus?: string;
}

/**
 * Display warranty information and allow submission of claims with attachments.
 * Includes a simple replacement swap flow tied to the device instance ID.
 */
export function WarrantyPanel({
  deviceInstanceId,
  warrantyStatus = "unknown",
}: WarrantyPanelProps) {
  const [claimDescription, setClaimDescription] = useState("");
  const [attachments, setAttachments] = useState<File[]>([]);
  const [replacementId, setReplacementId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [swapSubmitting, setSwapSubmitting] = useState(false);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAttachments(Array.from(e.target.files || []));
  };

  const submitClaim = async () => {
    if (!claimDescription) return;
    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("description", claimDescription);
      attachments.forEach((file) => formData.append("attachments", file));
      await apiClient.post(
        `/components/${deviceInstanceId}/warranty/claims`,
        formData,
      );
      setClaimDescription("");
      setAttachments([]);
    } finally {
      setSubmitting(false);
    }
  };

  const submitSwap = async () => {
    if (!replacementId) return;
    setSwapSubmitting(true);
    try {
      await apiClient.post(`/components/${deviceInstanceId}/swap`, {
        replacement_id: replacementId,
      });
      setReplacementId("");
    } finally {
      setSwapSubmitting(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Warranty</CardTitle>
        <CardDescription>
          Manage warranty claims and device swaps
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <Label>Warranty Status</Label>
          <p
            className={cn(
              "mt-1 text-sm",
              warrantyStatus === "active" ? "text-green-600" : "text-red-600",
            )}
          >
            {warrantyStatus}
          </p>
        </div>

        {warrantyStatus === "active" && (
          <div className="space-y-2">
            <Label htmlFor="claim-description">Submit Claim</Label>
            <Textarea
              id="claim-description"
              value={claimDescription}
              onChange={(e) => setClaimDescription(e.target.value)}
              placeholder="Describe the issue"
            />
            <Input type="file" multiple onChange={onFileChange} />
            <Button onClick={submitClaim} disabled={submitting}>
              {submitting ? "Submitting..." : "Submit Claim"}
            </Button>
          </div>
        )}

        <Separator />

        <div className="space-y-2">
          <Label htmlFor="replacement-id">Replacement Device ID</Label>
          <Input
            id="replacement-id"
            value={replacementId}
            onChange={(e) => setReplacementId(e.target.value)}
            placeholder="Enter replacement device instance ID"
          />
          <Button
            variant="outline"
            onClick={submitSwap}
            disabled={swapSubmitting}
          >
            {swapSubmitting ? "Swapping..." : "Swap Device"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default WarrantyPanel;
