const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export type ApiKeyStatus = 'valid' | 'invalid' | 'unverified' | 'unconfigured' | 'unsaved' | 'unavailable';

export interface ApiKey {
  id: number;
  provider: string;
  key_value: string;
  is_active: boolean;
  description?: string;
  display_name?: string;
  source?: string;
  status?: ApiKeyStatus | string;
  validation_error?: string | null;
  last_validated_at?: string | null;
  last_validation_latency_ms?: number | null;
  created_at: string;
  updated_at?: string;
  last_used?: string;
}

export interface ApiKeySummary {
  id?: number;
  provider: string;
  display_name?: string;
  source?: string;
  status: ApiKeyStatus | string;
  is_active: boolean;
  description?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  last_used?: string | null;
  last_validated_at?: string | null;
  validation_error?: string | null;
  last_validation_latency_ms?: number | null;
  has_key: boolean;
  has_stored_key?: boolean;
  supports_model_discovery?: boolean;
}

export interface ApiKeyCreateRequest {
  provider: string;
  key_value: string;
  description?: string;
  is_active: boolean;
  validation_status?: string;
  validation_error?: string | null;
  last_validated_at?: string | null;
  last_validation_latency_ms?: number | null;
}

export interface ApiKeyUpdateRequest {
  key_value?: string;
  description?: string;
  is_active?: boolean;
  validation_status?: string;
  validation_error?: string | null;
  last_validated_at?: string | null;
  last_validation_latency_ms?: number | null;
}

export interface ApiKeyValidateResponse {
  provider: string;
  display_name: string;
  valid: boolean;
  status: ApiKeyStatus | string;
  checked_at: string;
  latency_ms?: number | null;
  error?: string | null;
  discovered_models?: string[] | null;
}

export interface ApiKeyBulkUpdateRequest {
  api_keys: ApiKeyCreateRequest[];
}

class ApiKeysService {
  private baseUrl = `${API_BASE_URL}/api-keys`;

  async getAllApiKeys(includeInactive = false): Promise<ApiKeySummary[]> {
    const params = new URLSearchParams();
    if (includeInactive) {
      params.append('include_inactive', 'true');
    }

    const response = await fetch(`${this.baseUrl}?${params}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch API keys: ${response.statusText}`);
    }
    return response.json();
  }

  async getApiKey(provider: string): Promise<ApiKey> {
    const response = await fetch(`${this.baseUrl}/${encodeURIComponent(provider)}`);
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('API key not found');
      }
      throw new Error(`Failed to fetch API key: ${response.statusText}`);
    }
    return response.json();
  }

  async validateApiKey(provider: string, keyValue: string): Promise<ApiKeyValidateResponse> {
    const response = await fetch(`${this.baseUrl}/validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ provider, key_value: keyValue }),
    });

    if (!response.ok) {
      throw new Error(`Failed to validate API key: ${response.statusText}`);
    }
    return response.json();
  }

  async createOrUpdateApiKey(request: ApiKeyCreateRequest): Promise<ApiKey> {
    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || `Failed to create/update API key: ${response.statusText}`);
    }
    return response.json();
  }

  async updateApiKey(provider: string, request: ApiKeyUpdateRequest): Promise<ApiKey> {
    const response = await fetch(`${this.baseUrl}/${encodeURIComponent(provider)}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('API key not found');
      }
      const errorText = await response.text();
      throw new Error(errorText || `Failed to update API key: ${response.statusText}`);
    }
    return response.json();
  }

  async deleteApiKey(provider: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/${encodeURIComponent(provider)}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('API key not found');
      }
      throw new Error(`Failed to delete API key: ${response.statusText}`);
    }
  }

  async bulkUpdateApiKeys(request: ApiKeyBulkUpdateRequest): Promise<ApiKey[]> {
    const response = await fetch(`${this.baseUrl}/bulk`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to bulk update API keys: ${response.statusText}`);
    }
    return response.json();
  }

  async updateLastUsed(provider: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/${encodeURIComponent(provider)}/last-used`, {
      method: 'PATCH',
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('API key not found');
      }
      throw new Error(`Failed to update last used timestamp: ${response.statusText}`);
    }
  }
}

export const apiKeysService = new ApiKeysService();
