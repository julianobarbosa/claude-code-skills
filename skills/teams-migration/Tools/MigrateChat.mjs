#!/usr/bin/env node

/**
 * MigrateChat.mjs — Bulk post messages to an MS Teams channel via Graph API.
 *
 * Usage:
 *   node MigrateChat.mjs --team TEAM_ID --channel CHANNEL_ID --messages /path/to/messages.json
 *
 * The messages JSON file should be an array of objects with:
 *   { from: "Sender Name", createdDateTime: "ISO string", content: "message body" }
 *
 * Features:
 *   - Reads MSAL token from ~/.teams-mcp-token-cache.json
 *   - Automatic token refresh via OAuth2 refresh_token grant
 *   - Rate limiting (429) with Retry-After
 *   - Progress tracking to /tmp/teams_migration_progress.json (resumable)
 *   - HTML formatting with sender attribution and localized timestamps
 */

import { readFileSync, writeFileSync } from 'fs';
import { homedir } from 'os';
import { join } from 'path';
import { parseArgs } from 'util';

// ── CLI Arguments ──────────────────────────────────────────────────

const { values } = parseArgs({
  options: {
    team:     { type: 'string', short: 't' },
    channel:  { type: 'string', short: 'c' },
    messages: { type: 'string', short: 'm' },
    progress: { type: 'string', short: 'p' },
    timezone: { type: 'string', default: 'America/Sao_Paulo' },
    locale:   { type: 'string', default: 'pt-BR' },
    delay:    { type: 'string', default: '100' },
  },
});

const TEAM_ID       = values.team;
const CHANNEL_ID    = values.channel;
const MESSAGES_PATH = values.messages;
const PROGRESS_PATH = values.progress || '/tmp/teams_migration_progress.json';
const TIMEZONE      = values.timezone || 'America/Sao_Paulo';
const LOCALE        = values.locale   || 'pt-BR';
const DELAY_MS      = parseInt(values.delay || '100', 10);

if (!TEAM_ID || !CHANNEL_ID || !MESSAGES_PATH) {
  console.error('Usage: node MigrateChat.mjs --team TEAM_ID --channel CHANNEL_ID --messages FILE');
  console.error('');
  console.error('Options:');
  console.error('  --team, -t       Destination team ID (required)');
  console.error('  --channel, -c    Destination channel ID (required)');
  console.error('  --messages, -m   Path to messages JSON file (required)');
  console.error('  --progress, -p   Path to progress file (default: /tmp/teams_migration_progress.json)');
  console.error('  --timezone       Timestamp timezone (default: America/Sao_Paulo)');
  console.error('  --locale         Timestamp locale (default: pt-BR)');
  console.error('  --delay          Delay between messages in ms (default: 100)');
  process.exit(1);
}

// ── Token Management ───────────────────────────────────────────────

const CACHE_PATH = join(homedir(), '.teams-mcp-token-cache.json');
const AUTH_PATH  = join(homedir(), '.msgraph-mcp-auth.json');

function getAccessToken() {
  const cache = JSON.parse(readFileSync(CACHE_PATH, 'utf8'));
  const atEntries = cache.AccessToken || {};
  for (const [, val] of Object.entries(atEntries)) {
    return val.secret;
  }
  throw new Error('No access token found in cache');
}

async function refreshToken() {
  const cache = JSON.parse(readFileSync(CACHE_PATH, 'utf8'));
  const rtEntries = cache.RefreshToken || {};
  let refreshSecret = null;
  for (const [, val] of Object.entries(rtEntries)) {
    refreshSecret = val.secret;
  }
  if (!refreshSecret) throw new Error('No refresh token found');

  const auth = JSON.parse(readFileSync(AUTH_PATH, 'utf8'));
  const clientId = auth.clientId;

  const acctEntries = cache.Account || {};
  let realm = '';
  for (const [, val] of Object.entries(acctEntries)) {
    realm = val.realm;
  }

  const body = new URLSearchParams({
    client_id: clientId,
    grant_type: 'refresh_token',
    refresh_token: refreshSecret,
    scope: 'https://graph.microsoft.com/.default offline_access',
  });

  const resp = await fetch(
    `https://login.microsoftonline.com/${realm}/oauth2/v2.0/token`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: body.toString(),
    }
  );

  if (!resp.ok) {
    const errText = await resp.text();
    throw new Error(`Token refresh failed: ${resp.status} ${errText}`);
  }

  const data = await resp.json();

  for (const [, val] of Object.entries(cache.AccessToken)) {
    val.secret = data.access_token;
    val.expires_on = String(Math.floor(Date.now() / 1000) + data.expires_in);
    val.cached_at = String(Math.floor(Date.now() / 1000));
  }
  if (data.refresh_token) {
    for (const [, val] of Object.entries(cache.RefreshToken)) {
      val.secret = data.refresh_token;
    }
  }
  writeFileSync(CACHE_PATH, JSON.stringify(cache, null, 2));
  return data.access_token;
}

