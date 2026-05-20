#!/usr/bin/env bash
#
# Solve PerimeterX / HUMAN Security with Capzy — pure curl + jq.
#
# Cost:   from $0.001 per solve (flat)
# Speed:  ~10 seconds median
#
# Requires: curl, jq (brew install jq / apt install jq)
#
# PerimeterX clearance cookies (_px3 / _px2 / _pxhd) are IP-bound — your
# proxy is REQUIRED, there is no ProxyLess variant. Use the SAME sticky
# proxy your downstream HTTP client will replay the cookies on.
#
# Run with:
#   export CAPZY_KEY="capzy_xxxxxxxxxxxxxxxxxxxxxxxx"
#   export PROXY_HOST="gw.your-provider.com"
#   export PROXY_PORT="10000"
#   export PROXY_USER="your-user"
#   export PROXY_PASS="your-pass"
#   bash basic.sh

set -euo pipefail

API_BASE="${API_BASE:-https://api.capzy.ai}"
: "${CAPZY_KEY:?set CAPZY_KEY in your env (grab one at https://capzy.ai/auth/register)}"
: "${PROXY_HOST:?set PROXY_HOST (sticky residential / mobile / static-ISP — datacenter fails PerimeterX)}"
: "${PROXY_PORT:?set PROXY_PORT}"
PROXY_USER="${PROXY_USER:-}"
PROXY_PASS="${PROXY_PASS:-}"

# Customize the task body to match the target site you're solving.
# Proxy fields are mandatory for PerimeterX.
TASK=$(jq -n \
  --arg url "https://example.com" \
  --arg ph "$PROXY_HOST" \
  --argjson pp "$PROXY_PORT" \
  --arg pu "$PROXY_USER" \
  --arg ppw "$PROXY_PASS" \
  '{
    type: "AntiPerimeterXTask",
    websiteURL: $url,
    proxyType: "http",
    proxyAddress: $ph,
    proxyPort: $pp,
  } + (if $pu == "" then {} else { proxyLogin: $pu, proxyPassword: $ppw } end)')

# ─── 1) Create the task ───────────────────────────────────────────────
echo "creating task..."
CREATE_RESP=$(curl -sS -X POST "${API_BASE}/createTask" \
  -H 'Content-Type: application/json' \
  -d "{\"clientKey\":\"${CAPZY_KEY}\",\"task\":${TASK}}")

ERROR_ID=$(echo "$CREATE_RESP" | jq -r '.errorId // 0')
if [ "$ERROR_ID" != "0" ]; then
  echo "createTask failed:" >&2
  echo "$CREATE_RESP" | jq . >&2
  exit 1
fi

TASK_ID=$(echo "$CREATE_RESP" | jq -r '.taskId')
echo "created task ${TASK_ID}"

# ─── 2) Poll until ready ──────────────────────────────────────────────
DEADLINE=$(( $(date +%s) + 120 ))
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  RESULT=$(curl -sS -X POST "${API_BASE}/getTaskResult" \
    -H 'Content-Type: application/json' \
    -d "{\"clientKey\":\"${CAPZY_KEY}\",\"taskId\":\"${TASK_ID}\"}")

  STATUS=$(echo "$RESULT" | jq -r '.status // "unknown"')
  if [ "$STATUS" = "ready" ]; then
    echo "$RESULT" | jq '.solution'
    # ─── How to use the result ────────────────────────────────────
    # `solution.cookie` is a ready-to-paste Cookie: header string.
    # Pull it with jq and replay through your SAME sticky proxy:
    #
    #   COOKIE=$(echo "$RESULT" | jq -r '.solution.cookie')
    #   UA=$(echo "$RESULT" | jq -r '.solution.userAgent')
    #   curl -x "$PROXY" -H "Cookie: $COOKIE" -H "User-Agent: $UA" "$TARGET_URL"
    exit 0
  fi
  if [ "$STATUS" != "processing" ]; then
    echo "unexpected status: $STATUS" >&2
    echo "$RESULT" | jq . >&2
    exit 1
  fi
  sleep 2
done

echo "solve took longer than 120s — unusual; check https://capzy.ai/status" >&2
exit 1
