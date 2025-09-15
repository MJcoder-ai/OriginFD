/**
 * Typed HTTP client for OriginFD API
 */
import ky, { type KyInstance } from 'ky'
import type {
  LoginRequest,
  TokenResponse,
  UserResponse,
  DocumentCreateRequest,
  DocumentResponse,
  PatchRequest,
  PatchResponse,
  DocumentVersion,
  Task,
  ToolMetadata,
  OdlDocument,
  AuditEntry,
} from '@originfd/types-odl'

export interface ApiClientConfig {
  baseUrl?: string
  orchestratorUrl?: string
  timeout?: number
  headers?: Record<string, string>
}

export interface AuthTokens {
  accessToken: string
  refreshToken: string
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
  private api: KyInstance
  private orchestratorApi: KyInstance
  private authTokens: AuthTokens | null = null
  private baseUrl: string
  private orchestratorUrl: string

  constructor(config: ApiClientConfig = {}) {
    const {
      baseUrl = '/api/bridge',
      orchestratorUrl = process.env.NEXT_PUBLIC_ORCHESTRATOR_URL || 'http://localhost:8001',
      timeout = 30000,
      headers = {},
    } = config

    this.baseUrl = baseUrl
    this.orchestratorUrl = orchestratorUrl

    this.api = ky.create({
      prefixUrl: baseUrl,
      timeout,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      hooks: {
        beforeRequest: [
          (request) => {
            if (this.authTokens?.accessToken) {
              request.headers.set('Authorization', `Bearer ${this.authTokens.accessToken}`)
            }
          },
        ],
        afterResponse: [
          async (request, options, response) => {
            if (response.status === 401 && this.authTokens?.refreshToken) {
              // Try to refresh token
              try {
                await this.refreshToken()
                // Retry original request
                request.headers.set('Authorization', `Bearer ${this.authTokens!.accessToken}`)
                return ky(request)
              } catch (error) {
                // Refresh failed, clear tokens
                this.authTokens = null
                throw new ApiError('Authentication failed', 401)
              }
            }
            
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
            
            return response
          },
        ],
      },
    })

    this.orchestratorApi = ky.create({
      prefixUrl: orchestratorUrl,
      timeout,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      hooks: {
        beforeRequest: [
          (request) => {
            if (this.authTokens?.accessToken) {
              request.headers.set('Authorization', `Bearer ${this.authTokens.accessToken}`)
            }
          },
        ],
      },
    })
  }

  // Authentication
  async login(credentials: LoginRequest): Promise<UserResponse> {
    const response = await this.api.post('auth/login', { json: credentials }).json<TokenResponse>()
    
    this.authTokens = {
      accessToken: response.access_token,
      refreshToken: response.refresh_token,
    }

    // Store tokens in localStorage (in browser environment)
    if (typeof window !== 'undefined') {
      localStorage.setItem('originfd_tokens', JSON.stringify(this.authTokens))
    }

    // Get user info
    return this.getCurrentUser()
  }

  async refreshToken(): Promise<void> {
    if (!this.authTokens?.refreshToken) {
      throw new ApiError('No refresh token available', 401)
    }

    const response = await this.api
      .post('auth/refresh', {
        headers: {
          Authorization: `Bearer ${this.authTokens.refreshToken}`,
        },
      })
      .json<TokenResponse>()

    this.authTokens = {
      accessToken: response.access_token,
      refreshToken: response.refresh_token,
    }

    // Update stored tokens
    if (typeof window !== 'undefined') {
      localStorage.setItem('originfd_tokens', JSON.stringify(this.authTokens))
    }
  }

  async getCurrentUser(): Promise<UserResponse> {
    return this.api.get('auth/me').json<UserResponse>()
  }

  async logout(): Promise<void> {
    try {
      await this.api.post('auth/logout')
    } catch (error) {
      // Ignore logout errors
    } finally {
      this.authTokens = null
      if (typeof window !== 'undefined') {
        localStorage.removeItem('originfd_tokens')
      }
    }
  }

