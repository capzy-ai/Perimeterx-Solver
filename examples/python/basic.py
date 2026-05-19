"""
Solve PerimeterX / HUMAN Security with Capzy — minimal Python example, `requests` only.

Cost:   from $0.001 per solve (flat)
Speed:  ~10 seconds median

PerimeterX clearance cookies (_px3 / _px2 / _pxhd) are IP-bound — your
proxy is required, and there is no ProxyLess variant. Use the SAME
sticky proxy your downstream HTTP client will replay the cookies on.

Run with:
    pip install requests
    export CAPZY_KEY="capzy_xxxxxxxxxxxxxxxxxxxxxxxx"
    export PROXY_HOST="gw.your-provider.com"
    export PROXY_PORT="10000"
    export PROXY_USER="your-user"
    export PROXY_PASS="your-pass"
    python basic.py
"""

import os
import time

import requests

API_BASE = "https://api.capzy.ai"

# Grab a key for free at https://capzy.ai/auth/register ($0.10 starter credit).
CAPZY_KEY = os.environ["CAPZY_KEY"]

# Your sticky residential / mobile / static-ISP proxy. Datacenter IPs
# will fail PerimeterX's IP-trust scoring every time — don't use them.
PROXY_HOST = os.environ["PROXY_HOST"]
PROXY_PORT = int(os.environ["PROXY_PORT"])
PROXY_USER = os.environ.get("PROXY_USER", "")
PROXY_PASS = os.environ.get("PROXY_PASS", "")


def solve() -> dict:
    # 1) Create the task. Returns immediately with a taskId; the actual
    #    solve runs on Capzy's infrastructure using YOUR proxy.
    task = {
        "type": "AntiPerimeterXTask",
        "websiteURL": "https://example.com",
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
    print(f"created task {task_id}")

    # 2) Poll until ready. Cap the wait at 120s for slower captcha types.
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


if __name__ == "__main__":
    solution = solve()
    print("solution:", solution)
    # ─── How to use the result ────────────────────────────────────
    # Set ALL the returned cookies on your HTTP client and reuse the User-Agent. _px3 rotates every ~60 seconds — re-solve when it expires.
