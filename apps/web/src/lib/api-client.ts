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
      return this.request(`documents/${projectId}-main`)
    } catch (error) {
      // Fallback to old behavior for existing mock data
      console.warn('Primary document not found, falling back to project ID:', projectId)
      return this.request(`documents/${projectId}`)
    }
  }

  async getProjectReview(projectId: string): Promise<any> {
    return this.request(`projects/${projectId}/review`)
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

    // Get user info
    return this.getCurrentUser()
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