/**
 * Solve PerimeterX / HUMAN Security with Capzy — minimal Node.js example.
 *
 * Cost:   from $0.001 per solve (flat)
 * Speed:  ~10 seconds median
 *
 * PerimeterX clearance cookies (_px3 / _px2 / _pxhd) are IP-bound — your
 * proxy is REQUIRED, and there is no ProxyLess variant. Use the SAME
 * sticky proxy your downstream HTTP client will replay the cookies on.
 *
 * Run with (Node 18+):
 *   export CAPZY_KEY="capzy_xxxxxxxxxxxxxxxxxxxxxxxx"
 *   export PROXY_HOST="gw.your-provider.com"
 *   export PROXY_PORT="10000"
 *   export PROXY_USER="your-user"
 *   export PROXY_PASS="your-pass"
 *   node basic.js
 *
 * Uses the built-in global `fetch` — no dependencies, no npm install.
 */

const API_BASE = "https://api.capzy.ai";
const CAPZY_KEY = process.env.CAPZY_KEY;

// Sticky residential / mobile / static-ISP proxy. Datacenter IPs fail
// PerimeterX's IP-trust scoring every time — don't bother.
const PROXY_HOST = process.env.PROXY_HOST;
const PROXY_PORT = parseInt(process.env.PROXY_PORT, 10);
const PROXY_USER = process.env.PROXY_USER || "";
const PROXY_PASS = process.env.PROXY_PASS || "";

async function postJson(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}

async function solve() {
  // 1) Create the task — proxy is required for PerimeterX.
  const task = {
    type: "AntiPerimeterXTask",
    websiteURL: "https://example.com",
    proxyType: "http",
    proxyAddress: PROXY_HOST,
    proxyPort: PROXY_PORT,
  };
  if (PROXY_USER) {
    task.proxyLogin = PROXY_USER;
    task.proxyPassword = PROXY_PASS;
  }
  const created = await postJson("/createTask", {
    clientKey: CAPZY_KEY,
    task,
  });
  if (created.errorId) {
    throw new Error(`createTask: ${created.errorCode} — ${created.errorDescription}`);
  }
  const taskId = created.taskId;
  console.log("created task", taskId);

  // 2) Poll until ready.
  const deadline = Date.now() + 120_000;
  while (Date.now() < deadline) {
    const result = await postJson("/getTaskResult", {
      clientKey: CAPZY_KEY,
      taskId,
    });
    if (result.errorId) {
      throw new Error(`getTaskResult: ${result.errorCode} — ${result.errorDescription}`);
    }
    if (result.status === "ready") return result.solution;
    await new Promise((r) => setTimeout(r, 2000));
  }
  throw new Error("solve took longer than 120s");
}

(async () => {
  const solution = await solve();
  console.log("solution:", solution);
  // ─── Example solution shape ─────────────────────────────────
  // {
  //   token:              "<_px3 cookie value>",
  //   cookie:             "_px3=<value>; _pxhd=<value>; _pxvid=<uuid>",
  //   cookies:            [{ name: "_px3", value: "...", domain: "...", path: "/" }, ...],
  //   userAgent:          "Mozilla/5.0 (...) Chrome/... Safari/...",
  //   challengePresented: true,   // Hold Captcha widget rendered + held
  //   holdDurationSec:    9.4,    // 0 if challengePresented is false
  //   ipBound:            true
  // }
  //
  // ─── How to use the result ──────────────────────────────────
  // Drop-in — paste `cookie` straight into a Cookie: header:
  //
  //   const headers = {
  //     "Cookie":     solution.cookie,
  //     "User-Agent": solution.userAgent,
  //   };
  //   await fetch(targetUrl, { headers, agent: yourProxyAgent });
  //
  // Replay MUST come through the SAME proxy you supplied at solve
  // time (clearance is IP+UA bound). `_px3` rotates every ~60s on
  // newer deployments — re-solve when it expires.
})();
