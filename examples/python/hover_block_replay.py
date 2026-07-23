"""
hover.hillsclerk.com end-to-end with AntiPerimeterXTask.

hover runs PerimeterX first-party. You don't have to capture the block yourself:
give Capzy the URL, your proxy, and a UA, and it navigates the page, trips the
press-and-hold, solves it, and returns clearance tied to your session. Then you
replay the cookies + UA on the same proxy.

Steps:
    1. createTask with the target URL + your proxy + UA.
    2. Poll getTaskResult until it's ready.
    3. Replay the returned cookies + UA on the same proxy. You're through (200).

Keep the TLS fingerprint in sync with the UA. curl_cffi is pinned to chrome146
so the JA3/H2 matches the Chrome/146 User-Agent on the replay. Same sticky proxy
IP + same UA across the solve and the replay, since the clearance is bound to
both.

Cost:   $0.025 per solve (proxy required)
Speed:  ~12 seconds median

Run:
    pip install curl_cffi
    export CAPZY_KEY="capzy_xxxxxxxxxxxxxxxxxxxxxxxx"
    export PROXY_HOST="gw.your-provider.com"
    export PROXY_PORT="10001"          # sticky port = stable egress IP
    export PROXY_USER="your-user"
    export PROXY_PASS="your-pass"
    python hover_block_replay.py
"""

import os
import time

from curl_cffi import requests as creq

API_BASE = "https://api.capzy.ai"
CAPZY_KEY = os.environ["CAPZY_KEY"]

PROXY_HOST = os.environ["PROXY_HOST"]
PROXY_PORT = int(os.environ["PROXY_PORT"])
PROXY_USER = os.environ.get("PROXY_USER", "")
PROXY_PASS = os.environ.get("PROXY_PASS", "")

TARGET_URL = os.environ.get(
    "TARGET_URL", "https://hover.hillsclerk.com/html/case/caseSearch.html")

# TLS impersonation and UA have to be the same Chrome version, otherwise the
# JA3/H2 fingerprint won't line up with the User-Agent string.
IMPERSONATE = "chrome146"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36")


def _proxies() -> dict:
    auth = f"{PROXY_USER}:{PROXY_PASS}@" if PROXY_USER else ""
    url = f"http://{auth}{PROXY_HOST}:{PROXY_PORT}"
    return {"http": url, "https": url}


def solve() -> dict:
    """Steps 1-2. Create the task and poll until Capzy returns clearance."""
    task = {
        "type": "AntiPerimeterXTask",
        "websiteURL": TARGET_URL,
        "userAgent": USER_AGENT,        # same UA you'll replay with
        "proxyType": "http",
        "proxyAddress": PROXY_HOST,
        "proxyPort": PROXY_PORT,
    }
    if PROXY_USER:
        task["proxyLogin"] = PROXY_USER
        task["proxyPassword"] = PROXY_PASS

    created = creq.post(f"{API_BASE}/createTask",
                        json={"clientKey": CAPZY_KEY, "task": task},
                        timeout=15).json()
    if created.get("errorId"):
        raise RuntimeError(f"createTask failed: {created.get('errorCode')}: "
                           f"{created.get('errorDescription')}")
    task_id = created["taskId"]
    print(f"created task {task_id}, solving the press-and-hold...")

    deadline = time.time() + 120
    while time.time() < deadline:
        res = creq.post(f"{API_BASE}/getTaskResult",
                        json={"clientKey": CAPZY_KEY, "taskId": task_id},
                        timeout=15).json()
        if res.get("errorId"):
            raise RuntimeError(f"getTaskResult failed: {res.get('errorCode')}: "
                               f"{res.get('errorDescription')}")
        if res["status"] == "ready":
            return res["solution"]
        time.sleep(2)
    raise TimeoutError("solve took longer than 120s")


# Text that only shows up when PerimeterX is still blocking. A 200 status
# alone doesn't mean you're through, the block/captcha page returns 200 too,
# so we scan the body for these.
BLOCK_MARKERS = (
    "access to this page has been denied",
    "please verify you are a human",
    "px-captcha",
    "perimeterx, inc",
)


def replay(solution: dict) -> bool:
    """Step 3. Replay the clearance and actually check we landed on the real
    page, not another block. Returns True only if it's clean."""
    sent_px3 = ""
    for c in solution.get("cookies", []):
        if c.get("name") == "_px3":
            sent_px3 = c.get("value", "")

    r = creq.get(
        TARGET_URL, timeout=30, impersonate=IMPERSONATE, proxies=_proxies(),
        headers={"User-Agent": solution.get("userAgent", USER_AGENT),
                 "Cookie": solution["cookie"],
                 "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                 "Accept-Language": "en-US,en;q=0.9"})

    body = (r.text or "").lower()
    print(f"  status: {r.status_code}, body: {len(r.text)} bytes")

    if r.status_code != 200:
        print(f"  blocked: status {r.status_code}")
        return False

    hits = [m for m in BLOCK_MARKERS if m in body]
    if hits:
        print(f"  blocked: challenge markers in body {hits}")
        return False

    # If PX rejected our cookie it hands back a fresh _px3 to start over.
    # Same value (or no _px3 on the response) means it was accepted.
    got_px3 = r.cookies.get("_px3")
    if sent_px3 and got_px3 and got_px3 != sent_px3:
        print("  blocked: server replaced _px3 (cookie rejected)")
        return False

    return True


if __name__ == "__main__":
    print(f"target: {TARGET_URL}\n")
    solution = solve()

    print("\nsolved, clearance minted:")
    print(f"  challengePresented: {solution.get('challengePresented')} "
          f"(held {solution.get('holdDurationSec')}s)")
    print(f"  _pxvid (uuid):      {solution.get('uuid')}")
    print(f"  cookie:             {solution.get('cookie', '')[:80]}...")

    print("\nreplay through the same proxy:")
    ok = replay(solution)
    print("cleared PerimeterX" if ok else
          "still blocked - use the same sticky port + UA for the solve and replay")
