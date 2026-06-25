# Remi — Architecture

## Overview

Remi is a single-page, single-file (`index.html`) AI assistant for a retail pharmacy counter. It runs in two modes on one device: **Tech Mode**, where it autonomously watches a simulated shift and uses the Claude API with real tool-use to investigate and react to events, and **Patient Mode**, a kiosk-style pickup flow for patients that shares the same underlying state. There is no backend, build step, or framework — everything lives in client-side HTML/CSS/JS, calling the Anthropic API directly from the browser.

## System Components

| Component | What it does | Reads | Writes |
|---|---|---|---|
| **Simulation Engine** (`events`, `advanceMinute()`, `scheduleTick()`) | Fires a scripted timeline of shift events (fills, rejects, shortages, discrepancies, a diversion reveal) at simulated-shift minutes, at a speed the user controls (1×/2×/4×). | `state.shiftMinutes`, `state.speed`, `state.fired` | `state.shiftMinutes`, `state.fired`, triggers event handlers |
| **Event Handlers** (`handleFill`, `handleReject`, `handleShortage`, `handleDiscrepancy`, `handleDiversion`, `generateHandoffReport`) | Update shift bookkeeping (counts, stats, feed cards) for a fired event, then — for anything that's actually a decision point — call `runAgentTurn()`. | `state` | `state` (counts, stats, logs); calls `runAgentTurn()` |
| **Agentic Tool-Use Engine** (`runAgentTurn()`, `streamClaudeTurn()`, `TOOLS`, `TOOL_IMPL`) | The real decision-maker. Sends an event + state snapshot to Claude with tool definitions; Claude decides what to investigate and concludes with a recommendation. See "Agentic Loop" below. | `state` (via tool calls), `pharmacyStateSnapshot()` | `state` (via `flag_pharmacist`), reasoning panel DOM |
| **Live Shift Feed** (`pushFeedCard()`) | Left-hand panel: an instant, factual log of "what happened" — independent of whether Claude reacted. | `state` | feed panel DOM |
| **Reasoning Panel** (`runAgentTurn()`, `streamClaudeTurn()`, `escapeHtml()`) | Center panel: Claude's actual streamed reasoning, tool calls, and conclusions for each event — and, separately, command-bar Q&A via `askRemi()`. | — | reasoning panel DOM |
| **State Board** (`renderStateBoard()`, `flashStat()`) | Right-hand panel: live shift stats, controlled-substance counts/status, inventory bars, follow-up queue. | `state` | state board DOM |
| **EKG Strip** (`drawEkg()`, `ekgWave()`, `pulseEkg()`) | Purely decorative animated heartbeat that pulses on every shift event. | `ekgAmp`, `ekgX` | canvas |
| **Command Bar** (`askRemi()`, `buildSystemPrompt()`, `submitCommand()`) | Free-form Q&A to Claude, single-turn, no tool-use — separate from the agentic engine by design (see Design Decisions). | `state` (for context) | reasoning panel DOM |
| **API Key Modal** (`getApiKey()`, `openKeyModal()`, `closeKeyModal()`) | Lets the user paste an Anthropic API key, persisted in `localStorage`. Without it, both `runAgentTurn()` and `askRemi()` short-circuit and prompt for one. | `localStorage` | `localStorage` |
| **Patient Mode** (`renderPatientStep()`, `patientData`, `pickupDrugPool`) | Kiosk-style pickup flow: identity verification, prescription lookup, copay explanation, OBRA '90 counseling offer, signature/confirmation. | `state`, `patientData` | `state`, `patientData`, patient-mode DOM |
| **Cross-Mode Link** (`checkCrossModeAndProceed()`, `flashCrossModeAlert()`) | The one place Patient Mode reads a flag Tech Mode's agent set, redirecting a pickup to "team member needed" if the drug has an active CS flag or diversion alert. | `state.csFlags`, `state.diversionDetected` | patient-mode DOM, `state.followupList` |

