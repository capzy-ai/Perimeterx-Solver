/**
 * GNC end-to-end: solve a real PerimeterX press-and-hold with the BLOCK-REPLAY task.
 *
 * gnc.com sits behind PerimeterX / HUMAN Security. This shows the full
 * "consume-the-block" loop — the deterministic way to solve PerimeterX:
 *
 *   1. YOU request the protected GNC page through your proxy.
 *   2. PerimeterX answers with a 403 block (the press-and-hold page).
 *   3. You hand Capzy that exact block (body + cookies) + your proxy + UA.
 *   4. Capzy adopts THAT session, solves the press-and-hold, and returns
 *      clearance bound to your own _pxvid.
 *   5. You replay the returned cookies + UA on the SAME proxy -> 200 OK.
 *
 * A fresh navigation from a clean IP often silent-passes (nothing to solve)
 * and mints a brand-new session that re-challenges on replay. Block-replay is
 * deterministic: you supply the live 403, so the clearance binds to the
 * session you are actually using.
 *
 * Cost:   $0.025 per solve (proxy required)
 * Speed:  ~10 seconds median
 *
 * Run with (Node 18+):
 *   npm install undici            # needed to route fetch through your proxy
 *   export CAPZY_KEY="capzy_xxxxxxxxxxxxxxxxxxxxxxxx"
 *   export PROXY_HOST="gw.your-provider.com"
 *   export PROXY_PORT="10000"
 *   export PROXY_USER="your-user"
 *   export PROXY_PASS="your-pass"
 *   node gnc_block_replay.js
 */

const { ProxyAgent } = require("undici");

const API_BASE = "https://api.capzy.ai";
const CAPZY_KEY = process.env.CAPZY_KEY;

// Sticky proxy. PerimeterX clearance is IP-bound, so the SAME proxy must fetch
// the block, solve, and replay. Use a sticky port for one consistent egress IP.
const PROXY_HOST = process.env.PROXY_HOST;
const PROXY_PORT = parseInt(process.env.PROXY_PORT, 10);
const PROXY_USER = process.env.PROXY_USER || "";
const PROXY_PASS = process.env.PROXY_PASS || "";

// The protected GNC page. Homepage is PX-protected; override with any deeper
// GNC URL you actually need.
const TARGET_URL = process.env.TARGET_URL || "https://www.gnc.com/";

// Clearance is UA-bound — keep fetch, solve, and replay on the same UA.
const USER_AGENT =
  process.env.USER_AGENT ||
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
    "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36";

function proxyDispatcher() {
  const auth = PROXY_USER
    ? `${encodeURIComponent(PROXY_USER)}:${encodeURIComponent(PROXY_PASS)}@`
    : "";
  return new ProxyAgent(`http://${auth}${PROXY_HOST}:${PROXY_PORT}`);
}

function looksBlocked(status, body) {
  const markers = [
    "_pxAppId", "px-captcha", "captcha.px-cdn.net", "perimeterx",
    "Please verify you are a human", "Access to this page has been denied",
  ];
  return status === 403 || status === 429 || markers.some((m) => body.includes(m));
}

async function postJson(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}

// Step 1-2: hit GNC through the proxy and capture the PerimeterX block.
async function fetchBlock(dispatcher) {
  const res = await fetch(TARGET_URL, {
    dispatcher,
    headers: {
      "User-Agent": USER_AGENT,
      Accept:
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif," +
        "image/webp,*/*;q=0.8",
      "Accept-Language": "en-US,en;q=0.9",
      "Upgrade-Insecure-Requests": "1",
    },
  });
  const body = await res.text();

  // Parse cookies from the Set-Cookie headers into a {name: value} map.
  const cookies = {};
  for (const sc of res.headers.getSetCookie?.() || []) {
    const [pair] = sc.split(";");
    const idx = pair.indexOf("=");
    if (idx > 0) cookies[pair.slice(0, idx).trim()] = pair.slice(idx + 1).trim();
  }

  console.log(
    `GNC responded HTTP ${res.status} (${body.length} bytes, ` +
      `${Object.keys(cookies).length} cookies)`
  );

  if (!looksBlocked(res.status, body)) {
    throw new Error(
      "GNC did NOT block this request — it served the real page, so there is " +
        "no press-and-hold to solve. Block-replay needs an actual 403. Retry " +
        "on a fresh proxy port (a colder IP) or point TARGET_URL at a more " +
        "aggressively protected GNC path."
    );
  }
  return { body, cookies };
}

// Step 3-4: submit the block to Capzy and poll until clearance is minted.
async function solve(block) {
  const task = {
    type: "AntiPerimeterXBlockTask",
    websiteURL: TARGET_URL,
    blockData: block.body, // the live 403 — carries the session vid/uuid
    blockMode: "auto", // auto-detect HTML block vs XHR/JSON block
    cookies: block.cookies, // cookies from the blocked response
    userAgent: USER_AGENT, // MUST match the fetch + the replay
    proxyType: "http",
    proxyAddress: PROXY_HOST,
    proxyPort: PROXY_PORT,
  };
  if (PROXY_USER) {
    task.proxyLogin = PROXY_USER;
    task.proxyPassword = PROXY_PASS;
  }

  const created = await postJson("/createTask", { clientKey: CAPZY_KEY, task });
  if (created.errorId) {
    throw new Error(`createTask: ${created.errorCode} — ${created.errorDescription}`);
  }
  const taskId = created.taskId;
  console.log(`created task ${taskId} — solving the press-and-hold...`);

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

// Step 5: prove it works — replay the clearance on the SAME proxy.
async function replay(solution, dispatcher) {
  const res = await fetch(TARGET_URL, {
    dispatcher,
    headers: {
      Cookie: solution.cookie,
      "User-Agent": solution.userAgent,
      Accept:
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif," +
        "image/webp,*/*;q=0.8",
      "Accept-Language": "en-US,en;q=0.9",
    },
  });
  return res.status;
}

(async () => {
  console.log(`target: ${TARGET_URL}\n`);
  const dispatcher = proxyDispatcher();

  const block = await fetchBlock(dispatcher);
  const solution = await solve(block);

  console.log("\nSOLVED — clearance minted:");
  console.log(`  consumedBlock:      ${solution.consumedBlock}`);
  console.log(
    `  challengePresented: ${solution.challengePresented} ` +
      `(held ${solution.holdDurationSec}s)`
  );
  console.log(`  appId:              ${solution.blockAppId}`);
  console.log(`  _pxvid (uuid):      ${solution.uuid}`);
  console.log(`  cookie:             ${(solution.cookie || "").slice(0, 80)}...`);

  const status = await replay(solution, dispatcher);
  console.log(`\nreplay through the same proxy -> HTTP ${status}`);
  if (status === 200) {
    console.log("[OK] cleared PerimeterX — the page loaded with the solved session.");
  } else {
    console.log(
      "[WARN] replay was not 200. Make sure the SAME sticky proxy port + " +
        "User-Agent are used for fetch, solve, and replay."
    );
  }
})().catch((e) => {
  console.error(String(e.message || e));
  process.exit(1);
});
