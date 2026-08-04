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
| `type` | `string` | yes | AntiPerimeterXTask (the only supported variant — no ProxyLess for PerimeterX) |
| `websiteURL` | `string` | yes | Full URL of the PROTECTED parent page. NOT the PerimeterX challenge iframe URL (iframe.hsprotect.net / *.px-cdn.net) — those return ERROR_INVALID_PARAMS because the widget only renders inside the parent site's context. |
| `uuid` | `string` | no | Visitor `_pxvid` cookie value from the target page. Pre-seeded on the solver context before navigation so PerimeterX issues clearance tied to YOUR session. Strongly recommended for sites that enforce visitor binding. |
| `vid` | `string` | no | Visitor ID from `window._pxhc.vid` (sometimes distinct from uuid). Falls back to uuid when omitted. |
| `pxAppId` | `string` | no | PerimeterX tenant ID (e.g. PXzC5j78di). Visible in //client.perimeterx.net/<pxAppId>/main.min.js on the target page. |
| `_pxhd` | `string` | no | Hardened-device cookie value if the target site sets one alongside _pxvid. |


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
  "errorId":  0,
  "status":   "ready",
  "solution": { ... }
}
```

The `solution` object contains:

| Field | Type | Notes |
|-------|------|-------|
| `token` | `string` | Highest-priority cookie value (_px3 if present, else _px2, else _pxhd) |
| `cookies` | `array` | All _px* cookies in {name, value, domain, path} form for full session replay |
| `userAgent` | `string` | User-Agent used during solve — match this on subsequent requests |

### How to use the solution

Set ALL the returned cookies on your HTTP client and reuse the User-Agent, and replay through the SAME proxy you supplied at solve time — the cookies are bound to that IP. _px3 rotates every ~60 seconds — re-solve when it expires.

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

## Naming conventions

Field names are camelCase on the wire (`websiteURL`, `websiteKey`,
`proxyAddress`). Stick to that exactly when you build the JSON.
