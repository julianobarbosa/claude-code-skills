---
name: TeamsMigration
description: Migrate MS Teams chat content to channels or between chats. USE WHEN teams migration, migrate chat, copy messages, teams channel, move chat history, teams backup, chat to channel. SkillSearch('teamsmigration') for docs.
---

## Customization

**Before executing, check for user customizations at:**
`~/.claude/skills/PAI/USER/SKILLCUSTOMIZATIONS/TeamsMigration/`

If this directory exists, load and apply any PREFERENCES.md, configurations, or resources found there. These override default behavior. If the directory does not exist, proceed with skill defaults.

## Voice Notification

**You MUST send this notification BEFORE doing anything else when this skill is invoked.**

1. **Send voice notification**:
   ```bash
   curl -s -X POST http://localhost:8888/notify \
     -H "Content-Type: application/json" \
     -d '{"message": "Running the WORKFLOWNAME workflow in the TeamsMigration skill to ACTION"}' \
     > /dev/null 2>&1 &
   ```

2. **Output text notification**:
   ```
   Running the **WorkflowName** workflow in the **TeamsMigration** skill to ACTION...
   ```

# TeamsMigration

Migrate MS Teams meeting chat or group chat content to team channels, preserving sender attribution, timestamps, images, and attachments. Uses the `teams-mcp` MCP server for reading and the Microsoft Graph API directly for high-volume batch posting with automatic token refresh and rate limiting.

## Workflow Routing

| Workflow | Trigger | File |
|----------|---------|------|
| **MigrateChat** | "migrate chat", "copy chat to channel", "move messages" | `Workflows/MigrateChat.md` |
| **ExportChat** | "export chat", "backup chat", "download messages" | `Workflows/ExportChat.md` |

## Examples

**Example 1: Migrate a meeting chat to a team channel**
```
User: "Migrate the Teams meeting chat to the DevOps channel"
--> Invokes MigrateChat workflow
--> Verifies auth, fetches all messages with pagination
--> Filters system/deleted messages, reverses to chronological order
--> Posts each message with sender + timestamp attribution
--> Verifies count parity and spot-checks content
```

**Example 2: Export chat messages to a local file**
```
User: "Export all messages from our DevOps chat"
--> Invokes ExportChat workflow
--> Fetches all messages with full pagination
--> Saves to JSON file with metadata
```

## Quick Reference

- **MCP Server:** `@floriscornel/teams-mcp` (npm)
- **Auth file:** `~/.msgraph-mcp-auth.json`
- **Token cache:** `~/.teams-mcp-token-cache.json`
- **Auth command:** `npx @floriscornel/teams-mcp@latest authenticate`
- **Migration tool:** `Tools/MigrateChat.mjs` (Node.js, no dependencies)

## Key Learnings

- **Graph API `descending: false` not supported** -- fetch descending, reverse array
- **`download_message_hosted_content`** only works for channel messages, not chat messages
- **Token auto-refresh** via MSAL refresh token in `~/.teams-mcp-token-cache.json`
- **Rate limiting** handled by respecting `Retry-After` header on 429 responses
- **For bulk posting (50+ messages)** use `Tools/MigrateChat.mjs` directly via Graph API instead of MCP tool calls
- **Account must have Teams license** -- `Chat.*` endpoints fail without it (403)
