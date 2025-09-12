/**
 * Temporary API client implementation while fixing workspace packages
 * This will be replaced with proper @originfd/http-client import once module resolution is fixed
 */

export type Domain = 'PV' | 'BESS' | 'HYBRID' | 'GRID' | 'MICROGRID'
export type Scale = 'RESIDENTIAL' | 'COMMERCIAL' | 'INDUSTRIAL' | 'UTILITY' | 'HYPERSCALE'

export interface DocumentCreateRequest {
  project_name: string
  portfolio_id?: string
  domain: Domain
  scale: Scale
  document_data: any
}

export interface DocumentResponse {
  id: string
  project_name: string
  domain: Domain
  scale: Scale
  current_version: number
  content_hash: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface ModelInfo {
  id: string
  name: string
  provider: string
  region: string
  cost_per_1k_tokens: number
  latency_ms: number
  eval_score: number
  is_active: boolean
  routing_rules?: Record<string, string>
  cag_hit_rate: number
  cag_drift: number
}

export interface UserResponse {
  id: string
  email: string
  full_name?: string
  is_active: boolean
  roles: string[]
}

export interface AuthTokens {
  accessToken: string
  refreshToken: string
}

export interface PSUUsageResponse {
  tenant_id: string
  total_psu: number
  events: any[]
}

export interface EscrowStatusResponse {
  tenant_id: string
  milestones: any[]
  total: number
}

export interface TransactionsResponse {
  tenant_id: string
  transactions: any[]
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: any
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export class OriginFDClient {
  private baseUrl: string
  private authTokens: { accessToken: string; refreshToken: string } | null = null

  constructor(baseUrl = '/api/bridge') {
    this.baseUrl = baseUrl
  }

  private async request(endpoint: string, options: RequestInit = {}): Promise<any> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    }

