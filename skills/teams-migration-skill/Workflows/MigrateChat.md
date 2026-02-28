# MigrateChat Workflow

Migrate all messages from an MS Teams meeting chat (or group chat) to a team channel with full sender attribution and timestamp preservation.

## Prerequisites

- `teams-mcp` MCP server connected and authenticated
- Account with Teams license (Chat API requires it)
- Source chat ID and destination team/channel IDs

## Step 1: Gather Parameters

Use `AskUserQuestion` to collect:

1. **Source chat ID** -- Extract from Teams URL: `19:meeting_...@thread.v2`
2. **Destination team ID** -- Extract from Teams URL: `groupId=...`
3. **Destination channel ID** -- Either known or discover via `list_channels`

If user provides Teams URLs, parse them:
- Chat URL: `https://teams.microsoft.com/l/chat/19:meeting_...@thread.v2/conversations?context=...`
- Team URL: `https://teams.microsoft.com/l/team/19%3A...@thread.tacv2/conversations?groupId=TEAM_ID&tenantId=TENANT_ID`

## Step 2: Verify Authentication

```
Load tool: mcp__teams-mcp__auth_status
Call: mcp__teams-mcp__auth_status
```

- Confirm account has Teams license
- If auth fails or wrong account: `npx @floriscornel/teams-mcp@latest authenticate`

**CRITICAL:** If account lacks Teams license, Chat API endpoints return 403. Channel endpoints may still work. Must re-auth with a licensed account.

## Step 3: Identify Destination Channel

If channel ID not provided:
```
Load tool: mcp__teams-mcp__list_channels
Call with: teamId = DESTINATION_TEAM_ID
```

Present channels to user if multiple exist. Default to "General" if only one.

## Step 4: Fetch All Source Messages

```
Load tool: mcp__teams-mcp__get_chat_messages
Call with:
  chatId: SOURCE_CHAT_ID
  fetchAll: true
  limit: 2000
  descending: true    # IMPORTANT: ascending NOT supported by Graph API
  contentFormat: "markdown"
```

**CRITICAL LEARNINGS:**
- `descending: false` returns error: `QueryOptions to order by 'CreatedDateTime' in 'Ascending' direction is not supported`
- Always fetch descending and **reverse the array** for chronological posting
- Result may be too large for MCP response -- saved to file automatically
- Parse from saved file using `python3` or `node`

## Step 5: Process Messages

```python
# Filter and prepare messages
filtered = [m for m in messages if m.get('from') and m.get('content','').strip()]
# 'from' field is absent on system messages
# Empty content = system events (join/leave)

filtered.reverse()  # Chronological order (oldest first)
```

**Filtering rules:**
- Remove messages without `from` field (system messages)
- Remove messages with empty `content` (system events)
- Optionally remove deleted messages (`deletedDateTime != null`)
- Ask user about system messages if unsure

## Step 6: Post Messages via Graph API

**For 50+ messages, use `Tools/MigrateChat.mjs` directly instead of individual MCP calls.**

```bash
# Copy tool to /tmp, configure constants, and run
node /path/to/Tools/MigrateChat.mjs
```

The tool handles:
- MSAL token from `~/.teams-mcp-token-cache.json`
- Automatic token refresh via refresh token
- Rate limiting (429 responses with Retry-After)
- Progress tracking to `/tmp/teams_migration_progress.json`
- Resume from last successful post on restart

**Message format (HTML for Graph API):**
```html
<b>SENDER_NAME</b> -- <i>TIMESTAMP_LOCALIZED</i><br><br>MESSAGE_CONTENT
```

**For small batches (<50 messages), use MCP directly:**
```
Load tool: mcp__teams-mcp__send_channel_message
Call with:
  teamId: DESTINATION_TEAM_ID
  channelId: DESTINATION_CHANNEL_ID
  format: "markdown"
  message: "**Sender** -- _Timestamp_\n\nContent"
```

## Step 7: Verify Migration

1. **Count check:** Source filtered count == destination posted count
2. **Spot-check:** Read 5-10 messages from destination via `get_channel_messages`
3. **Source integrity:** Confirm source chat still readable (read-only operations only)

## Edge Cases

| Case | Handling |
|------|----------|
| Messages with images | Image URLs preserved in markdown. `imageUrl` param for MCP, `<img>` for Graph API |
| OneDrive/SharePoint files | Links preserved as-is (no re-upload) |
| Token expiration mid-migration | Auto-refreshed by `MigrateChat.mjs` using MSAL refresh token |
| Rate limiting (429) | Respect `Retry-After` header, retry automatically |
| Very large chats (2000+) | `fetchAll: true` handles pagination via `@odata.nextLink` |
| MCP server restart needed | `/mcp` in Claude Code, then new session for tool re-registration |
| Sensitive content (passwords) | Ask user before posting -- flag potential credentials |
| @mentions in source | Preserved as text in message body (not functional @mentions in destination) |
