# ExportChat Workflow

Export all messages from an MS Teams chat to a local JSON file for backup or analysis.

## Step 1: Gather Parameters

Collect source chat ID from user (parse from Teams URL if provided).

## Step 2: Verify Authentication

Same as MigrateChat Step 2.

## Step 3: Fetch All Messages

```
Load tool: mcp__teams-mcp__get_chat_messages
Call with:
  chatId: SOURCE_CHAT_ID
  fetchAll: true
  limit: 2000
  descending: true
  contentFormat: "markdown"
```

## Step 4: Save to File

If result is too large for MCP response, it's already saved to a file automatically.
Otherwise, save the JSON response to a user-specified path (default: `/tmp/teams_chat_export_YYYYMMDD.json`).

Include metadata:
```json
{
  "exportDate": "ISO timestamp",
  "chatId": "source chat ID",
  "totalMessages": N,
  "filteredMessages": M,
  "senders": ["list of unique senders"],
  "dateRange": { "earliest": "ISO", "latest": "ISO" },
  "messages": [...]
}
```

## Step 5: Summary

Report to user:
- Total messages exported
- Unique senders
- Date range
- File path
- Messages with attachments/images count