  setTokens(tokens: AuthTokens): void {
    this.authTokens = tokens
  }

  getTokens(): AuthTokens | null {
    return this.authTokens
  }

  // Load tokens from localStorage
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

  // Health checks
  async getHealth(): Promise<any> {
    return this.api.get('health').json()
  }

  async getHealthDetailed(): Promise<any> {
    return this.api.get('health/detailed').json()
  }

  // Document management
  async createDocument(request: DocumentCreateRequest): Promise<DocumentResponse> {
    return this.api.post('odl/', { json: request }).json<DocumentResponse>()
  }

  async getDocument(docId: string, version?: number): Promise<OdlDocument> {
    const searchParams = version ? { version: version.toString() } : {}
    return this.api.get(`odl/${docId}`, { searchParams }).json<OdlDocument>()
  }

  async patchDocument(request: PatchRequest): Promise<PatchResponse> {
    return this.api.post('odl/patch', { json: request }).json<PatchResponse>()
  }

  async getDocumentVersions(
    docId: string,
    limit = 50,
    offset = 0
  ): Promise<DocumentVersion[]> {
    return this.api
      .get(`odl/${docId}/versions`, {
        searchParams: { limit: limit.toString(), offset: offset.toString() },
      })
      .json<DocumentVersion[]>()
  }

  async getDocumentAudit(docId: string): Promise<{ document_id: string; total_entries: number; audit_entries: AuditEntry[] }> {
    return this.api.get(`odl/${docId}/audit`).json()
  }

  // AI Orchestrator
  async submitTask(
    taskType: string,
    description: string,
    context: Record<string, any>,
    priority: 'low' | 'normal' | 'high' | 'urgent' = 'normal'
  ): Promise<{ task_id: string }> {
    return this.orchestratorApi
      .post('tasks/', {
        json: {
          task_type: taskType,
          description,
          context,
          priority,
        },
      })
      .json<{ task_id: string }>()
  }

