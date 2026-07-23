# Examples — PerimeterX / HUMAN Security

Copy-pasteable examples for solving **PerimeterX / HUMAN Security** through the
Capzy HTTP API. Three languages, same two-step protocol:

1. `POST /createTask` — get a `taskId`
2. `POST /getTaskResult` (poll every 2s) until `status === "ready"`

## Setup

1. **Sign up** at [capzy.ai/auth/register](https://capzy.ai/auth/register) — $0.10 in real credits on signup. No card required.
2. **Get your API key** at [capzy.ai/dashboard/api-keys](https://capzy.ai/dashboard/api-keys). Keys start with `capzy_`.
3. **Export it** — every example reads `CAPZY_KEY` from the environment:
   ```bash
   export CAPZY_KEY="capzy_xxxxxxxxxxxxxxxxxxxxxxxx"
   ```
4. **Update the example** — open the file you want to run and replace any `https://example.com` / placeholder sitekey / etc. with values from the page you're actually solving against.

## Files

| Language        | File                              |
|-----------------|-----------------------------------|
| **curl / bash** | [`curl/basic.sh`](curl/basic.sh)  |
| **Python**      | [`python/basic.py`](python/basic.py) |
| **Node.js**     | [`nodejs/basic.js`](nodejs/basic.js) |

Each example is fully self-contained and ~50 lines. No SDK, no client
library, no abstraction between you and the API.

## Block-replay (consume-the-block) — full GNC walkthrough

`AntiPerimeterXBlockTask` is the deterministic way to solve PerimeterX: instead
of letting us navigate fresh and hope a press-and-hold appears, **you** make the
request, hit the 403 block yourself, and hand us that exact block. We adopt your
session, solve the press-and-hold, and return clearance bound to your own
`_pxvid` — so it validates when you replay it.

These run end-to-end against the live, PerimeterX-protected **gnc.com**:
fetch the page through your proxy → capture the 403 → solve → replay → confirm a
`200`.

| Language     | File                                                       |
|--------------|------------------------------------------------------------|
| **Python**   | [`python/gnc_block_replay.py`](python/gnc_block_replay.py) |
| **Node.js**  | [`nodejs/gnc_block_replay.js`](nodejs/gnc_block_replay.js) (`npm install undici`) |

Use the SAME sticky proxy port and `User-Agent` for the fetch, the solve, and
the replay — PerimeterX clearance is IP- and UA-bound. There is no curl version:
the flow has to capture a response body and resubmit it, which a shell one-liner
does not do cleanly.
