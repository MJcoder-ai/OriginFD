/**
 * Temporary API client implementation while fixing workspace packages
 * This will be replaced with proper @originfd/http-client import once module resolution is fixed
 */

export type Domain = "PV" | "BESS" | "HYBRID" | "GRID" | "MICROGRID";
export type Scale =
  | "RESIDENTIAL"
  | "COMMERCIAL"
  | "INDUSTRIAL"
  | "UTILITY"
  | "HYPERSCALE";

export type ProjectStatus = "draft" | "active" | "under_review" | "completed";

export interface ProjectCreateRequest {
  name: string;
  description?: string;
  domain: Domain;
  scale: Scale;
  location_name?: string;
  latitude?: number;
  longitude?: number;
  country_code?: string;
  total_capacity_kw?: number;
  tags?: string[];
}

export interface ProjectResponse {
  id: string;
  name: string;
  description?: string | null;
  domain: Domain;
  scale: Scale;
  status: ProjectStatus;
  display_status: string;
  completion_percentage: number;
  location_name?: string | null;
  total_capacity_kw?: number | null;
  tags: string[];
  owner_id: string;
  created_at: string;
  updated_at: string;
  initialization_task_id?: string | null;
  document_id?: string | null;
  document_hash?: string | null;
}

export interface DocumentCreateRequest {
  project_name: string;
  portfolio_id?: string;
  domain: Domain;
  scale: Scale;
  document_data: any;
}

export interface DocumentResponse {
  id: string;
  project_name: string;
  domain: Domain;
  scale: Scale;
  current_version: number;
  content_hash: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  region: string;
  cost_per_1k_tokens: number;
  latency_ms: number;
  eval_score: number;
  is_active: boolean;
  routing_rules?: Record<string, string>;
  cag_hit_rate: number;
  cag_drift: number;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  roles: string[];
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

export interface PSUUsageResponse {
  tenant_id: string;
  total_psu: number;
  events: any[];
}

export interface EscrowStatusResponse {
  tenant_id: string;
  milestones: any[];
  total: number;
}

export interface TransactionsResponse {
  tenant_id: string;
  transactions: any[];
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: any,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const normalizeBaseUrl = (baseUrl: string): string => {
  if (!baseUrl) {
    return "/api/proxy";
  }

  const trimmed = baseUrl.trim();
  return trimmed.replace(/\/+$/, "");
};

const resolveApiBaseUrl = (): string => {
  if (typeof window !== "undefined") {
    const browserBase = (window as any).__ORIGINFD_API_BASE__;
    if (typeof browserBase === "string" && browserBase.trim().length > 0) {
      return normalizeBaseUrl(browserBase);
    }
  }

  return normalizeBaseUrl("/api/proxy");
};

export class OriginFDClient {
  private baseUrl: string;

  constructor(baseUrl = resolveApiBaseUrl()) {
    this.baseUrl = normalizeBaseUrl(baseUrl);
  }

  private async request(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<any> {
    const url = `${this.baseUrl}${
      endpoint.startsWith("/") ? endpoint : "/" + endpoint
    }`;

    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };

    const response = await fetch(url, {
      ...options,
      headers,
      cache: "no-store",
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

      try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.detail || errorMessage;
      } catch {
        // Use default message if JSON parsing fails
      }

      throw new ApiError(errorMessage, response.status, errorText);
    }

    return response.json();
  }

