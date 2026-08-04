<div align="center">

<img src="https://capzy.ai/capzy-icon.png" alt="Capzy" width="96" />

# PerimeterX / HUMAN Security Captcha Solver

**Bypass PerimeterX press-and-hold. Returns _px3 / _px2 / _pxhd cookies.**

[![Solve cost](https://img.shields.io/badge/from-%240.001%20%2F%20solve-%23ff5d2a)](https://capzy.ai/solvers)
[![Speed](https://img.shields.io/badge/avg%20solve-~10%20seconds-%2322c55e)](https://capzy.ai/solvers/perimeterx)
[![Uptime](https://img.shields.io/badge/uptime-99.9%25-%2322c55e)](https://capzy.ai/status)
[![License: MIT](https://img.shields.io/badge/license-MIT-%23ff5d2a)](LICENSE)

[Live Demo](https://capzy.ai/solvers/perimeterx/demo) ·
[Get Free $0.10 Credit](https://capzy.ai/auth/register) ·
[Dashboard](https://capzy.ai/dashboard) ·
[Full Docs](https://capzy.ai/docs) ·
[Pricing](https://capzy.ai/solvers)

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
| `AntiPerimeterXTask` | You supply the proxy (required — IP-bound) | **$0.001**   |

For consistency across the target site, use the proxy variant with the
**same proxy your session is already running through** — the solver
mints the token from that IP, so when you submit it back through the
same proxy everything looks consistent.

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

# 1) Create the task
created = requests.post("https://api.capzy.ai/createTask", json={
    "clientKey": KEY,
    "task": {
        "type": "AntiPerimeterXTask",
        "websiteURL": "https://example.com"
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
    "websiteURL": "https://example.com"
  }
}
```

| Field | Type | Required | Notes |
|-------|------|:--------:|-------|
| `type` | `string` | yes | AntiPerimeterXTask (the only supported variant — no ProxyLess for PerimeterX) |
| `websiteURL` | `string` | yes | Full URL of the PROTECTED parent page. NOT the PerimeterX challenge iframe URL (iframe.hsprotect.net / *.px-cdn.net) — those return ERROR_INVALID_PARAMS because the widget only renders inside the parent site's context. |
| `uuid` | `string` | no | Visitor `_pxvid` cookie value from the target page. Pre-seeded on the solver context before navigation so PerimeterX issues clearance tied to YOUR session. Strongly recommended for sites that enforce visitor binding. |
| `vid` | `string` | no | Visitor ID from `window._pxhc.vid` (sometimes distinct from uuid). Falls back to uuid when omitted. |
| `pxAppId` | `string` | no | PerimeterX tenant ID (e.g. PXzC5j78di). Visible in //client.perimeterx.net/<pxAppId>/main.min.js on the target page. |
| `_pxhd` | `string` | no | Hardened-device cookie value if the target site sets one alongside _pxvid. |
| `proxyType` | `string` | no  | http | https | socks4 | socks5 (only for `AntiPerimeterXTask`) |
| `proxyAddress` | `string` | no  | IP or hostname of your proxy (only for `AntiPerimeterXTask`) |
| `proxyPort` | `integer` | no  | Port number of your proxy (only for `AntiPerimeterXTask`) |
| `proxyLogin` | `string` | no  | Optional — omit if your proxy doesn't require auth (only for `AntiPerimeterXTask`) |
| `proxyPassword` | `string` | no  | Optional — omit if your proxy doesn't require auth (only for `AntiPerimeterXTask`) |

Full reference in [`docs/parameters.md`](docs/parameters.md).

## Response shape

When the task is ready (`status: "ready"`), `solution` contains:

| Field | Type | Notes |
|-------|------|-------|
| `token` | `string` | Highest-priority cookie value (_px3 if present, else _px2, else _pxhd) |
| `cookies` | `array` | All _px* cookies in {name, value, domain, path} form for full session replay |
| `userAgent` | `string` | User-Agent used during solve — match this on subsequent requests |

### How to use the result

Set ALL the returned cookies on your HTTP client and reuse the User-Agent, and replay through the SAME proxy you supplied at solve time — the cookies are bound to that IP. _px3 rotates every ~60 seconds — re-solve when it expires.

## Features

- Your residential / mobile / static-ISP proxy required (IP-bound cookies)
- Returns _px3 (priority) → _px2 → _pxhd with full _px* cookie set
- User-Agent capture for session continuity
- Handles press-and-hold and behavioral-only variants

## FAQ

**Why isn't there a ProxyLess variant?** PerimeterX clearance cookies (_px3 / _px2 / _pxhd) are cryptographically tied to the IP they were issued to. A token solved on our pool IP would be rejected the moment your downstream client called the protected endpoint from your own IP. So PerimeterX only ships in proxy-required form — your residential / mobile / ISP proxy mints the token directly. Other captchas (Turnstile, hCaptcha base, GeeTest, reCAPTCHA v2 base) aren't IP-bound and DO have ProxyLess variants on Capzy.

**What kind of proxy do I need?** Residential, mobile, or static ISP — all fine. Datacenter proxies will fail PerimeterX's IP-trust scoring every time. Use a sticky session (~5-10 min stickiness) so the same IP is reused for both the solve and your downstream call.

**Why does _px3 expire so fast?** Newer high-security deployments rotate _px3 every ~60 seconds. Re-solve when it expires, or keep the same sticky proxy across solves so consecutive _px3 mints chain cleanly.

**What are `uuid` / `vid` and do I need them?** Strongly recommended for any site that enforces session continuity. `uuid` is the `_pxvid` cookie value on the target page — find it in DevTools → Application → Cookies → `_pxvid`. Pass it on createTask and Capzy pre-seeds it on the solver's browser context BEFORE navigation, so PerimeterX issues clearance tied to YOUR visitor session. Without it the token may be rejected when your client replays. `vid` is sometimes distinct from `uuid` (read from `window._pxhc.vid`); if you only have `uuid` we use it for both.

**I tried passing the iframe URL (iframe.hsprotect.net) and it fails — why?** That URL is the PerimeterX challenge-iframe, not the protected page. Hitting it directly returns a ~2 KB empty stub because the press-and-hold widget only renders inside the parent site's DOM context. Pass the URL of the parent page (the actual page the user is trying to access) as websiteURL. The solver now rejects iframe URLs with ERROR_INVALID_PARAMS so the wrong input is obvious on the first try (and refunded).

## What you'll need

- A Capzy API key — [sign up](https://capzy.ai/auth/register) (free, $0.10 credit).
- Network access to `https://api.capzy.ai`.

## Other captcha types

Capzy solves 25+ captcha types. Full catalog at
[capzy.ai/solvers](https://capzy.ai/solvers). Each type has its own
solver repo on [github.com/capzy-ai](https://github.com/capzy-ai).

## The Capzy platform

Capzy is web access infrastructure for modern automation. Beyond captcha solving:

| Product | What it does |
|---------|--------------|
| **[Solver API](https://capzy.ai/solvers)** | Solve 25+ captcha types through one HTTP API. |
| **[Cloud Browser](https://capzy.ai/browser)** | Real remote Chrome over CDP / WebSocket, billed per GB. |
| **[Fingerprint API](https://capzy.ai/fingerprints)** | Coherent, authentic browser fingerprints on demand. |
| **[Proxies API](https://capzy.ai/proxies)** | Global proxy egress with simple per-GB pricing. |
| **[Web Scraper API](https://capzy.ai/web-scraper)** | Fetch, render, bypass anti-bot, and extract in one call. |

One API key and one wallet balance across every product.

## Keywords

`perimeterx / human security solver`, `perimeterx / human security captcha solver`, `perimeterx / human security bypass`, `perimeterx / human security api`, `solve perimeterx / human security`, `perimeterx / human security solving service`, `captcha solver`, `captcha solving api`, `automated captcha solver`, `captcha bypass api`

## License

[MIT](LICENSE).

---

<div align="center">

**[Sign up for free credits →](https://capzy.ai/auth/register)**

Built by [Capzy](https://capzy.ai). Issues + PRs welcome.

</div>
