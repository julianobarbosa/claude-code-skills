#!/usr/bin/env bash
# YouTubeSearch — search YouTube via yt-dlp and output structured results
set -euo pipefail

# Defaults
QUERY=""
COUNT=20
MONTHS=6

usage() {
  echo "Usage: yt-search.sh <query> [--count N] [--months N]"
  echo "  query     Search terms (required)"
  echo "  --count   Number of results (default: 20)"
  echo "  --months  Filter to last N months (default: 6)"
  exit 1
}

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --count)  COUNT="$2"; shift 2 ;;
    --months) MONTHS="$2"; shift 2 ;;
    --help|-h) usage ;;
    *)
      if [[ -z "$QUERY" ]]; then
        QUERY="$1"
      else
        QUERY="$QUERY $1"
      fi
      shift
      ;;
  esac
done

[[ -z "$QUERY" ]] && usage

# Calculate date cutoff (YYYYMMDD) for post-filtering
if [[ "$(uname)" == "Darwin" ]]; then
  DATE_CUTOFF=$(date -v-"${MONTHS}m" +%Y%m%d)
else
  DATE_CUTOFF=$(date -d "-${MONTHS} months" +%Y%m%d)
fi

# Human-readable number formatting
format_number() {
  local n="$1"
  if [[ -z "$n" || "$n" == "null" || "$n" == "None" ]]; then
    echo "N/A"
    return
  fi
  if (( n >= 1000000000 )); then
    printf "%.1fB" "$(echo "scale=1; $n / 1000000000" | bc)"
  elif (( n >= 1000000 )); then
    printf "%.1fM" "$(echo "scale=1; $n / 1000000" | bc)"
  elif (( n >= 1000 )); then
    printf "%.1fK" "$(echo "scale=1; $n / 1000" | bc)"
  else
    echo "$n"
  fi
}

# Format duration from seconds
format_duration() {
  local secs="$1"
  if [[ -z "$secs" || "$secs" == "null" || "$secs" == "None" ]]; then
    echo "N/A"
    return
  fi
  local h=$(( secs / 3600 ))
  local m=$(( (secs % 3600) / 60 ))
  local s=$(( secs % 60 ))
  if (( h > 0 )); then
    printf "%d:%02d:%02d" "$h" "$m" "$s"
  else
    printf "%d:%02d" "$m" "$s"
  fi
}

# Format upload date YYYYMMDD -> YYYY-MM-DD
format_date() {
  local d="$1"
  if [[ -z "$d" || "$d" == "null" || ${#d} -lt 8 ]]; then
    echo "N/A"
    return
  fi
  echo "${d:0:4}-${d:4:2}-${d:6:2}"
}

echo ""
echo "============================================================"
echo "  YouTube Search: \"$QUERY\""
echo "  Results: up to $COUNT | Period: last $MONTHS months"
echo "============================================================"
echo ""

# Fetch more results than needed to allow for date filtering
# yt-dlp's --dateafter doesn't work with search, so we filter manually
FETCH_COUNT=$(( COUNT * 2 ))
if (( FETCH_COUNT < 30 )); then
  FETCH_COUNT=30
fi

# yt-dlp outputs multi-line JSON; compact to one JSON object per line
RESULTS=$(yt-dlp \
  "ytsearch${FETCH_COUNT}:${QUERY}" \
  --dump-json \
  --no-download \
  --no-warnings \
  2>/dev/null | jq -c '.' || true)

if [[ -z "$RESULTS" ]]; then
  echo "No results found."
  exit 0
fi

INDEX=0
while IFS= read -r line; do
  # Date filter: skip videos older than cutoff
  UPLOAD_DATE=$(echo "$line" | jq -r '.upload_date // empty')
  if [[ -n "$UPLOAD_DATE" && "$UPLOAD_DATE" < "$DATE_CUTOFF" ]]; then
    continue
  fi

  INDEX=$((INDEX + 1))
  if (( INDEX > COUNT )); then
    break
  fi

  TITLE=$(echo "$line" | jq -r '.title // "N/A"')
  CHANNEL=$(echo "$line" | jq -r '.channel // .uploader // "N/A"')
  SUBS=$(echo "$line" | jq -r '.channel_follower_count // empty')
  VIEWS=$(echo "$line" | jq -r '.view_count // empty')
  DURATION=$(echo "$line" | jq -r '.duration // empty')
  URL=$(echo "$line" | jq -r '.webpage_url // .url // "N/A"')

  SUBS_FMT=$(format_number "${SUBS:-}")
  VIEWS_FMT=$(format_number "${VIEWS:-}")
  DURATION_FMT=$(format_duration "${DURATION:-}")
  DATE_FMT=$(format_date "${UPLOAD_DATE:-}")

  # Engagement ratio
  if [[ -n "$SUBS" && "$SUBS" != "null" && "$SUBS" != "0" && -n "$VIEWS" && "$VIEWS" != "null" ]]; then
    RATIO=$(printf "%.2f" "$(echo "scale=4; $VIEWS / $SUBS" | bc)")
    RATIO_FMT="${RATIO}x"
  else
    RATIO_FMT="N/A"
  fi

  echo "  #${INDEX}"
  echo "  Title:        $TITLE"
  echo "  Channel:      $CHANNEL"
  echo "  Subscribers:  $SUBS_FMT"
  echo "  Views:        $VIEWS_FMT"
  echo "  Duration:     $DURATION_FMT"
  echo "  Uploaded:     $DATE_FMT"
  echo "  Engagement:   $RATIO_FMT (views/subs)"
  echo "  URL:          $URL"
  echo ""
  echo "------------------------------------------------------------"
  echo ""
done <<< "$RESULTS"

echo "  Search complete."
