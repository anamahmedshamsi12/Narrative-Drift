# Remi — AI Pharmacy Agent

> *"I worked as a pharmacy technician. This is the tool I wish existed."*

Remi is an agentic AI assistant built for the retail pharmacy counter. It operates in two distinct modes — **Tech Mode** for pharmacy staff and **Patient Mode** for patients at pickup — running autonomously in the background, detecting problems before they're asked about, and handling routine patient interactions so the tech can stay in their workflow.

Built for the **FutureAI Global Hackathon 2026** — Healthcare AI + AI Agents & Automation tracks.

---

## The Problem

Retail pharmacy technicians are interrupted an average of **once every four minutes**. Each interruption means a lost count, a forgotten callback, a discrepancy that doesn't get traced. Controlled substance discrepancy investigations — federally required, DEA-audited — are done manually with paper logs and memory. Patient pickups pull the tech away from everything else for 3–5 minutes of routine verification.

The result: errors, compliance risk, and a cognitive load that burns through staff.

The enterprise solutions (Omnicell, BD Pyxis) are built for hospitals. Independent retail pharmacies — where this pain is worst — have spreadsheets and sticky notes.

**Remi closes that gap.**

---

## What Remi Does

### Tech Mode — Operational AI Agent
Remi monitors the pharmacy shift autonomously. She doesn't wait to be asked.

**Shift Simulation Engine**
- Live event stream: fills, insurance rejects, inventory drops, controlled substance counts
- Accelerated time simulation (1×, 2×, 4× speed) for demos
- 20+ scripted shift events that build into a narrative arc

**Discrepancy Investigation**
- Detects controlled substance count mismatches automatically
- Traces full transaction history: dispensed, received, returned, adjusted
- Reconstructs where each unit should be, step by step
- Identifies most likely explanation — or explicitly flags as unexplained
- Generates DEA Form 106 language when pattern crosses diversion threshold

**Diversion Pattern Detection**
- Tracks discrepancies across multiple count cycles within a shift
- Identifies patterns consistent with diversion tactics (consistent small gaps)
- Escalates with full documentation trail — not just an alert, a case file

**Insurance Reject Decoder**
- Decodes NCPDP reject codes in plain English
- Gives the most likely fix: override code, PA trigger, rebill options
- Offers GoodRx cash price comparison when appropriate
- Generates script for what to tell the patient right now

**Inventory Intelligence**
- Real-time stock tracking with visual indicators
- FDA shortage list integration — flags extended lead times
- Proactive reorder recommendations based on fill velocity
- Patient impact assessment when stock is critically low

**Follow-up Queue**
- Logs patient callbacks, price checks, script-ready notifications
- Urgency scoring — surfaces overdue items without being asked
- End-of-shift handoff report: everything still open, next tech priorities

**Remi's Reasoning Panel**
- Every autonomous action shows chain-of-thought line by line
- Judges and reviewers see the AI actually reasoning, not just outputting
- Distinguishes between "wait," "act," and "escalate" decisions with rationale

---

### Patient Mode — Pickup Intake Agent
When a patient approaches the counter, Remi switches to a warm, accessible interface and handles the entire pickup flow so the tech doesn't have to stop what they're doing.

**Identity Verification**
- Collects name and date of birth conversationally
- Confirms identity before pulling prescription details

**Prescription Lookup**
- Surfaces what's ready for pickup
- Shows drug name, quantity, prescriber
- Flags if anything is still pending or requires pharmacist attention

**Copay Explanation**
- Shows copay clearly with insurance breakdown
- If copay is higher than expected: explains why (formulary tier, deductible status, prior auth)
- Offers GoodRx comparison automatically if cash price is lower
- Flags tech if patient needs assistance or wants to speak to someone

**OBRA '90 Counseling Offer**
- Federally mandated: every patient must be offered pharmacist counseling
- Remi handles the offer conversationally, not as a checkbox
- Documents offer + patient response automatically
- If patient has questions: captures them and queues for pharmacist with full context so they're not walking in cold

**Digital Signature Capture**
- Collects pickup acknowledgment
- Logs timestamp, drug, quantity, patient confirmation

