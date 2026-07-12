#!/usr/bin/env bun
/**
 * Senhasegura MCP Server
 *
 * Exposes core senhasegura PAM operations as MCP tools.
 * Run via Bun. See ../References/McpIntegration.md for client wiring.
 *
 * Required environment variables:
 *   SENHASEGURA_URL
 *   SENHASEGURA_CLIENT_ID
 *   SENHASEGURA_CLIENT_SECRET
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

interface SenhaseguraConfig {
  baseUrl: string;
  clientId: string;
  clientSecret: string;
}

class SenhaseguraClient {
  private accessToken: string | null = null;
  private tokenExpiry: Date | null = null;

  constructor(private config: SenhaseguraConfig) {}

  async authenticate(): Promise<void> {
    const response = await fetch(`${this.config.baseUrl}/iso/oauth2/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "client_credentials",
        client_id: this.config.clientId,
        client_secret: this.config.clientSecret,
      }),
    });

    if (!response.ok) {
      throw new Error(
        `senhasegura auth failed: ${response.status} ${response.statusText}`,
      );
    }

    const data = (await response.json()) as {
      access_token: string;
      expires_in: number;
    };
    this.accessToken = data.access_token;
    // Refresh at expiry minus 60s — see SKILL.md Gotcha #2
    this.tokenExpiry = new Date(Date.now() + data.expires_in * 1000 - 60_000);
  }

  private async ensureAuth(): Promise<void> {
    if (
      !this.accessToken ||
      !this.tokenExpiry ||
      this.tokenExpiry < new Date()
    ) {
      await this.authenticate();
    }
  }

  async request(
    method: string,
    endpoint: string,
    body?: unknown,
  ): Promise<unknown> {
    await this.ensureAuth();
    const response = await fetch(`${this.config.baseUrl}${endpoint}`, {
      method,
      headers: {
        Authorization: `Bearer ${this.accessToken}`,
        "Content-Type": "application/json",
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!response.ok) {
      throw new Error(
        `senhasegura ${method} ${endpoint} failed: ${response.status} ${response.statusText}`,
      );
    }
    return response.json();
  }

  async releaseCustody(credentialId: string): Promise<void> {
    await this.request("DELETE", `/iso/pam/credential/custody/${credentialId}`);
  }
}

const requireEnv = (name: string): string => {
  const v = process.env[name];
  if (!v) throw new Error(`Missing required env var: ${name}`);
  return v;
};

const client = new SenhaseguraClient({
  baseUrl: requireEnv("SENHASEGURA_URL"),
  clientId: requireEnv("SENHASEGURA_CLIENT_ID"),
  clientSecret: requireEnv("SENHASEGURA_CLIENT_SECRET"),
});

const server = new Server(
  { name: "senhasegura-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "senhasegura_list_credentials",
      description: "List all credentials visible to this A2A authorization.",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "senhasegura_get_credential",
      description: "Get credential metadata by ID (no password).",
      inputSchema: {
        type: "object",
        properties: {
          id: { type: "string", description: "Credential ID" },
        },
        required: ["id"],
      },
    },
    {
      name: "senhasegura_get_password",
      description:
        "Retrieve the password for a credential. Custody is released automatically after retrieval.",
      inputSchema: {
        type: "object",
        properties: {
          credentialId: { type: "string", description: "Credential ID" },
        },
        required: ["credentialId"],
      },
    },
    {
      name: "senhasegura_list_ssh_keys",
      description: "List all SSH keys registered in PAM Core.",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "senhasegura_get_ssh_key",
      description: "Get an SSH key by ID (includes private key).",
      inputSchema: {
        type: "object",
        properties: {
          id: { type: "string", description: "SSH key ID" },
        },
        required: ["id"],
      },
    },
    {
      name: "senhasegura_rotate_ssh_key",
      description: "Trigger immediate rotation for an SSH key.",
      inputSchema: {
        type: "object",
        properties: {
          id: { type: "string", description: "SSH key ID" },
        },
        required: ["id"],
      },
    },
    {
      name: "senhasegura_dsm_list_secrets",
      description:
        "List secrets in DevOps Secret Manager, optionally filtered by application.",
      inputSchema: {
        type: "object",
        properties: {
          application: {
            type: "string",
            description: "Optional application filter",
          },
        },
      },
    },
    {
      name: "senhasegura_dsm_get_secret",
      description: "Get a DSM secret by identifier.",
      inputSchema: {
        type: "object",
        properties: {
          identifier: { type: "string", description: "Secret identifier" },
        },
        required: ["identifier"],
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const a = args as Record<string, string | undefined>;

  const text = (data: unknown) => ({
    content: [{ type: "text" as const, text: JSON.stringify(data, null, 2) }],
  });

  switch (name) {
    case "senhasegura_list_credentials": {
      return text(await client.request("GET", "/api/pam/credential"));
    }

    case "senhasegura_get_credential": {
      if (!a.id) throw new Error("id is required");
      return text(await client.request("GET", `/api/pam/credential/${a.id}`));
    }

    case "senhasegura_get_password": {
      const credentialId = a.credentialId;
      if (!credentialId) throw new Error("credentialId is required");
      try {
        return text(
          await client.request(
            "GET",
            `/iso/coe/senha?credentialId=${encodeURIComponent(credentialId)}`,
          ),
        );
      } finally {
        // Always release custody — see SKILL.md Gotcha #1
        await client.releaseCustody(credentialId).catch(() => {
          // Swallow release errors; the primary call result has already been returned.
          // Operators should monitor for orphaned custody via senhasegura's audit reports.
        });
      }
    }

    case "senhasegura_list_ssh_keys": {
      return text(await client.request("GET", "/api/pam/sshkey"));
    }

    case "senhasegura_get_ssh_key": {
      if (!a.id) throw new Error("id is required");
      return text(await client.request("GET", `/api/pam/sshkey/${a.id}`));
    }

    case "senhasegura_rotate_ssh_key": {
      if (!a.id) throw new Error("id is required");
      return text(
        await client.request("POST", `/api/pam/sshkey/${a.id}/rotate`),
      );
    }

    case "senhasegura_dsm_list_secrets": {
      const endpoint = a.application
        ? `/api/dsm/secret?application=${encodeURIComponent(a.application)}`
        : "/api/dsm/secret";
      return text(await client.request("GET", endpoint));
    }

    case "senhasegura_dsm_get_secret": {
      if (!a.identifier) throw new Error("identifier is required");
      return text(
        await client.request(
          "GET",
          `/api/dsm/secret/${encodeURIComponent(a.identifier)}`,
        ),
      );
    }

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