  async createDocument(
    request: DocumentCreateRequest,
  ): Promise<DocumentResponse> {
    return this.request("odl/", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async createProject(request: ProjectCreateRequest): Promise<ProjectResponse> {
    return this.request("projects/", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async listProjects(): Promise<DocumentResponse[]> {
    return this.request("projects/");
  }

  async getProject(projectId: string): Promise<any> {
    return this.request(`projects/${projectId}`);
  }

  async getDocument(documentId: string): Promise<any> {
    return this.request(`documents/${documentId}`);
  }

  async getProjectDocuments(projectId: string): Promise<any[]> {
    return this.request(`projects/${projectId}/documents`);
  }

  async getPrimaryProjectDocument(projectId: string): Promise<any> {
    // Get the primary/main document for a project
    // For backward compatibility, try project-{uuid} format first
    try {
      return await this.request(`documents/${projectId}-main`);
    } catch (error) {
      // Fallback to old behavior for existing mock data
      console.warn(
        "Primary document not found, falling back to project ID:",
        projectId,
      );
      return await this.request(`documents/${projectId}`);
    }
  }

  async getProjectReview(projectId: string): Promise<any> {
    return this.request(`projects/${projectId}/review`);
  }

  // ---- New (Phase-1) ----
  async getProjectHierarchy(projectId: string): Promise<any> {
    return this.request(`projects/${projectId}/hierarchy`);
  }
  async getProjectViews(projectId: string): Promise<any[]> {
    return this.request(`projects/${projectId}/views`);
  }
  async getCanvasView(canvasId: string, projectId: string): Promise<any> {
    const qs = projectId ? `?projectId=${encodeURIComponent(projectId)}` : "";
    return this.request(`views/${canvasId}${qs}`);
  }
  async getSLD(
    projectId: string,
    scope: string,
  ): Promise<{ scope: string; nodes: any[]; edges: any[] }> {
    return this.request(
      `projects/${projectId}/sld?scope=${encodeURIComponent(scope)}`,
    );
  }
  async getViewOverrides(
    canvasId: string,
  ): Promise<Record<string, { x: number; y: number }>> {
    return this.request(`views/${canvasId}/overrides`);
  }
  async patchViewOverrides(
    canvasId: string,
    positions: Record<string, { x: number; y: number }>,
  ): Promise<{ ok: boolean }> {
    return this.request(`views/${canvasId}/overrides`, {
      method: "PATCH",
      body: JSON.stringify(positions),
    });
  }
  async getAsset(projectId: string, instanceId: string): Promise<any> {
    const qs = `?projectId=${encodeURIComponent(projectId)}`;
    return this.request(`assets/${encodeURIComponent(instanceId)}${qs}`);
  }

  async getProjectScenarios(projectId: string): Promise<any[]> {
    return this.request(`projects/${projectId}/scenarios`);
  }

  async adoptScenario(projectId: string, scenarioId: string): Promise<any> {
    return this.request(`projects/${projectId}/scenarios/${scenarioId}/adopt`, {
      method: "POST",
    });
  }

  async createComponent(request: any): Promise<any> {
    return this.request("components", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async exportDocument(projectId: string, format: string): Promise<any> {
    return this.request(`projects/${projectId}/export/${format}`);
  }

  // Operation methods for warranty panel
  async post(path: string, data?: any): Promise<any> {
    const options = data
      ? { method: "POST", body: JSON.stringify(data) }
      : { method: "POST" };
    return this.request(path, options);
  }

  async getPlannerTrace(runId: string): Promise<any> {
    return this.request(`planner/${runId}`);
  }

  async listModels(): Promise<ModelInfo[]> {
    return this.request("model-registry/models");
  }

  async submitApproval(projectId: string, approved: boolean): Promise<any> {
    return this.request("approvals", {
      method: "POST",
      body: JSON.stringify({ project_id: projectId, approved }),
    });
  }

  async login(credentials: LoginRequest): Promise<UserResponse> {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(credentials),
      cache: "no-store",
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = "Authentication failed";
      try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.detail || errorMessage;
      } catch {
        if (errorText) {
          errorMessage = errorText;
        }
      }

      throw new ApiError(errorMessage, response.status);
    }

    const data = await response.json();

    if (data?.user) {
      return data.user;
    }

    return this.getCurrentUser();
  }

  async getCurrentUser(): Promise<UserResponse> {
    const response = await fetch("/api/auth/me", {
      method: "GET",
      cache: "no-store",
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

      try {
        const errorData = JSON.parse(errorText);
        errorMessage = errorData.detail || errorMessage;
      } catch {
        if (errorText) {
          errorMessage = errorText;
        }
      }

      throw new ApiError(errorMessage, response.status);
    }

    return response.json();
  }

  async logout(): Promise<void> {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } catch (error) {
      // Ignore logout errors
    }
  }

  loadStoredTokens(): void {}

  getTokens(): AuthTokens | null {
    return null;
  }

  setTokens(_tokens: AuthTokens): void {}

  // Commerce APIs
  async getPsuUsage(tenantId: string): Promise<PSUUsageResponse> {
    return this.request(`commerce/psu/${tenantId}`);
  }

  async getEscrowStatus(tenantId: string): Promise<EscrowStatusResponse> {
    return this.request(`commerce/escrow/${tenantId}`);
  }

  async getTransactionHistory(tenantId: string): Promise<TransactionsResponse> {
    return this.request(`commerce/transactions/${tenantId}`);
  }

  async getHealth(): Promise<any> {
    return this.request("health");
  }

  async submitTask(
    taskType: string,
    description: string,
    context: any,
    priority = "normal",
  ): Promise<any> {
    return this.request("tasks/", {
      method: "POST",
      body: JSON.stringify({
        task_type: taskType,
        description,
        context,
        priority,
      }),
    });
  }

  // Component APIs
  async listComponents(
    params: {
      page?: number;
      page_size?: number;
      search?: string;
      category?: string;
      domain?: string;
      status?: string;
    } = {},
  ): Promise<any> {
    const searchParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });

    const query = searchParams.toString();
    return this.request(`components${query ? "?" + query : ""}`);
  }

  async getStats(): Promise<any> {
    return this.request("components/stats");
  }

  async getComponent(componentId: string): Promise<any> {
    return this.request(`components/${componentId}`);
  }

  async updateComponent(componentId: string, data: any): Promise<any> {
    return this.request(`components/${componentId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async transitionStatus(
    componentId: string,
    newStatus: string,
    comment?: string,
  ): Promise<any> {
    return this.request(`components/${componentId}/status`, {
      method: "POST",
      body: JSON.stringify({ status: newStatus, comment }),
    });
  }

  async parseDatasheet(file: File): Promise<any> {
    const formData = new FormData();
    formData.append("file", file);

    const url = `${this.baseUrl}/components/parse-datasheet`;
    const response = await fetch(url, {
      method: "POST",
      body: formData,
      cache: "no-store",
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new ApiError(
        `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorText,
      );
    }

    return response.json();
  }

  isAuthenticated(): boolean {
    return false;
  }
}

// Default client instance
// Use real backend API instead of mock endpoints
// Use environment variable for API base URL in production
export const API_BASE_URL = resolveApiBaseUrl();

export const apiClient = new OriginFDClient(API_BASE_URL);

// Initialize stored tokens on import (browser only)
if (typeof window !== "undefined") {
  apiClient.loadStoredTokens();
}

export const componentAPI = apiClient;
export default apiClient;