## State Management

Everything lives in one global object, `state` (declared near the top of the `<script>` block). Selected fields:

| Field | Type | Meaning |
|---|---|---|
| `shiftMinutes` | number | Minutes elapsed since shift start (09:00). |
| `running`, `paused`, `speed` | bool, bool, number | Simulation clock controls. |
| `inv` / `invStart` | object | Current / starting standard-inventory counts (`met`, `ozm`, `lip`, `amx`). |
| `cs` / `csStart` | object | Current / starting controlled-substance counts (`oxy`, `hydro`, `add`, `xan`). |
| `oxyExpected` | number | What oxycodone's count *should* be — the only CS drug the scripted timeline ever introduces a real discrepancy for. See `expectedCount()`. |
| `oxyDiscrepancies` | array | `{ gap, at, n }` entries — oxycodone's discrepancy history, read by `trace_discrepancy` and `generate_form106`. |
| `csLog` | array | `{ drug, pt, qty, atMin, runningCount }` — full fill-by-fill ledger for every CS fill, read by `trace_discrepancy`. |
| `scripts`, `flags`, `rejects`, `followups` | number | Shift stat counters shown on the state board. |
| `diversionDetected` | bool | Set by the scripted diversion event; read by the cross-mode link and `conclusionColorFor()`. |
| `csFlags` / `csCritical` | object | Per-drug status (`due` / `ok` / `flag`) and critical flag, keyed by drug. |
| `fired` | Set | Dedupe key for the simulation loop so an event can't fire twice. |
| `followupList` | array | `{ name, reason, startMin, overdue }` — the pharmacist follow-up queue, written by both scripted seed data and `flag_pharmacist`. |

`drugNames` and `invMax` are constant lookup tables alongside `state`, not part of it.

## Agentic Loop

This is the core of the "is it really agentic" answer. For every shift event that warrants a decision, the flow is:

1. **Event fires** (`handleEvent()` in `advanceMinute()`'s scripted timeline, or the shift-end timeout).
2. **Handler updates bookkeeping** (counts, stats, feed card), then calls `runAgentTurn({ icon, trigger, userPrompt })`. `userPrompt` embeds the event description plus a fresh `pharmacyStateSnapshot()` — deliberately a *summary*, not the full ledger, so Claude has a reason to call a tool rather than already having everything.
3. **`runAgentTurn()` loop** (capped at 5 turns): calls `streamClaudeTurn(messages, body)`.
   - `streamClaudeTurn()` opens a streamed `POST /v1/messages` request with the `tools` array attached, and parses the Server-Sent Event stream live: text deltas are written into the DOM token-by-token (so the reasoning panel visibly "types"), and `tool_use` blocks are reconstructed from incremental JSON fragments.
   - If Claude's turn includes one or more `tool_use` blocks: the preceding text (Claude's own "> ..." commentary) is left on screen, a `⚙ calling toolName({...})` line is rendered for each tool call, `TOOL_IMPL[name](input)` is executed against `state`, and the result is sent back as a `tool_result` message. The loop continues.
   - If Claude's turn has no tool calls: that text is its final conclusion. The intermediate streamed lines from *that* turn are removed and replaced with one styled `.r-conclusion` bubble (color picked by `conclusionColorFor()`); lines from earlier turns stay as the visible investigation trail.
4. **Loop ends** when Claude stops calling tools, the 5-turn cap is hit, or an error occurs — errors render directly in the panel rather than failing silently.

Every request, tool selection, tool result, and conclusion is also logged to the browser console as `[Remi] ...` so the decision flow can be inspected live in devtools.

## Tool Definitions

