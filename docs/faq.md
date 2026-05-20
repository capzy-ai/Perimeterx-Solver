# FAQ — PerimeterX / HUMAN Security

## Pricing

**How much does a solve cost?** From $0.001 per solve. Flat — no
per-account tier, no monthly minimum, no retainer.

**Do I get free credit to try?** Yes — every account gets $0.10 in
real credits on signup, no card required.

**How do I pay?** Card (Stripe) or crypto. Top up the balance at
[capzy.ai/dashboard/billing](https://capzy.ai/dashboard/billing).

## Setup

**How do I get an API key?** Sign up at
[capzy.ai/auth/register](https://capzy.ai/auth/register), then grab a
key from [capzy.ai/dashboard/api-keys](https://capzy.ai/dashboard/api-keys).
Keys start with `capzy_`.

## Behaviour

**How long does a solve take?** ~10 seconds median for PerimeterX / HUMAN Security.
Cap your polling loop at 120 seconds — solves that take longer than
that are abnormal.

**Can I solve in parallel?** Yes. Account default is 30 concurrent
in-flight tasks; raised on request.

**Is there a rate limit?** Account default is 30 `createTask` requests
per second. Capzy's infrastructure scales horizontally — contact us
if you need higher limits.

## Errors and refunds

**What if a solve fails?** Failed solves auto-refund. Capzy only
deducts the solve fee when it successfully returns a solution.

**Are successful solves refundable?** No. Once a solution is handed
back, the work is done. If the solution doesn't behave the way you
expected at the target site, open a [support ticket](https://capzy.ai/support).

**Are there hidden fees?** No. The flat per-solve price is everything.

## Integration

**Can I use this with Selenium / Puppeteer / Playwright?** Yes — call
the Capzy API, get the solution, then apply it to the page (set a
field, click a coordinate, paste a token, whatever the task type
returns).

**Can I call Capzy from the browser?** No — your API key would be
exposed. Always call from a backend you control.

**Is there an SDK?** Yes — official Python SDK at
[github.com/capzy-ai/capzy-pip](https://github.com/capzy-ai/capzy-pip).
This repo is the SDK-free path for everyone else.

## Captcha-specific questions

**Do you support PerimeterX Hold Captcha (the press-and-hold widget)?** Yes — that's the primary challenge type this solver handles. PerimeterX's Hold Captcha (officially "HUMAN Challenge", since HUMAN Security acquired PerimeterX in 2022) is the press-and-hold button that PerimeterX renders when its risk score crosses a threshold. The button looks simple, but under the hood it runs a proof-of-work computation while streaming cursor-variance telemetry during the 8–10s hold. Our solver detects the widget (`#px-captcha`, `[class*="press-and-hold"]`, etc.), approaches it on a cubic-Bezier path, holds for 8.5–11.0s (randomized) with cursor micro-jitter every 200–400ms, and captures the resulting `_px3` cookie. The `challengePresented` field in the solution tells you whether the widget actually rendered — `true` means we exercised the press-and-hold; `false` means our fingerprint passed silently before PerimeterX escalated. Either way the cookies are valid.

**Why isn't there a ProxyLess variant?** PerimeterX clearance cookies (`_px3` / `_px2` / `_pxhd`) are cryptographically bound to the IP they were issued to. A token solved on our pool IP would be rejected the moment your downstream client called the protected endpoint from your own IP. So we don't ship a ProxyLess variant for PerimeterX — supply your own sticky proxy and we'll mint the token on that IP. Calls to `AntiPerimeterXTaskProxyLess` are rejected with `ERROR_PROXY_REQUIRED`.

**What proxy works for PerimeterX?** Residential, mobile, or static ISP — all fine. Datacenter proxies fail PerimeterX's press-and-hold validation every time because PerimeterX scores IP trust as a primary signal. Use a sticky session (~5–10 min stickiness) so the same IP is reused for the solve and your downstream call.

**Why does _px3 expire so fast?** Newer high-security deployments rotate _px3 every ~60 seconds. Re-solve when it expires, or keep the same sticky proxy across solves so consecutive _px3 mints chain cleanly.

**What are `uuid` / `vid` and do I need them?** Strongly recommended for any site that enforces session continuity (Microsoft signup, EA, retail signups). `uuid` is the `_pxvid` cookie value on the target page — find it in DevTools → Application → Cookies → `_pxvid`. Pass it on `createTask` and Capzy pre-seeds it on the solver's browser context BEFORE navigation, so PerimeterX issues clearance tied to YOUR visitor session. Without it our token belongs to a session PerimeterX won't recognize when your client replays. `vid` is sometimes distinct from `uuid` (read from `window._pxhc.vid`); if you only have `uuid` we use it for both.

**I tried passing the iframe URL (`iframe.hsprotect.net/...`) and it fails immediately — why?** That URL is the PerimeterX challenge-iframe, not the protected page. Hitting it directly returns a ~2 KB empty stub because the press-and-hold widget only renders inside the parent site's DOM context. Pass the URL of the page the user is actually trying to access (the parent page) as `websiteURL`. The solver now rejects iframe URLs with `ERROR_INVALID_PARAMS` so the wrong input is obvious on the first try (and refunded).

## Operational

**Where can I see uptime / incidents?**
[capzy.ai/status](https://capzy.ai/status).

**Where can I see my usage / spend?** The
[dashboard](https://capzy.ai/dashboard) shows your balance, recent
tasks, error rates, and a usage breakdown.

**How do I get help?** Open a [support ticket](https://capzy.ai/support).
Include the `taskId` for solve-specific questions.
