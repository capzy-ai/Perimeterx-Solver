<div align="center">

<img src="https://capzy.ai/capzy-logo.svg" alt="Capzy" width="220" />

# PerimeterX / HUMAN Security Solver

**Solves the Hold Captcha (HUMAN Challenge press-and-hold). Returns _px3 / _px2 / _pxhd cookies.**

[![Solve cost](https://img.shields.io/badge/from-%240.001%20%2F%20solve-%23ff5d2a)](https://capzy.ai/pricing)
[![Speed](https://img.shields.io/badge/avg%20solve-~10%20seconds-%2322c55e)](https://capzy.ai/products/perimeterx)
[![Uptime](https://img.shields.io/badge/uptime-99.9%25-%2322c55e)](https://capzy.ai/status)
[![License: MIT](https://img.shields.io/badge/license-MIT-%23ff5d2a)](LICENSE)

[Live Demo](https://capzy.ai/products/perimeterx/demo) ·
[Get Free $0.10 Credit](https://capzy.ai/auth/register) ·
[Dashboard](https://capzy.ai/dashboard) ·
[Full Docs](https://capzy.ai/docs) ·
[Pricing](https://capzy.ai/pricing)

</div>

---

## What this repo is

Copy-pasteable examples for solving **PerimeterX / HUMAN Security** through the
[Capzy](https://capzy.ai) HTTP API — no SDK required. Pure curl, Python,
and Node.js using the raw API. Easy to read, easy to port, easy to audit.

## What is PerimeterX / HUMAN Security?

PerimeterX (now HUMAN Security) is a bot protection platform that scores requests on IP trust, browser fingerprint, TLS/JA3, and on-page behavior. The visible CAPTCHA is a press-and-hold button; the cookie hierarchy is _px3 (newest, ~60s expiry) > _px2 > _pxhd. Capzy returns all of them.

## Why Capzy

- **From $0.001 per solve.** Flat pricing — no tiers, no retainer, no monthly minimum.
- **~10 seconds average solve.** Production-grade speed.
- **Drop-in compatible.** `createTask` / `getTaskResult` protocol. If your code already speaks the standard solver shape, swap the host to `https://api.capzy.ai`.
- **$0.10 in real credits on sign-up.** No card. 100 free test solves.

## Pricing

| Task type | When to use | Cost / solve |
|-----------|-------------|-------------:|
| `AntiPerimeterXTask`                       | The only supported variant — your residential / mobile / ISP proxy required | **$0.001**   |

> **There is no `AntiPerimeterXTaskProxyLess`.** PerimeterX clearance
> cookies (`_px3` / `_px2` / `_pxhd`) are cryptographically bound to the
> IP they were issued to. A token solved on our pool IP would be
> rejected the moment your downstream client called the protected
> endpoint from your own IP. So we don't offer a ProxyLess variant for
> PerimeterX — supply your own sticky proxy (the same one your
> downstream session will use) and we'll mint the token on that IP.

## 60-second quickstart

```bash
# 1. Sign up — gets you $0.10 in free credits (100 solves)
open https://capzy.ai/auth/register

# 2. Copy your API key from the dashboard
#    https://capzy.ai/dashboard/api-keys

# 3. Run any example
export CAPZY_KEY="capzy_..."
bash examples/curl/basic.sh
```

Minimal Python:

```python
import requests, time

KEY = "capzy_xxxxxxxxxxxxxxxxxxxxxxxx"

# 1) Create the task — proxy is REQUIRED for PerimeterX.
#    Use the SAME proxy your downstream session will be on so the
#    issued _px3 / _px2 cookie validates when you replay it.
created = requests.post("https://api.capzy.ai/createTask", json={
    "clientKey": KEY,
    "task": {
        "type": "AntiPerimeterXTask",
        "websiteURL": "https://example.com",
        "proxyType": "http",
        "proxyAddress": "gw.your-provider.com",
        "proxyPort": 10000,
        "proxyLogin": "your-user",
        "proxyPassword": "your-pass",
    },
}).json()
task_id = created["taskId"]

# 2) Poll until ready
while True:
    result = requests.post("https://api.capzy.ai/getTaskResult", json={
        "clientKey": KEY, "taskId": task_id,
    }).json()
    if result["status"] == "ready":
        break
    time.sleep(2)

print(result["solution"])
```

That's the whole protocol. The rest of this repo is just that, in every
language we could think of.

## Pick your language

| Language        | Example                                       |
|-----------------|-----------------------------------------------|
| **curl / bash** | [`examples/curl/basic.sh`](examples/curl/basic.sh)    |
| **Python**      | [`examples/python/basic.py`](examples/python/basic.py) |
| **Node.js**     | [`examples/nodejs/basic.js`](examples/nodejs/basic.js) |

See [`examples/README.md`](examples/README.md) for setup details.

## Request envelope

```json
{
  "clientKey": "capzy_xxxxxxxxxxxxxxxxxxxxxxxx",
  "task": {
    "type": "AntiPerimeterXTask",
    "websiteURL": "https://example.com",
    "proxyType": "http",
    "proxyAddress": "gw.your-provider.com",
    "proxyPort": 10000,
    "proxyLogin": "your-user",
    "proxyPassword": "your-pass"
  }
}
```

| Field | Type | Required | Notes |
|-------|------|:--------:|-------|
| `type` | `string` | yes | `AntiPerimeterXTask` (the only supported variant — no ProxyLess) |
| `websiteURL` | `string` | yes | Full URL of the protected page |
| `proxyType` | `string` | **yes** | `http` / `https` / `socks4` / `socks5` |
| `proxyAddress` | `string` | **yes** | IP or hostname of your proxy |
| `proxyPort` | `integer` | **yes** | Port number of your proxy |
| `proxyLogin` | `string` | no | Omit if your proxy doesn't require auth |
| `proxyPassword` | `string` | no | Omit if your proxy doesn't require auth |

Use a **sticky** proxy session so the IP doesn't rotate between the
solve and your downstream call. Residential / mobile / static ISP all
work; datacenter IPs fail PerimeterX's IP-trust scoring every time.

Full reference in [`docs/parameters.md`](docs/parameters.md).

## Response shape

When the task is ready (`status: "ready"`), `solution` contains:

| Field | Type | Notes |
|-------|------|-------|
| `token` | `string` | Highest-priority cookie value alone (_px3 if present, else _px2, else _pxhd). Use when you only need the proof string. |
| `cookie` | `string` | Ready-to-paste `Cookie:` header value (`_px3=...; _pxhd=...; _pxvid=...`). Domain intentionally omitted — it's a header value, not a jar entry. |
| `cookies` | `array` | Structured `{name, value, domain, path}` array for customers building their own cookie jar. |
| `userAgent` | `string` | User-Agent used during solve — must match on every replay request (clearance is UA-bound). |
| `ipBound` | `boolean` | Always `true` for PerimeterX — the proof is tied to the solving IP; replays must come through the same proxy. |
| `challengePresented` | `boolean` | `true` if the **Hold Captcha** (press-and-hold) widget rendered and we held it. `false` if our fingerprint passed silently. Either way the cookies are valid — this flag just tells you which code path minted them. |
| `holdDurationSec` | `number` | Seconds we held the press-and-hold button (`8.5`–`11.0`). `0` when `challengePresented` is `false`. |
| `holdStrategy` | `string` | `challengeTime` if we read PX's server-supplied hold duration from the bundle, `fallback-window` if we used the community-tuned 8.5–11s window. Diagnostic for monitoring per-deployment hook-hit rate. |
| `challengeTimeMs` | `number \| null` | The actual server-supplied hold duration in milliseconds when `holdStrategy = challengeTime`. `null` on the fallback path. |
| `collectorEvents` | `array` | POSTs to `collector-*.perimeterx.net/api/v[12]/collector/*` observed during the solve. Each entry: `{url, status, body_excerpt, at}`. PX fires these after press completion; the response says whether the press was accepted. Diagnostic — useful when a solve looks successful but downstream replay fails. |
| `uuid` | `string` | The `_pxvid` visitor identifier PX bound the clearance to. **Only present when `challengePresented = true`.** The Hold Captcha mints `_px3` BOUND to this visitor — `_px3` + `_pxvid` + `_pxhd` are validated as a triple on every downstream request, so the customer's replay MUST use the same `_pxvid` for the clearance to validate. Pass it back in via the `uuid` task param on subsequent solves to keep the visitor consistent. |
| `vid` | `string` | Secondary visitor identifier (`window._pxhc.vid` — sometimes set separately by the PX bundle, often identical to `uuid`). **Only present when `challengePresented = true`.** Pin alongside `uuid` for sites that enforce a separate vid via their PX integration. |

### Example

```json
{
  "errorId": 0,
  "status": "ready",
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

### How to use the result

Three flavours of the same proof are returned — pick whichever fits your client:

```python
# Drop-in (`requests` / `httpx`):
headers = {
    "Cookie": solution["cookie"],
    "User-Agent": solution["userAgent"],
}
resp = requests.get(target_url, headers=headers, proxies=your_proxy)

# Or set ALL structured cookies on a jar:
for c in solution["cookies"]:
    session.cookies.set(c["name"], c["value"])

# Or token-only (when you just need the proof):
headers = {"Cookie": f"_px3={solution['token']}"}
```

Replay MUST come through the same proxy you supplied at solve time, with the same User-Agent. `_px3` rotates every ~60 seconds on newer deployments — re-solve when it expires.

## Features

- **Solves Hold Captcha** (HUMAN Challenge) — Bezier-curve approach, 8.5–11s hold, cursor micro-jitter during the hold window
- Returns _px3 (priority) → _px2 → _pxhd with full _px* cookie set
- Ready-to-paste `cookie` header string **plus** structured `cookies` array
- `challengePresented` field tells you whether the press-and-hold widget actually rendered, or whether the cookies came from a silent fingerprint pass
- User-Agent capture for session continuity

## FAQ

**Why no ProxyLess variant?** PerimeterX `_px3` / `_px2` / `_pxhd` clearance cookies are cryptographically tied to the IP they were issued to. If we solved on our pool IP, your downstream request from your own IP would be rejected. So PerimeterX only ships in proxy-required form — your residential / mobile / ISP proxy mints the token directly. Other captchas (Turnstile, hCaptcha, GeeTest, reCAPTCHA v2 base) aren't IP-bound and DO have ProxyLess variants on Capzy.

**What kind of proxy works?** Residential, mobile, or static ISP — all fine. Datacenter proxies will fail because PerimeterX scores IP trust as a primary signal and DC ranges are well-known. Use a sticky session (~5-10 min stickiness) so the same IP can be reused for both the solve and your downstream call.

**Why does _px3 expire so fast?** Newer high-security deployments rotate _px3 every ~60 seconds. Re-solve when it expires, or keep the same sticky proxy across solves so consecutive _px3 mints chain cleanly.

## What you'll need

- A Capzy API key — [sign up](https://capzy.ai/auth/register) (free, $0.10 credit).
- Network access to `https://api.capzy.ai`.

## Other captcha types

Capzy solves 25+ captcha types. Full catalog at
[capzy.ai/pricing](https://capzy.ai/pricing). Each type has its own
solver repo on [github.com/capzy-ai](https://github.com/capzy-ai).

## License

[MIT](LICENSE).

---

<div align="center">

**[Sign up for free credits →](https://capzy.ai/auth/register)**

Built by [Capzy](https://capzy.ai). Issues + PRs welcome.

</div>
