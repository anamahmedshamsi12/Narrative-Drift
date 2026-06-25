# Remi — Pharmacy Domain Reference

This document explains the real-world pharmacy concepts the codebase models, so a contributor without pharmacy background can read `index.html` and understand *why* the logic is shaped the way it is.

## NCPDP Reject Codes

When a pharmacy submits a prescription claim electronically, the patient's insurance (the "payer," processed through a PBM — Pharmacy Benefit Manager) can reject it with a standardized NCPDP (National Council for Prescription Drug Programs) reject code. The codes covered in `REJECT_CODES` (used by the `decode_reject` tool):

| Code | Meaning | Typical real-world fix |
|---|---|---|
| **70** | Product/service not covered — usually a DAW (Dispense As Written) code mismatch: the prescriber's DAW instruction doesn't match what the plan requires. | Rebill as DAW-0 (pharmacist-selected generic substitution allowed) or get the prescriber to confirm a DAW-1 (brand medically necessary) override. |
| **75** | Prior authorization required, frequently seen in practice as "refill too soon" — the days-supply math says the patient still has medication left. | Request a vacation override from the PBM (for legitimate early refills, e.g. travel), or initiate a formal prior authorization (PA). Cash-pay alternatives like GoodRx are often offered while this is sorted out. |
| **76** | Plan limitations exceeded — typically a quantity limit (e.g. plan caps a drug at 30 tablets/month, prescriber wrote 90). | Check the fill against plan quantity limits; may need a quantity-limit override or PA. |
| **88** | DUR (Drug Utilization Review) reject — the claims system flagged a potential interaction, duplication, or other clinical conflict. | Pharmacist must review for actual interaction/duplication; if appropriate, submit a DUR override using a "level of effort" code documenting the clinical judgment made. |

These four were chosen because 70 and 75 appear in the scripted shift timeline (`events` array), and 76/88 round out the set with two more codes a tech encounters routinely, so `decode_reject` is useful beyond just the demo script.

## DEA Controlled Substance Schedules

The U.S. Drug Enforcement Administration (DEA) classifies controlled substances into five schedules by abuse potential and accepted medical use. The drugs modeled in `state.cs` are:

| Drug (as in `drugNames`) | Schedule | Why it matters here |
|---|---|---|
| Oxycodone 5mg | Schedule II | High abuse potential. Schedule II drugs require the strictest counting, record-keeping, and DEA reporting — this is why the discrepancy/diversion storyline centers on oxycodone specifically, not on a Schedule III/IV drug. |
| Hydrocodone 10mg | Schedule II | Same tier as oxycodone (re-scheduled from III to II in 2014). |
| Adderall 20mg (amphetamine) | Schedule II | Stimulant; same strict counting requirements. |
| Xanax 0.5mg (alprazolam) | Schedule IV | Lower abuse potential than Schedule II, but still a controlled substance requiring perpetual inventory and counts — included so the state board demonstrates that not every CS drug carries equal regulatory weight. |

Schedule II drugs in particular require **perpetual inventory** — every single unit dispensed, received, returned, or wasted must reconcile to a running count, with no tolerance for unexplained loss. This is the real-world basis for `state.csLog` (the transaction ledger) and `trace_discrepancy()`: a pharmacy that can't account for a Schedule II gap has a federal compliance problem, not just a bookkeeping one.

## OBRA '90 Counseling Requirement

The Omnibus Budget Reconciliation Act of 1990 (OBRA '90) is federal law requiring pharmacists (via Medicaid initially, now effectively universal practice) to **offer** counseling to every patient on a new or changed prescription — and to document that the offer was made, regardless of whether the patient accepts. The pharmacist doesn't have to counsel every patient, but the *offer* and the patient's response must happen and be recorded.

This is modeled in Patient Mode's `'counseling'` step in `renderPatientStep()`: Remi makes the offer conversationally as part of the pickup flow, captures the patient's response, and — if the patient has a question — routes it to the pharmacist via the `'counseling-question'` step rather than letting Remi answer clinical questions herself (consistent with the "never make clinical decisions" rule baked into both system prompts).

## DEA Form 106

DEA Form 106 is the **Report of Theft or Loss of Controlled Substances**, filed with the DEA's Diversion Control Division when a registrant (the pharmacy) discovers a theft or "significant loss" of controlled substances — which includes suspected employee diversion, not just break-ins. It must be filed within a defined window of discovery and typically triggers internal escalation (pharmacist-in-charge, pharmacy manager, sometimes corporate security) alongside the federal filing.

In the codebase, the `generate_form106` tool models the *drafting* step: given a drug's discrepancy history, it returns whether filing is recommended (`form_106_recommended: history.length >= 2` — i.e., a repeated unexplained gap, not a single isolated count error) and draft narrative language. It does not itself decide to file or notify anyone — that judgment, and the decision of how to phrase it to the tech, is left to Claude's reasoning in `runAgentTurn()`, consistent with this app modeling Remi as an assistant that recommends, not one that takes regulatory action unilaterally.

## Glossary

| Term | Meaning |
|---|---|
| **PBM** | Pharmacy Benefit Manager — the third party (e.g. CVS Caremark, Express Scripts) that processes insurance claims for prescriptions on behalf of the health plan. |
| **DAW** | Dispense As Written — a code on a prescription claim indicating whether brand or generic substitution is allowed/required. |
| **PA** | Prior Authorization — an approval the prescriber must obtain from the payer before a drug will be covered. |
| **DUR** | Drug Utilization Review — an automated and/or pharmacist clinical check for interactions, duplications, or other issues at the point of dispensing. |
| **Perpetual inventory** | A running, continuously reconciled count of controlled substance stock, required for Schedule II drugs — every dispense/receipt must be logged against it. |
| **Count cycle** | A discrete physical count of a controlled substance's on-hand quantity, compared against the expected (perpetual inventory) count to detect discrepancies. Modeled as `ev.n` on discrepancy events. |
| **Diversion** | The illegal redirection of controlled substances from legitimate medical channels — e.g. an employee removing tablets for personal use or resale. Suspected diversion is what `generate_form106` and the diversion-pattern storyline are about. |
| **Diversion Control Division** | The DEA office controlled substance registrants report theft/loss to (where Form 106 goes). |
| **NCPDP** | National Council for Prescription Drug Programs — the standards body whose claim reject-code taxonomy (`REJECT_CODES`) is used industry-wide for e-prescribing and claims adjudication. |
| **GoodRx** | A consumer prescription discount service; pharmacies commonly compare its cash price against a patient's insurance copay when the copay is high or a claim is rejected. |
| **FDA shortage list** | The FDA's published list of drugs in active national shortage — modeled here for Ozempic (GLP-1 agonists have had real, prolonged shortages), driving the `check_inventory` tool's `fda_shortage_active` flag and the proactive reorder/patient-notification recommendations Claude makes around it. |
| **Days supply** | How many days a dispensed quantity is intended to last at the prescribed dose — the basis for "refill too soon" (reject code 75) calculations. |
