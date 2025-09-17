import { NextRequest, NextResponse } from "next/server";
import { MediaProcessingJob, ProcessingJobType } from "@/lib/types";

// Mock processing jobs data
const mockProcessingJobs: MediaProcessingJob[] = [
  {
    id: "job_001",
    asset_id: "asset_004",
    job_type: "text_extraction",
    status: "completed",
    progress_percentage: 100,
    started_at: "2025-01-16T09:15:00Z",
    completed_at: "2025-01-16T09:18:00Z",
    output_metadata: {
      extracted_text_length: 15420,
      pages_processed: 28,
      confidence_score: 97.8,
      extracted_entities: [
        "power_rating",
        "voltage",
        "efficiency",
        "dimensions",
      ],
    },
  },
  {
    id: "job_002",
    asset_id: "asset_004",
    job_type: "thumbnail_generation",
    status: "completed",
    progress_percentage: 100,
    started_at: "2025-01-16T09:00:00Z",
    completed_at: "2025-01-16T09:02:00Z",
    output_metadata: {
      thumbnail_count: 1,
      thumbnail_size: "200x150",
      thumbnail_format: "jpeg",
    },
  },
  {
    id: "job_003",
    asset_id: "asset_005",
    job_type: "data_extraction",
    status: "processing",
    progress_percentage: 65,
    started_at: "2025-01-16T10:30:00Z",
    output_metadata: {
      progress_details: "Extracting technical specifications from page 3 of 4",
    },
  },
];

interface ProcessingJobRequest {
  asset_id: string;
  job_types: ProcessingJobType[];
  priority?: "low" | "normal" | "high";
  options?: Record<string, any>;
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const assetId = searchParams.get("asset_id");
    const jobType = searchParams.get("job_type");
    const status = searchParams.get("status");

    let filteredJobs = mockProcessingJobs;

    if (assetId) {
      filteredJobs = filteredJobs.filter((job) => job.asset_id === assetId);
    }

    if (jobType) {
      filteredJobs = filteredJobs.filter((job) => job.job_type === jobType);
    }

    if (status) {
      filteredJobs = filteredJobs.filter((job) => job.status === status);
    }

    console.log(`Fetching processing jobs: ${filteredJobs.length} found`);
    return NextResponse.json(filteredJobs);
  } catch (error) {
    console.error("Error fetching processing jobs:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const jobRequest: ProcessingJobRequest = await request.json();

    if (
      !jobRequest.asset_id ||
      !jobRequest.job_types ||
      jobRequest.job_types.length === 0
    ) {
      return NextResponse.json(
        { error: "Missing required fields: asset_id, job_types" },
        { status: 400 },
      );
    }

    // Create jobs for each requested type
    const createdJobs: MediaProcessingJob[] = [];

    for (const jobType of jobRequest.job_types) {
      const newJob: MediaProcessingJob = {
        id: `job_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`,
        asset_id: jobRequest.asset_id,
        job_type: jobType,
        status: "queued",
        progress_percentage: 0,
        started_at: new Date().toISOString(),
        output_metadata: {
          priority: jobRequest.priority || "normal",
          options: jobRequest.options || {},
        },
      };

      mockProcessingJobs.push(newJob);
      createdJobs.push(newJob);

      // Simulate job processing (in real implementation, queue to processing service)
      simulateJobProcessing(newJob);
    }

    console.log(
      `Created ${createdJobs.length} processing jobs for asset ${jobRequest.asset_id}`,
    );
    return NextResponse.json(createdJobs, { status: 201 });
  } catch (error) {
    console.error("Error creating processing jobs:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}

// Mock job processing simulation
function simulateJobProcessing(job: MediaProcessingJob) {
  // Simulate job progression
  setTimeout(() => {
    job.status = "processing";
    job.progress_percentage = 25;
  }, 1000);

  setTimeout(() => {
    job.progress_percentage = 50;
  }, 3000);

  setTimeout(() => {
    job.progress_percentage = 75;
  }, 5000);

  setTimeout(() => {
    job.status = "completed";
    job.progress_percentage = 100;
    job.completed_at = new Date().toISOString();

    // Generate mock output based on job type
    job.output_metadata = {
      ...job.output_metadata,
      ...generateMockOutput(job.job_type),
    };
  }, 8000);
}

function generateMockOutput(jobType: ProcessingJobType): Record<string, any> {
  switch (jobType) {
    case "thumbnail_generation":
      return {
        thumbnail_count: 1,
        thumbnail_size: "200x150",
        thumbnail_format: "jpeg",
        processing_time_ms: 2100,
      };

    case "text_extraction":
      return {
        extracted_text_length: Math.floor(Math.random() * 20000) + 5000,
        pages_processed: Math.floor(Math.random() * 20) + 1,
        confidence_score: Math.floor(Math.random() * 20) + 80,
        processing_time_ms: 5400,
      };

    case "data_extraction":
      return {
        extracted_entities: [
          "power_rating",
          "efficiency",
          "dimensions",
          "warranty",
        ],
        structured_data_points: Math.floor(Math.random() * 15) + 5,
        confidence_score: Math.floor(Math.random() * 25) + 75,
        processing_time_ms: 7200,
      };

    case "format_conversion":
      return {
        output_format: "pdf",
        compression_ratio: Math.floor(Math.random() * 30) + 70,
        quality_score: 95,
        processing_time_ms: 3200,
      };

    case "virus_scan":
      return {
        scan_result: "clean",
        signatures_checked: 5420892,
        scan_duration_ms: 1800,
      };

    case "compliance_check":
      return {
        compliance_score: Math.floor(Math.random() * 20) + 80,
        standards_checked: ["IEC 61215", "UL 1703", "CE"],
        issues_found: Math.floor(Math.random() * 3),
        processing_time_ms: 4500,
      };

    default:
      return {
        processing_time_ms: 2000,
        status: "completed",
      };
  }
}
