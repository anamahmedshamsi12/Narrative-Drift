# Remi — Demo Script

A practical run-through for recording the hackathon demo video or walking judges through the app live. Pairs with the shorter "Demo Flow" summary in the README — this version includes setup notes and covers everything built since that summary was written (sidebar views, drug tooltips, Electron shell).

## Setup (before recording)

1. Get an Anthropic API key.
2. Open the app one of two ways:
   - **Browser** (simplest, no install): `open index.html`
   - **Desktop app** (native window, what judges should see if you want the "installed software" feel): `npm install && npm start`
3. Click **🔑 API Key** in the topbar (or go to Settings in the sidebar) and paste the key. It's saved to `localStorage`/the OS, not sent anywhere but `api.anthropic.com`.
4. Have your browser/devtools console open at least once before recording so you can show the `[Remi] ...` log lines proving the agent calls are real, if a judge asks.

## Script (~4 minutes)

**0:00 — Personal hook (30s)**
> "I worked as a pharmacy technician. Techs are interrupted every four minutes. Controlled substance investigations are done with paper logs and memory. I built Remi — and unlike most AI demos, the agent reasoning you're about to see is a real Claude tool-use loop, not scripted text."

**0:30 — Tech Mode: start the shift (60s)**
- Hit **▶ Start Shift** at 2× or 4× speed.
- First fill comes in — point out the Live Shift Feed logs it instantly, independent of whether the agent reacts.
- Insurance reject fires (code 75) — watch the reasoning panel stream: Remi's own "> checking..." lines appear live, then `⚙ calling decode_reject(...)` renders, then the final conclusion. This is the real tell that it's not canned text — the tool call line is genuine.
- First oxycodone discrepancy — watch Remi call `trace_discrepancy`, reconstruct the ledger, and conclude there's no transaction-level explanation.

**1:30 — Diversion detection (30s)**
- Second discrepancy fires. Remi connects it to the first via `generate_form106`, drafts DEA Form 106 language, and (if it decides to) calls `flag_pharmacist` — watch the Follow-ups count tick up live as that tool call lands.

**2:00 — Tour the sidebar (45s)**
- Hover the sidebar to expand it; click through:
  - **Dispensing** — the full CS ledger, with the discrepancy showing as its own "COUNT" row rather than attached to a fill (call out that this is intentionally honest about what a discrepancy actually means).
  - **Inventory** — full 8-drug grid; manually edit a count to show it writing back live and the reorder list updating.
  - **Interactions** — type two drug names (e.g. "oxycodone", "alprazolam"), hit Check, show the severity matrix and its disclaimer that this is Claude's reasoning grounded by OpenFDA label text, not a database lookup.
  - **Reports** — show the deterministic shift report + Form 106 draft, then **Generate Audit Package** to trigger the print dialog (target "Save as PDF").

**2:45 — Drug tooltips (20s)**
- Hover any drug name anywhere in the app (feed, inventory, dispensing). After ~300ms, the OpenFDA-backed card appears — class, route, boxed warning if one exists, interactions/dosing excerpts. Move the mouse onto the card itself to show it doesn't disappear.

**3:05 — Patient Mode: pickup intake (40s)**
- Switch to Patient Mode (or press **Cmd/Ctrl+P** if running the desktop build).
- Walk identity verification → prescription confirmation → OBRA counseling offer → copay.
- Pick up the flagged oxycodone patient to show **cross-mode intelligence**: Remi silently alerts the tech, AND seeds that drug into the Interactions checker for when they switch back.

**3:45 — Command bar + wrap (15s)**
- Type "Generate shift handoff report" in the command bar.
- Press **Escape** to snap back to Tech Mode.
- Close on: "Every reasoning step you saw was a live Claude API call with real tool use — not a script."

## If asked "is this really agentic?"

Open devtools → Console. Every agent turn logs `[Remi] Event fired`, `[Remi] State snapshot`, `[Remi] Claude API request`, `[Remi] Tool(s) selected`, `[Remi] Tool result`, `[Remi] Agent conclusion` — the full decision trail, not just the rendered output. See `docs/ARCHITECTURE.md` → "Agentic Loop" for the code-level explanation.

## Known limitations to acknowledge if asked

- The Interactions view's severity matrix is Claude's clinical reasoning grounded by OpenFDA label text where available — not a structured drug-interaction database (OpenFDA doesn't expose one). Disclosed in the UI itself, not hidden.
- DEA schedule badges come from a small local lookup table (`DRUG_SCHEDULES`), not OpenFDA — OpenFDA's label data doesn't reliably expose schedule.
- `PAR_LEVELS` in the Inventory view are illustrative reference numbers for the demo, not real wholesale ordering thresholds.
- The Electron desktop build is unsigned — fine for local demo/judging, not for distribution without a code-signing setup.