  async getTaskStatus(taskId: string): Promise<Task | null> {
    try {
      return await this.orchestratorApi.get(`tasks/${taskId}`).json<Task>()
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        return null
      }
      throw error
    }
  }

  async cancelTask(taskId: string): Promise<{ success: boolean }> {
    return this.orchestratorApi
      .delete(`tasks/${taskId}`)
      .json<{ success: boolean }>()
  }

  async listTasks(
    status?: string,
    limit = 50,
    offset = 0
  ): Promise<Task[]> {
    const searchParams: Record<string, string> = {
      limit: limit.toString(),
      offset: offset.toString(),
    }
    
    if (status) {
      searchParams.status = status
    }

    return this.orchestratorApi
      .get('tasks/', { searchParams })
      .json<Task[]>()
  }

  async listTools(category?: string): Promise<ToolMetadata[]> {
    const searchParams = category ? { category } : {}
    return this.orchestratorApi
      .get('tools/', { searchParams })
      .json<ToolMetadata[]>()
  }

  async getToolMetadata(toolName: string): Promise<ToolMetadata> {
    return this.orchestratorApi
      .get(`tools/${toolName}`)
      .json<ToolMetadata>()
  }

  // Project management (placeholder endpoints)
  async listProjects(): Promise<DocumentResponse[]> {
    // This would be a proper endpoint in the backend
    // For now, we'll simulate it by getting recent documents
    return this.api.get('projects/').json<DocumentResponse[]>()
  }

  async getProject(projectId: string): Promise<any> {
    return this.api.get(`projects/${projectId}`).json()
  }

  async updateProject(projectId: string, updates: any): Promise<any> {
    return this.api.patch(`projects/${projectId}`, { json: updates }).json()
  }

  async deleteProject(projectId: string): Promise<{ success: boolean }> {
    return this.api.delete(`projects/${projectId}`).json<{ success: boolean }>()
  }

  // Marketplace (placeholder)
  async listComponents(category?: string): Promise<any[]> {
    const searchParams = category ? { category } : {}
    return this.api.get('marketplace/components', { searchParams }).json<any[]>()
  }

  async getComponent(componentId: string): Promise<any> {
    return this.api.get(`marketplace/components/${componentId}`).json()
  }

  // Additional Project Methods
  async getProjectDocuments(projectId: string): Promise<DocumentResponse[]> {
    return this.api.get(`projects/${projectId}/documents`).json<DocumentResponse[]>()
  }

  async getPrimaryProjectDocument(projectId: string): Promise<OdlDocument> {
    return this.api.get(`projects/${projectId}/documents/primary`).json<OdlDocument>()
  }

  async getProjectReview(projectId: string): Promise<any> {
    return this.api.get(`projects/${projectId}/review`).json()
  }

  async submitApproval(projectId: string, approved: boolean): Promise<any> {
    return this.api.post(`projects/${projectId}/review/approve`, { json: { approved } }).json()
  }

  async getProjectScenarios(projectId: string): Promise<any[]> {
    return this.api.get(`projects/${projectId}/scenarios`).json<any[]>()
  }

  async adoptScenario(projectId: string, scenarioId: string): Promise<any> {
    return this.api.post(`projects/${projectId}/scenarios/${scenarioId}/adopt`).json()
  }

  // Model Registry
  async listModels(): Promise<any[]> {
    return this.api.get('models/').json<any[]>()
  }

  // Transparency Dashboard
  async getPsuUsage(tenantId: string): Promise<any> {
    return this.api.get(`transparency/tenants/${tenantId}/psu-usage`).json()
  }

  async getEscrowStatus(tenantId: string): Promise<any> {
    return this.api.get(`transparency/tenants/${tenantId}/escrow`).json()
  }

  async getTransactionHistory(tenantId: string): Promise<any[]> {
    return this.api.get(`transparency/tenants/${tenantId}/transactions`).json<any[]>()
  }

  // Canvas and Assets
  async getAsset(projectId: string, instanceId: string): Promise<any> {
    return this.api.get(`projects/${projectId}/assets/${instanceId}`).json()
  }

  async patchViewOverrides(viewId: string, overrides: any): Promise<any> {
    return this.api.patch(`views/${viewId}/overrides`, { json: overrides }).json()
  }

  // Document Export
  async exportDocument(projectId: string, format: string): Promise<any> {
    return this.api.get(`projects/${projectId}/export/${format}`).json()
  }

  // Operations and Warranty
  async createWarrantyClaim(deviceInstanceId: string, formData: any): Promise<any> {
    return this.api.post(`components/${deviceInstanceId}/warranty/claims`, { json: formData }).json()
  }

  async swapComponent(deviceInstanceId: string, swapData: any): Promise<any> {
    return this.api.post(`components/${deviceInstanceId}/swap`, { json: swapData }).json()
  }

  // Generic HTTP methods for compatibility
  async post(path: string, data?: any): Promise<any> {
    const options = data ? { json: data } : {}
    return this.api.post(path, options).json()
  }

  async patch(path: string, data?: any): Promise<any> {
    const options = data ? { json: data } : {}
    return this.api.patch(path, options).json()
  }

  async put(path: string, data?: any): Promise<any> {
    const options = data ? { json: data } : {}
    return this.api.put(path, options).json()
  }

  async delete(path: string): Promise<any> {
    return this.api.delete(path).json()
  }

  // Utility methods
  async get(path: string, searchParams?: Record<string, string>): Promise<any> {
    const options = searchParams ? { searchParams } : {}
    return this.api.get(path, options).json()
  }

  isAuthenticated(): boolean {
    return !!this.authTokens?.accessToken
  }

  getBaseUrl(): string {
    return this.baseUrl
  }

  getOrchestratorUrl(): string {
    return this.orchestratorUrl
  }
}

// Default client instance
export const apiClient = new OriginFDClient()

// Initialize stored tokens on import (browser only)
if (typeof window !== 'undefined') {
  apiClient.loadStoredTokens()
}

export default apiClient