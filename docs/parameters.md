# Parameters reference — PerimeterX / HUMAN Security

Every field you can pass to `POST /createTask` for this task type.

## Envelope

```json
{
  "clientKey": "capzy_xxxxxxxxxxxxxxxxxxxxxxxx",
  "task": { ... }
}
```

| Field        | Required | Notes                                                       |
|--------------|:--------:|-------------------------------------------------------------|
| `clientKey`  | yes      | Your Capzy API key. Starts with `capzy_`. Find it at [capzy.ai/dashboard/api-keys](https://capzy.ai/dashboard/api-keys). |
| `task`       | yes      | The task object — see below.                                |

## Task object

### Required + optional fields

| Field | Type | Required | Notes |
|-------|------|:--------:|-------|
| `type` | `string` | yes | `AntiPerimeterXTask` — the only supported variant. **There is no `AntiPerimeterXTaskProxyLess`.** PerimeterX clearance cookies (`_px3` / `_px2` / `_pxhd`) are cryptographically bound to the IP they were issued to, so the solve MUST happen on the same proxy your downstream session uses. |
| `websiteURL` | `string` | yes | Full URL of the **PROTECTED parent page** (the page the user is trying to access). **NOT the PerimeterX challenge-iframe URL** — passing `iframe.hsprotect.net` / `*.px-cdn.net` will return `ERROR_INVALID_PARAMS` because the widget only renders inside the parent site's context. |
| `uuid` | `string` | recommended | Visitor `_pxvid` cookie value from the target page (UUID format). When provided, we pre-seed it on the solver's browser context **before navigation** so PerimeterX mints a clearance cookie tied to YOUR visitor session, not a fresh one. **Strongly recommended** for sites that enforce session-binding (Microsoft signup, EA, retail signups, etc.) — without it the token may be rejected when your client replays. Capture from DevTools → Application → Cookies → `_pxvid` on the target page. |
| `vid` | `string` | optional | Visitor ID from `window._pxhc.vid` on the parent page. Often equals `uuid` — pass separately only when they're distinct values. If you pass `uuid` and not `vid`, we use `uuid` for both. |
| `pxAppId` | `string` | optional | PerimeterX tenant ID (e.g. `PXzC5j78di`). Visible in the api.js URL on the target page: `//client.perimeterx.net/<pxAppId>/main.min.js`. Used for diagnostics. |
| `_pxhd` | `string` | optional | Hardened-device cookie value if the target site sets one alongside `_pxvid`. |


### Proxy fields — **required**

PerimeterX is IP-bound: your proxy must be supplied on every call. Use a
sticky session so the same IP can be reused for both the solve and your
downstream HTTP client.

| Field | Type | Required | Notes |
|-------|------|:--------:|-------|
| `proxyType` | `string` | **yes** | `http` / `https` / `socks4` / `socks5` |
| `proxyAddress` | `string` | **yes** | IP or hostname of your proxy. Residential / mobile / static-ISP only — datacenter IPs fail PerimeterX's IP-trust scoring. |
| `proxyPort` | `integer` | **yes** | Port number of your proxy |
| `proxyLogin` | `string` | no | Omit if your proxy doesn't require auth |
| `proxyPassword` | `string` | no | Omit if your proxy doesn't require auth |


## Response

### `POST /createTask` success

```json
{
  "errorId": 0,
  "taskId":  "12345"
}
```

### `POST /getTaskResult` while processing

```json
{
  "errorId": 0,
  "status":  "processing"
}
```

### `POST /getTaskResult` when ready

```json
{
  "errorId": 0,
  "status":  "ready",
  "solution": {
    "token": "abcdef1234567890.xyz789.abc...",
    "cookie": "_px3=abcdef1234567890.xyz789.abc...; _pxhd=hardened_device_cookie",
    "cookies": [
      { "name": "_px3",   "value": "abcdef1234567890.xyz789.abc...",       "domain": ".example.com", "path": "/" },
      { "name": "_pxvid", "value": "aeaa41ad-53c7-11f1-933e-72f891b6838a", "domain": ".example.com", "path": "/" },
      { "name": "_pxhd",  "value": "hardened_device_cookie_value",         "domain": ".example.com", "path": "/" }
    ],
    "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "ipBound": true,
    "challengePresented": true,
    "holdDurationSec": 9.42,
    "holdStrategy": "challengeTime",
    "challengeTimeMs": 9100,
    "collectorEvents": [
      { "url": "https://collector-PXzC5j78di.perimeterx.net/api/v2/collector/s2s", "status": 200, "body_excerpt": "{\"do\":[]}", "at": 12.3 }
    ],
    "uuid": "aeaa41ad-53c7-11f1-933e-72f891b6838a",
    "vid":  "aeaa41ad-53c7-11f1-933e-72f891b6838a"
  }
}
```

| Field | Type | Notes |
|-------|------|-------|
| `token` | `string` | Highest-priority cookie value alone (_px3 if present, else _px2, else _pxhd). Use when you only need the proof string. |
| `cookie` | `string` | Ready-to-paste `Cookie:` header value with every _px* cookie joined. Domain intentionally omitted — it's a header value, not a jar entry, so it ships to whichever URL you're calling. |
| `cookies` | `array` | Structured `{name, value, domain, path}` array for customers building their own cookie jar. |
| `userAgent` | `string` | User-Agent used during solve — must match on every replay request (clearance is UA-bound). |
| `ipBound` | `boolean` | Always `true` for PerimeterX. Flags that the proof is tied to the solving IP, so replays MUST come through the same proxy you supplied at solve time. |
| `challengePresented` | `boolean` | `true` if the **Hold Captcha** (press-and-hold widget, officially "HUMAN Challenge") rendered and we held it. `false` if our fingerprint passed silently before PerimeterX escalated. Both cases produce valid clearance cookies. |
| `holdDurationSec` | `number` | Seconds we held the press-and-hold button (`8.5`–`11.0`, randomized per solve). `0` when `challengePresented` is `false`. |
| `holdStrategy` | `string` | `challengeTime` if we read PX's server-supplied hold duration from the bundle, `fallback-window` if we used the community-tuned 8.5–11s window. |
| `challengeTimeMs` | `number \| null` | The actual server-supplied hold duration (ms) when `holdStrategy = challengeTime`. `null` on the fallback path. |
| `collectorEvents` | `array` | POSTs to `collector-*.perimeterx.net/api/v[12]/collector/*` observed during the solve. Each entry: `{url, status, body_excerpt, at}`. PX fires these after press completion; the response is the per-solve "press accepted / rejected" signal. |
| `uuid` | `string` | The `_pxvid` visitor identifier PX bound the clearance to. **Only present when `challengePresented = true`.** The Hold Captcha mints `_px3` BOUND to this visitor — `_px3` + `_pxvid` + `_pxhd` are validated as a triple on every downstream request, so the customer's replay MUST use the same `_pxvid` for the clearance to validate. Pass it back as the `uuid` task param on subsequent solves to keep the visitor consistent. |
| `vid` | `string` | Secondary visitor identifier (`window._pxhc.vid`). Sometimes set separately by the PX bundle, often identical to `uuid`. **Only present when `challengePresented = true`.** Pin alongside `uuid` for sites that enforce a separate vid. |

### How to use the solution

Three flavours of the same proof — pick whichever fits your client.

**Drop-in** (`requests` / `httpx`) — easiest:

```python
headers = {
    "Cookie": solution["cookie"],
    "User-Agent": solution["userAgent"],
}
resp = requests.get(target_url, headers=headers, proxies=your_proxy)
```

**Structured** — when you're building a `CookieJar`:

```python
for c in solution["cookies"]:
    session.cookies.set(c["name"], c["value"])
```

**Token-only** — when you just need the proof string:

```python
headers = {"Cookie": f"_px3={solution['token']}"}
```

Replay MUST come through the same proxy you supplied at solve time, with the same User-Agent. `_px3` rotates every ~60 seconds on newer deployments — re-solve when it expires.

### Error

```json
{
  "errorId":          1,
  "errorCode":        "ERROR_KEY_DOES_NOT_EXIST",
  "errorDescription": "Invalid API key"
}
```

`errorId` is `0` on success, `1` on any error. The `errorCode` is the
stable machine-readable identifier. Common codes:

- `ERROR_KEY_DOES_NOT_EXIST` — bad API key
- `ERROR_NO_BALANCE` — account balance below the cost of this task
- `ERROR_INVALID_PARAMS` — missing required field or malformed value
- `ERROR_MAX_TASKS_REACHED` — concurrent in-flight cap reached (default 30)
- `ERROR_RATE_LIMITED` — too many createTask calls per second
- `ERROR_TIMEOUT` — solve took longer than the cap (auto-refunded)
- `ERROR_CAPTCHA_UNSOLVABLE` — solver gave up (auto-refunded)
- `ERROR_INVALID_PARAMS` — most commonly returned when `websiteURL` is the PerimeterX challenge-iframe URL (`iframe.hsprotect.net` / `*.px-cdn.net`) instead of the parent protected page. Refunded.

## Naming conventions

Field names are camelCase on the wire (`websiteURL`, `websiteKey`,
`proxyAddress`). Stick to that exactly when you build the JSON.