**Cross-Mode Intelligence**
- Remi maintains operational awareness in Patient Mode
- If a patient is picking up a drug with an active discrepancy flag, Remi knows
- Alerts tech silently without interrupting the patient interaction

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    REMI AGENT CORE                   │
│                                                      │
│  ┌─────────────┐    ┌──────────────┐                │
│  │  Tech Mode  │    │ Patient Mode │                │
│  │  Dashboard  │◄──►│   Intake     │                │
│  └──────┬──────┘    └──────┬───────┘                │
│         │                  │                         │
│  ┌──────▼──────────────────▼───────┐                │
│  │        Shift State Engine        │                │
│  │  (inventory, CS log, queue,      │                │
│  │   discrepancies, events)         │                │
│  └──────────────┬───────────────────┘                │
│                 │                                    │
│  ┌──────────────▼───────────────────┐                │
│  │      Claude API (claude-sonnet)   │                │
│  │                                  │                │
│  │  Tools:                          │                │
│  │  • trace_discrepancy()           │                │
│  │  • check_inventory()             │                │
│  │  • decode_reject()               │                │
│  │  • add_followup()                │                │
│  │  • generate_form106()            │                │
│  │  • flag_pharmacist()             │                │
│  │  • patient_intake()              │                │
│  └──────────────────────────────────┘                │
└─────────────────────────────────────────────────────┘
```

**Simulation Engine** — JavaScript state machine running a full pharmacy shift in accelerated time. Events fire automatically, inventory drops, CS counts drift, discrepancies accumulate, diversion patterns emerge. Remi watches and acts without being prompted.

**Dual Mode UI** — Single-page application that switches cleanly between dark, data-dense Tech Mode and warm, accessible Patient Mode. Same agent, two completely different interfaces, one device.

**Reasoning Panel** — Every autonomous agent action renders its chain-of-thought line by line in real time. Not a summary — actual step-by-step reasoning visible to the user.

**Claude API Integration** — Free-form questions answered with full shift context injected into every API call. Remi knows what's happening in the shift when she answers anything.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vanilla HTML/CSS/JS — zero build step, runs anywhere |
| AI | Claude claude-sonnet-4-6 via Anthropic API |
| Fonts | Space Grotesk (UI) + JetBrains Mono (data) |
| Simulation | Custom JavaScript state machine |
| Deployment | Static file — open in any browser |

### Why no framework?
Hackathon constraint: maximum portability. Judges can open `index.html` directly. No npm install, no build step, no environment setup. The AI is the complexity — the delivery mechanism should be frictionless.

---

## Project Structure

```
remi-rx/
├── index.html          # Full application — Tech Mode + Patient Mode
├── README.md           # This file
├── DEMO.md             # Demo script for video recording
├── assets/
│   └── remi-logo.svg   # Brand mark
└── docs/
    ├── architecture.md # Detailed system design
    ├── pharmacy-domain.md  # Domain knowledge reference
    └── hackathon-submission.md  # Devpost copy
```

---

## Running Locally

```bash
git clone https://github.com/anamahmedshamsi12/remi-rx.git
cd remi-rx
open index.html
```

That's it. No dependencies.

---

## Demo Flow

**Recommended demo sequence for video (3 minutes):**

**0:00 — Personal hook (30 sec)**
> "I worked as a pharmacy technician. Techs are interrupted every four minutes. Controlled substance investigations are done with paper logs and memory. I built Remi."

**0:30 — Tech Mode: Start the shift (60 sec)**
- Hit Start Shift at 2× speed
- Watch first fills come in, Remi reconciling counts automatically
- Insurance reject fires — watch Remi decode code 75, offer GoodRx alternative, generate script
- First oxycodone discrepancy — watch reasoning panel trace the transaction log line by line

**1:30 — Diversion detection (30 sec)**
- Second discrepancy fires
- Watch Remi connect the two events, raise diversion flag
- DEA Form 106 language generated automatically

**2:00 — Patient Mode: Pickup intake (45 sec)**
- Switch to Patient Mode
- Walk through patient pickup: identity verification, prescription confirmation, OBRA offer, copay explanation
- Show cross-mode intelligence: patient picking up flagged drug, Remi silently alerting tech

**2:45 — Command bar demo (15 sec)**
- Type: "Generate shift handoff report"
- Show Claude API response with full shift context

---

## Why This Wins

**Innovation (30%):** First AI agent purpose-built for the retail pharmacy counter. Diversion pattern detection across shift cycles. Dual-mode architecture serving two distinct users on one device.

**Technical Complexity (25%):** Agentic reasoning loop with tool-use pattern. Multi-step discrepancy investigation. Cross-mode state sharing. Live simulation engine. Claude API with full shift context injection.

**Real-World Impact (20%):** DEA violations carry up to $15,691 per infraction. One caught diversion event pays for years of software. Independent pharmacies have no enterprise-grade tools. Built by someone who actually worked the counter.

**UI/UX (15%):** Two completely distinct visual modes — dark clinical dashboard for techs, warm accessible interface for patients. Reasoning panel makes AI thinking visible. EKG heartbeat responds to activity. Zero onboarding required.

**Presentation (10%):** Personal story from lived experience. Demo creates a visceral moment judges immediately understand.

---

## The Vision Beyond the Hackathon

**Hardware:** Remi lives on a dedicated device at the pharmacy counter — 8-inch touchscreen, built-in mic/speaker, swivels between tech-facing and patient-facing. Built on the same Raspberry Pi 4 + OLED platform as the builder's existing alfred.ai robot project. Independent pharmacies pay ~$300/month SaaS. No enterprise IT required.

**V2 Features:**
- PMS integration (PioneerRx, Datascan) for real transaction data
- Biennial inventory assistant — walks tech through DEA biennial inventory process
- Ordering intelligence — recommends what to order from Cardinal Health based on fill velocity
- Multi-pharmacy dashboard for owner-pharmacists managing multiple locations
- Prescriber office communication — agentic fax and callback management

---

## Builder

**Anam Ahmed**
MS Computer Science (Align), Khoury College — Northeastern University, 2027
BA Psychology, Minor in Cognitive Science — Rutgers University, 2023
Active NJ Pharmacy Technician License
AI Researcher, NU Launch Labs

*Built from firsthand experience behind the pharmacy counter.*

---

## Hackathon

**FutureAI Global Hackathon 2026**
Tracks: Healthcare AI + AI Agents & Automation
Devpost: https://futureai-global-hackthon.devpost.com
Deadline: July 5, 2026

---

*Remi — because every pharmacy counter deserves a coworker who never forgets.*