| Tool | Inputs | Reads | Writes | Side effects |
|---|---|---|---|---|
| `trace_discrepancy` | `{ drug }` | `state.csStart`, `state.cs`, `state.oxyDiscrepancies`, `state.csLog` | — | none (pure read) |
| `check_inventory` | `{ drug }` | `state.cs` or `state.inv`, `state.csFlags` | — | none (pure read) |
| `decode_reject` | `{ code, drug }` | `REJECT_CODES` lookup table | — | none (pure read) |
| `flag_pharmacist` | `{ reason, severity }` | — | `state.followupList`, `state.followups` | calls `renderStateBoard()` — the only tool with an immediately visible UI side effect |
| `generate_form106` | `{ drug }` | `state.oxyDiscrepancies` | — | none (pure read); returns a recommendation, not a decision |

The `drug` parameter on every tool is constrained with a JSON Schema `enum` of `Object.keys(drugNames)` rather than a free string, so Claude can't pass a value `TOOL_IMPL` wouldn't recognize.

## Mode Switching

Tech Mode and Patient Mode are two sibling `<div>`s (`#tech-mode`, `#patient-mode`) toggled by CSS classes (`.swapped` / `.active`) on a single button click — there is no routing, no separate state per mode. Both read and write the same global `state` object, which is what makes the cross-mode alert possible: `checkCrossModeAndProceed()` (called during the Patient Mode pickup flow) checks `state.csFlags` and `state.diversionDetected`, fields that Tech Mode's agent loop set possibly minutes earlier and on a different visible screen.

## API Integration

Two independent call paths, both direct browser→Anthropic (no proxy):

- **Agentic path** (`runAgentTurn` → `streamClaudeTurn`): `stream: true`, `tools: TOOLS` attached, multi-turn, system prompt from `buildAgentSystemPrompt()`.
- **Command-bar path** (`askRemi`): single non-streamed call, no `tools`, system prompt from `buildSystemPrompt()`.

Both require headers `x-api-key`, `anthropic-version: 2023-06-01`, and `anthropic-dangerous-direct-browser-access: true` — the last one is what permits calling the Messages API from a browser context at all. The key itself comes from `localStorage` (`remi_api_key`), set via the 🔑 API Key modal; a missing or rejected key reopens that modal automatically from either path.

## Design Decisions

- **Why two separate Claude call paths instead of one.** The command bar answers arbitrary free-form questions where low latency matters more than tool-grounded accuracy; the agentic loop investigates specific shift events where grounding in real tool data matters more than speed. Unifying them would force every quick question through a multi-turn tool loop, or strip tools from event investigation — both worse trade-offs than keeping the paths separate.
- **Why a lean state snapshot instead of dumping the full ledger into every prompt.** If `pharmacyStateSnapshot()` already contained the full transaction history, Claude would have no reason to call `trace_discrepancy()` — the tool would be decorative. Keeping the snapshot to summary counts and statuses is what makes tool use load-bearing rather than theater.
- **Why streaming instead of a single JSON response.** A non-streamed call would only let the reasoning panel render after the *entire* turn (including any tool call) completed, producing a frozen-then-dumped block of text. Streaming lets the panel show Claude "thinking" token by token, which is the actual point of the reasoning panel.
- **Why the conclusion color is inferred from keywords rather than a structured field.** Asking Claude to also emit a separate severity enum risks that field disagreeing with the free-text conclusion it wrote. Scanning the conclusion's own words for `CRITICAL`/`ESCALATE`/etc. guarantees the displayed color always matches what the tech actually reads.
- **Why the scripted timeline still decides *that* a diversion moment happens.** The "this is now a pattern" beat is a fixed dramatic point in the demo, not something extracted from raw events by Claude. What's real is everything downstream: Claude independently traces the history, decides whether to draft Form 106 language, and decides whether/how to escalate — see `handleDiversion()`'s comment for the exact boundary.
- **Why no backend.** Built for hackathon judging: anyone can open `index.html` directly with no install step. The cost is that the Anthropic API key lives in the browser's `localStorage` rather than behind a server — acceptable for a demo where each judge supplies their own key, not for a production deployment serving real patients.
