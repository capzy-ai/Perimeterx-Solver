/**
 * Solve PerimeterX / HUMAN Security with Capzy — minimal Node.js example.
 *
 * Cost:   from $0.001 per solve (flat)
 * Speed:  ~10 seconds median
 *
 * Run with (Node 18+):
 *   export CAPZY_KEY="capzy_xxxxxxxxxxxxxxxxxxxxxxxx"
 *   node basic.js
 *
 * Uses the built-in global `fetch` — no dependencies, no npm install.
 */

const API_BASE = "https://api.capzy.ai";
const CAPZY_KEY = process.env.CAPZY_KEY;

async function postJson(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}

async function solve() {
  // 1) Create the task.
  const created = await postJson("/createTask", {
    clientKey: CAPZY_KEY,
    task: {
      "type": "AntiPerimeterXTaskProxyLess",
      "websiteURL": "https://example.com"
    },
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
  // ─── How to use the result ──────────────────────────────────
  // Set ALL the returned cookies on your HTTP client and reuse the User-Agent. _px3 rotates every ~60 seconds — re-solve when it expires.
})();