    if (this.authTokens?.accessToken) {
      headers['Authorization'] = `Bearer ${this.authTokens.accessToken}`
    }

    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const errorText = await response.text()
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`
      
      try {
        const errorData = JSON.parse(errorText)
        errorMessage = errorData.detail || errorMessage
      } catch {
        // Use default message if JSON parsing fails
      }
      
      throw new ApiError(errorMessage, response.status, errorText)
    }

    return response.json()
  }

  async createDocument(request: DocumentCreateRequest): Promise<DocumentResponse> {
    return this.request('odl/', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  async listProjects(): Promise<DocumentResponse[]> {
    return this.request('projects/')
  }

  async getProject(projectId: string): Promise<any> {
    return this.request(`projects/${projectId}`)
  }

  async getDocument(documentId: string): Promise<any> {
    return this.request(`documents/${documentId}`)
  }

  async getProjectDocuments(projectId: string): Promise<any[]> {
    return this.request(`projects/${projectId}/documents`)
  }

  async getPrimaryProjectDocument(projectId: string): Promise<any> {
    // Get the primary/main document for a project
    // For backward compatibility, try project-{uuid} format first
    try {
      return await this.request(`documents/${projectId}-main`)
    } catch (error) {
      // Fallback to old behavior for existing mock data
      console.warn('Primary document not found, falling back to project ID:', projectId)
      return await this.request(`documents/${projectId}`)
    }
  }


  async getProjectReview(projectId: string): Promise<any> {
    return this.request(`projects/${projectId}/review`)
  }

  // ---- New (Phase-1) ----
  async getProjectHierarchy(projectId: string): Promise<any> {
    return this.request(`projects/${projectId}/hierarchy`)
  }
  async getProjectViews(projectId: string): Promise<any[]> {
    return this.request(`projects/${projectId}/views`)
  }
  async getCanvasView(canvasId: string, projectId: string): Promise<any> {
    const qs = projectId ? `?projectId=${encodeURIComponent(projectId)}` : ''
    return this.request(`views/${canvasId}${qs}`)
  }
  async getSLD(projectId: string, scope: string): Promise<{ scope: string; nodes: any[]; edges: any[] }> {
    return this.request(`projects/${projectId}/sld?scope=${encodeURIComponent(scope)}`)
  }
  async getViewOverrides(canvasId: string): Promise<Record<string, { x: number; y: number }>> {
    return this.request(`views/${canvasId}/overrides`)
  }
  async patchViewOverrides(canvasId: string, positions: Record<string, { x: number; y: number }>): Promise<{ ok: boolean }> {
    return this.request(`views/${canvasId}/overrides`, { method: 'PATCH', body: JSON.stringify(positions) })
  }
  async getAsset(projectId: string, instanceId: string): Promise<any> {
    const qs = `?projectId=${encodeURIComponent(projectId)}`
    return this.request(`assets/${encodeURIComponent(instanceId)}${qs}`)
  }

  async getProjectScenarios(projectId: string): Promise<any[]> {
    return this.request(`projects/${projectId}/scenarios`)
  }

  async listModels(): Promise<ModelInfo[]> {
    return this.request('model-registry/models')
  }

  async submitApproval(projectId: string, approved: boolean): Promise<any> {
    return this.request('approvals', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, approved }),
    })

  }

  async login(credentials: LoginRequest): Promise<UserResponse> {
    const response = await this.request('auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    })
    
    this.authTokens = {
      accessToken: response.access_token,
      refreshToken: response.refresh_token,
    }

    // Store tokens in localStorage (in browser environment)
    if (typeof window !== 'undefined') {
      localStorage.setItem('originfd_tokens', JSON.stringify(this.authTokens))
    }

    // Return user data from login response (if available) or get user info separately
    if (response.user) {
      return response.user
    } else {
      return this.getCurrentUser()
    }
  }

  async getCurrentUser(): Promise<UserResponse> {
    return this.request('auth/me')
  }

  async logout(): Promise<void> {
    try {
      await this.request('auth/logout', { method: 'POST' })
    } catch (error) {
      // Ignore logout errors
    } finally {
      this.authTokens = null
      if (typeof window !== 'undefined') {
        localStorage.removeItem('originfd_tokens')
      }
    }
  }

  loadStoredTokens(): void {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('originfd_tokens')
      if (stored) {
        try {
          this.authTokens = JSON.parse(stored)
        } catch (error) {
          // Invalid stored tokens, remove them
          localStorage.removeItem('originfd_tokens')
        }
      }
    }
  }

  getTokens(): AuthTokens | null {
    return this.authTokens
  }

  setTokens(tokens: AuthTokens): void {
    this.authTokens = tokens
  }

  // Commerce APIs
  async getPsuUsage(tenantId: string): Promise<PSUUsageResponse> {
    return this.request(`commerce/psu/${tenantId}`)
  }

  async getEscrowStatus(tenantId: string): Promise<EscrowStatusResponse> {
    return this.request(`commerce/escrow/${tenantId}`)
  }

  async getTransactionHistory(tenantId: string): Promise<TransactionsResponse> {
    return this.request(`commerce/transactions/${tenantId}`)
  }

  // Component APIs
  async listComponents(params: {
    page?: number;
    page_size?: number;
    search?: string;
    category?: string;
    domain?: string;
    status?: string;
  } = {}): Promise<any> {
    const searchParams = new URLSearchParams()
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value))
      }
    })
    
    const query = searchParams.toString()
    return this.request(`components${query ? '?' + query : ''}`)
  }

  async getStats(): Promise<any> {
    return this.request('components/stats')
  }

  async getComponent(componentId: string): Promise<any> {
    return this.request(`components/${componentId}`)
  }

  async updateComponent(componentId: string, data: any): Promise<any> {
    return this.request(`components/${componentId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  }

  async transitionStatus(componentId: string, newStatus: string, comment?: string): Promise<any> {
    return this.request(`components/${componentId}/status`, {
      method: 'POST',
      body: JSON.stringify({ status: newStatus, comment }),
    })
  }

  async parseDatasheet(file: File): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)

    const url = `${this.baseUrl}/components/parse-datasheet`
    const headers: HeadersInit = {}
    if (this.authTokens?.accessToken) {
      headers['Authorization'] = `Bearer ${this.authTokens.accessToken}`
    }

    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      headers,
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new ApiError(`HTTP ${response.status}: ${response.statusText}`, response.status, errorText)
    }

    return response.json()
  }

  isAuthenticated(): boolean {
    return !!this.authTokens?.accessToken
  }
}

// Default client instance
export const apiClient = new OriginFDClient()

// Initialize stored tokens on import (browser only)
if (typeof window !== 'undefined') {
  apiClient.loadStoredTokens()
}

export const componentAPI = apiClient
export default apiClient
