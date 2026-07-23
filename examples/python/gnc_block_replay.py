"""
GNC end-to-end: solve a real PerimeterX press-and-hold with the BLOCK-REPLAY task.

gnc.com sits behind PerimeterX / HUMAN Security. This example shows the full
"consume-the-block" loop against it — the deterministic way to solve PerimeterX:

    1. YOU request the protected GNC page through your proxy.
    2. PerimeterX answers with a 403 block (the press-and-hold page).
    3. You hand Capzy that exact block (its body + cookies) + your proxy + UA.
    4. Capzy adopts THAT session, solves the press-and-hold, and returns
       clearance bound to your own _pxvid.
    5. You replay the returned cookies + UA on the SAME proxy → 200 OK.

Why block-replay instead of `AntiPerimeterXTask`? A fresh navigation from a
clean IP often silent-passes — there is nothing to solve, and any clearance
minted belongs to a brand-new PX session that re-challenges when you replay it.
Block-replay is deterministic: you supply the live 403, so there is always a
real challenge, and the clearance binds to the session you are actually using.

Cost:   $0.025 per solve (proxy required)
Speed:  ~10 seconds median

Run with:
    pip install requests
    export CAPZY_KEY="capzy_xxxxxxxxxxxxxxxxxxxxxxxx"
    export PROXY_HOST="gw.your-provider.com"
    export PROXY_PORT="10000"
    export PROXY_USER="your-user"
    export PROXY_PASS="your-pass"
    python gnc_block_replay.py
"""

import os
import time

import requests

API_BASE = "https://api.capzy.ai"

# Grab a key for free at https://capzy.ai/auth/register ($0.10 starter credit).
CAPZY_KEY = os.environ["CAPZY_KEY"]

# Your sticky proxy. PerimeterX clearance is IP-bound, so the SAME proxy must
# be used to (a) fetch the block, (b) solve, and (c) replay. Use a sticky port
# so all three hit the same egress IP.
PROXY_HOST = os.environ["PROXY_HOST"]
PROXY_PORT = int(os.environ["PROXY_PORT"])
PROXY_USER = os.environ.get("PROXY_USER", "")
PROXY_PASS = os.environ.get("PROXY_PASS", "")

# The protected GNC page to break into. The homepage is PX-protected; override
# with any deeper GNC URL you actually need (e.g. a category or search page).
TARGET_URL = os.environ.get("TARGET_URL", "https://www.gnc.com/")

# Clearance is UA-bound: the SAME User-Agent must be used to fetch the block,
# to solve (we forward this), and to replay. Keep these three in lockstep.
USER_AGENT = os.environ.get(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
)


def _proxies() -> dict:
    if PROXY_USER:
        auth = f"{PROXY_USER}:{PROXY_PASS}@"
    else:
        auth = ""
    url = f"http://{auth}{PROXY_HOST}:{PROXY_PORT}"
    return {"http": url, "https": url}


def _looks_blocked(resp: requests.Response) -> bool:
    """True if this response is a PerimeterX block (the press-and-hold page)."""
    body = resp.text or ""
    markers = (
        "_pxAppId", "px-captcha", "captcha.px-cdn.net", "perimeterx",
        "Please verify you are a human", "Access to this page has been denied",
    )
    return resp.status_code in (403, 429) or any(m in body for m in markers)