// ── Graph API ──────────────────────────────────────────────────────

async function sendMessage(token, message, retryCount = 0) {
  const url = `https://graph.microsoft.com/v1.0/teams/${TEAM_ID}/channels/${encodeURIComponent(CHANNEL_ID)}/messages`;

  const resp = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      body: { contentType: 'html', content: message },
    }),
  });

  if (resp.status === 429) {
    const retryAfter = parseInt(resp.headers.get('Retry-After') || '10');
    console.log(`  Rate limited. Waiting ${retryAfter}s...`);
    await new Promise((r) => setTimeout(r, retryAfter * 1000));
    return sendMessage(token, message, retryCount + 1);
  }

  if (resp.status === 401 && retryCount === 0) {
    console.log('  Token expired, refreshing...');
    const newToken = await refreshToken();
    return sendMessage(newToken, message, retryCount + 1);
  }

  if (!resp.ok) {
    const errText = await resp.text();
    throw new Error(`Send failed: ${resp.status} ${errText}`);
  }

  return resp.json();
}

// ── Formatting ─────────────────────────────────────────────────────

function formatTimestamp(isoDate) {
  const d = new Date(isoDate);
  return d.toLocaleString(LOCALE, { timeZone: TIMEZONE });
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function markdownToHtml(content) {
  let html = content;
  html = html.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
  html = html.replace(/(?<![\/\w])_(.+?)_(?![\/\w])/g, '<i>$1</i>');
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1">');
  html = html.replace(/```([^`]+)```/gs, '<pre>$1</pre>');
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  html = html.replace(/\n/g, '<br>');
  return html;
}

// ── Main ───────────────────────────────────────────────────────────

async function main() {
  const messages = JSON.parse(readFileSync(MESSAGES_PATH, 'utf8'));

  let startIndex = 0;
  try {
    const progress = JSON.parse(readFileSync(PROGRESS_PATH, 'utf8'));
    startIndex = progress.lastPosted + 1;
    console.log(`Resuming from message ${startIndex} (${startIndex} already posted)`);
  } catch {
    console.log('Starting fresh migration');
  }

  let token = getAccessToken();
  const total = messages.length;
  let posted = startIndex;
  const errors = [];

  console.log(`Total messages to post: ${total - startIndex} (of ${total} total)`);
  console.log(`Destination: Team ${TEAM_ID}`);
  console.log(`Channel: ${CHANNEL_ID}`);
  console.log('');

  for (let i = startIndex; i < total; i++) {
    const msg = messages[i];
    const sender = msg.from;
    const timestamp = formatTimestamp(msg.createdDateTime);
    const content = msg.content;

    const formatted = `<b>${escapeHtml(sender)}</b> \u2014 <i>${timestamp}</i><br><br>${markdownToHtml(content)}`;

    try {
      await sendMessage(token, formatted);
      token = getAccessToken();
      posted++;

      writeFileSync(
        PROGRESS_PATH,
        JSON.stringify({ lastPosted: i, total, posted, errors: errors.length })
      );

      if (posted % 10 === 0 || i === total - 1) {
        console.log(`Progress: ${posted}/${total} (${Math.round((posted / total) * 100)}%)`);
      }

      await new Promise((r) => setTimeout(r, DELAY_MS));
    } catch (err) {
      console.error(`ERROR on message ${i} (from ${sender}): ${err.message}`);
      errors.push({ index: i, sender, error: err.message });

      writeFileSync(
        PROGRESS_PATH,
        JSON.stringify({
          lastPosted: i - 1,
          total,
          posted,
          errors: errors.length,
          errorDetails: errors,
        })
      );

      if (errors.length > 5) {
        console.error('Too many errors, stopping.');
        break;
      }
    }
  }

  console.log('');
  console.log(`Migration complete: ${posted}/${total} messages posted`);
  if (errors.length > 0) {
    console.log(`Errors: ${errors.length}`);
    for (const err of errors) {
      console.log(`  - Message ${err.index}: ${err.error}`);
    }
  }

  writeFileSync(
    PROGRESS_PATH,
    JSON.stringify(
      {
        lastPosted: posted - 1,
        total,
        posted,
        errors: errors.length,
        errorDetails: errors,
        completed: errors.length === 0,
        completedAt: new Date().toISOString(),
      },
      null,
      2
    )
  );
}

main().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
