/**
 * Senhasegura A2A API Client for TypeScript
 * OAuth 2.0 authentication with credential management
 */

interface SenhaseguraConfig {
  baseUrl: string;
  clientId: string;
  clientSecret: string;
  timeout?: number;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

interface Credential {
  id: string;
  identifier: string;
  username: string;
  hostname: string;
  ip?: string;
  type: string;
  additional_info?: string;
  tags?: string[];
}

interface CredentialPassword {
  id: string;
  password: string;
  expiration: string;
}

interface ApiResponse<T> {
  response: {
    status: number;
    message: string;
    error: boolean;
    error_code: number;
  } & T;
}

export class SenhaseguraClient {
  private config: SenhaseguraConfig;
  private accessToken: string | null = null;
  private tokenExpiry: Date | null = null;

  constructor(config: SenhaseguraConfig) {
    this.config = {
      timeout: 30000,
      ...config,
    };
  }

  /**
   * Authenticate and obtain access token
   */
  async authenticate(): Promise<void> {
    const response = await fetch(`${this.config.baseUrl}/iso/oauth2/token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        grant_type: "client_credentials",
        client_id: this.config.clientId,
        client_secret: this.config.clientSecret,
      }),
      signal: AbortSignal.timeout(this.config.timeout!),
    });

    if (!response.ok) {
      throw new Error(`Authentication failed: ${response.status} ${response.statusText}`);
    }

    const data: TokenResponse = await response.json();
    this.accessToken = data.access_token;
    this.tokenExpiry = new Date(Date.now() + data.expires_in * 1000 - 60000); // 1 min buffer
  }

  /**
   * Ensure we have a valid token
   */
  private async ensureAuthenticated(): Promise<void> {
    if (!this.accessToken || !this.tokenExpiry || this.tokenExpiry < new Date()) {
      await this.authenticate();
    }
  }

  /**
   * Make authenticated API request
   */
  private async request<T>(
    method: string,
    endpoint: string,
    options?: { body?: unknown; params?: Record<string, string> }
  ): Promise<T> {
    await this.ensureAuthenticated();

    const url = new URL(`${this.config.baseUrl}${endpoint}`);
    if (options?.params) {
      Object.entries(options.params).forEach(([key, value]) => {
        url.searchParams.set(key, value);
      });
    }

    const response = await fetch(url.toString(), {
      method,
      headers: {
        Authorization: `Bearer ${this.accessToken}`,
        "Content-Type": "application/json",
      },
      body: options?.body ? JSON.stringify(options.body) : undefined,
      signal: AbortSignal.timeout(this.config.timeout!),
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * List all credentials
   */
  async listCredentials(): Promise<Credential[]> {
    const response = await this.request<ApiResponse<{ credentials: Credential[] }>>(
      "GET",
      "/api/pam/credential"
    );
    return response.response.credentials;
  }

  /**
   * Get credential by ID
   */
  async getCredential(id: string): Promise<Credential> {
    const response = await this.request<ApiResponse<{ credential: Credential }>>(
      "GET",
      `/api/pam/credential/${id}`
    );
    return response.response.credential;
  }

  /**
   * Get credential password
   */
  async getPassword(credentialId: string): Promise<CredentialPassword> {
    const response = await this.request<ApiResponse<{ credential: CredentialPassword }>>(
      "GET",
      "/iso/coe/senha",
      { params: { credentialId } }
    );
    return response.response.credential;
  }

  /**
   * Create new credential
   */
  async createCredential(credential: Omit<Credential, "id">): Promise<Credential> {
    const response = await this.request<ApiResponse<{ credential: Credential }>>(
      "POST",
      "/api/pam/credential",
      { body: credential }
    );
    return response.response.credential;
  }

  /**
   * Update credential
   */
  async updateCredential(id: string, updates: Partial<Credential>): Promise<Credential> {
    const response = await this.request<ApiResponse<{ credential: Credential }>>(
      "PUT",
      `/api/pam/credential/${id}`,
      { body: updates }
    );
    return response.response.credential;
  }

  /**
   * Release credential custody
   */
  async releaseCustody(credentialId: string): Promise<void> {
    await this.request("DELETE", `/iso/pam/credential/custody/${credentialId}`);
  }

  /**
   * Get password with automatic custody release
   */
  async withPassword<T>(
    credentialId: string,
    callback: (password: string) => Promise<T>
  ): Promise<T> {
    const { password } = await this.getPassword(credentialId);
    try {
      return await callback(password);
    } finally {
      await this.releaseCustody(credentialId);
    }
  }
}

// Example usage
async function main() {
  const client = new SenhaseguraClient({
    baseUrl: process.env.SENHASEGURA_URL!,
    clientId: process.env.SENHASEGURA_CLIENT_ID!,
    clientSecret: process.env.SENHASEGURA_CLIENT_SECRET!,
  });

  // List all credentials
  const credentials = await client.listCredentials();
  console.log("Credentials:", credentials);

  // Get password with automatic custody release
  const result = await client.withPassword("123", async (password) => {
    console.log("Using password for database connection...");
    // Use password here
    return { success: true };
  });

  console.log("Result:", result);
}

export default SenhaseguraClient;