def fetch_block() -> tuple[str, dict]:
    """Step 1-2: hit GNC through the proxy and capture the PerimeterX block.

    Returns (block_body, cookie_map). Raises if GNC let us straight through
    (nothing to solve) or if the request failed at the proxy.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,"
                   "image/avif,image/webp,*/*;q=0.8"),
        "Accept-Language": "en-US,en;q=0.9",
        "Upgrade-Insecure-Requests": "1",
    })
    resp = session.get(TARGET_URL, proxies=_proxies(), timeout=30,
                       allow_redirects=True)

    # Cookies accumulate on the session across any redirects — pass the whole
    # jar; the solver normalises a {name: value} map for you.
    cookie_map = {c.name: c.value for c in session.cookies}

    print(f"GNC responded HTTP {resp.status_code} "
          f"({len(resp.text)} bytes, {len(cookie_map)} cookies)")

    if not _looks_blocked(resp):
        raise SystemExit(
            "GNC did NOT block this request — it served the real page, so there "
            "is no press-and-hold to solve. Block-replay needs an actual 403. "
            "Retry on a fresh proxy port (a colder IP), or point TARGET_URL at a "
            "more aggressively protected GNC path."
        )

    return resp.text, cookie_map


def solve(block_body: str, cookie_map: dict) -> dict:
    """Step 3-4: submit the block to Capzy and poll until clearance is minted."""
    task = {
        "type": "AntiPerimeterXBlockTask",
        "websiteURL": TARGET_URL,
        # The live 403 we just captured — its body carries the session vid/uuid.
        "blockData": block_body,
        "blockMode": "auto",          # auto-detect HTML block vs XHR/JSON block
        "cookies": cookie_map,        # cookies from the blocked response
        "userAgent": USER_AGENT,      # MUST match the fetch + the replay
        # Same proxy that hit the 403 — clearance is IP-bound.
        "proxyType": "http",
        "proxyAddress": PROXY_HOST,
        "proxyPort": PROXY_PORT,
    }
    if PROXY_USER:
        task["proxyLogin"] = PROXY_USER
        task["proxyPassword"] = PROXY_PASS

    created = requests.post(
        f"{API_BASE}/createTask",
        json={"clientKey": CAPZY_KEY, "task": task},
        timeout=15,
    ).json()
    if created.get("errorId"):
        raise RuntimeError(f"createTask failed: {created.get('errorCode')} — "
                           f"{created.get('errorDescription')}")

    task_id = created["taskId"]
    print(f"created task {task_id} — solving the press-and-hold...")

    deadline = time.time() + 120
    while time.time() < deadline:
        result = requests.post(
            f"{API_BASE}/getTaskResult",
            json={"clientKey": CAPZY_KEY, "taskId": task_id},
            timeout=15,
        ).json()
        if result.get("errorId"):
            raise RuntimeError(f"getTaskResult failed: {result.get('errorCode')} — "
                               f"{result.get('errorDescription')}")
        if result["status"] == "ready":
            return result["solution"]
        time.sleep(2)

    raise TimeoutError("solve took longer than 120s")


def replay(solution: dict) -> int:
    """Step 5: prove it works — replay the clearance on the SAME proxy."""
    headers = {
        "Cookie": solution["cookie"],
        "User-Agent": solution["userAgent"],
        "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,"
                   "image/avif,image/webp,*/*;q=0.8"),
        "Accept-Language": "en-US,en;q=0.9",
    }
    resp = requests.get(TARGET_URL, headers=headers, proxies=_proxies(),
                        timeout=30, allow_redirects=True)
    return resp.status_code


if __name__ == "__main__":
    print(f"target: {TARGET_URL}\n")

    block_body, cookie_map = fetch_block()
    solution = solve(block_body, cookie_map)

    print("\nSOLVED — clearance minted:")
    print(f"  consumedBlock:      {solution.get('consumedBlock')}")
    print(f"  challengePresented: {solution.get('challengePresented')} "
          f"(held {solution.get('holdDurationSec')}s)")
    print(f"  appId:              {solution.get('blockAppId')}")
    print(f"  _pxvid (uuid):      {solution.get('uuid')}")
    print(f"  cookie:             {solution.get('cookie', '')[:80]}...")

    status = replay(solution)
    print(f"\nreplay through the same proxy -> HTTP {status}")
    if status == 200:
        print("[OK] cleared PerimeterX — the page loaded with the solved session.")
    else:
        print("[WARN] replay was not 200. Make sure the SAME sticky proxy port "
              "+ User-Agent are used for fetch, solve, and replay.")

    # ─── Solution shape ───────────────────────────────────────────────
    # {
    #   "token":              "<_px3 cookie value>",
    #   "cookie":             "_px3=...; _pxhd=...; _pxvid=<uuid>",
    #   "cookies":            [{"name": "_px3", "value": "...", "domain": "...", "path": "/"}, ...],
    #   "userAgent":          "Mozilla/5.0 (...) Chrome/... Safari/...",
    #   "uuid":               "<_pxvid — pin your replay session to this>",
    #   "vid":                "<PX vid>",
    #   "challengePresented": True,
    #   "holdDurationSec":    9.4,
    #   "consumedBlock":      True,
    #   "blockAppId":         "PX...",
    #   "blockHostUrl":       "https://collector-PX....perimeterx.net",
    #   "ipBound":            True
    # }
