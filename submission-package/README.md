# Payment Clarity — Use Case 1 payment investigation package

**Payment Clarity helps payment operations and relationship managers understand which reviews a payment requires, why they apply, and what evidence or customer information to collect next.** It combines payment/client lookups, policy retrieval, exact calculations and a guarded AI explanation in one investigation workspace.

This is the original Payment Clarity project, aligned with **Use Case 1 — Payment Investigation Agent** in the [official Julius Baer sidequest repository](https://github.com/Singhacks-2026/juliusbaer-sidequest). It is not the production incident investigator. The [questions in your fork](https://github.com/MrAkashKumar/juliusbaer-sidequest/blob/main/usecase-1-payment-investigation-agent/questions/questions.json), official questions and local questions were compared on 5 September 2026 and are identical, including question IDs, payment IDs, wording and order.

## The three files

| File | Contents |
|---|---|
| `Solution.py` | A runnable entry point that calls the existing Payment Clarity agent and investigation core; validates question identity and answer structure |
| `answers.json` | Ten actual results packaged from the existing verified `submission.json`, preserving evidence, facts, tool activity and execution modes |
| `README.md` | Project explanation, explicit answers to the ten questions, architecture, limitations and run instructions |

**Keep this folder inside the complete `payment-clarity` project.** `Solution.py` reuses its `agent`, `core`, `tools`, `rag`, `reference` and `questions` directories. These three files alone are not a standalone implementation. Reusing the working code keeps app and export behaviour consistent.

The supplied `answers.json` is a validated copy of an existing run, not a new live run. It contains **eight accepted live AI responses and two labelled evidence fallbacks (Q01 and Q09)**. Those fallbacks remain disclosed; packaging does not turn them into live responses. The explanations below are a human-readable synthesis of the deterministic payment facts and policy checks, not hardcoded executable answers.

## What problem does it solve?

The specific task is to connect a payment with its client's applicable regional rules, destination code, other transfers to the same beneficiary, and the evidence behind the recommendation. The RM then needs a focused information request rather than an unexplained escalation.

For example, P50002 is below the global enhanced-review amount threshold, but Singapore RM review and an AE destination review still apply. Looking only at the global amount would miss required work. P50003 looks small individually, but its related same-day payments create a reviewable pattern.

The implementation retrieves these inputs, performs the checks, shows source clauses and assumptions, and prepares an editable RM request. A local review gate controls the customer preview. It does not approve, release, block or execute payments, or send messages.

These are synthetic exercise policies and records. The repository does not establish what Julius Baer currently does manually, its actual customer volumes, or the amount of time this product would save in production.

## Clear answers to the ten official questions

### Q01 — Should P50000 require enhanced review?

**No enhanced review is triggered by the supplied amount rule.** P50000 is USD 12,000, below the global threshold of more than USD 100,000 equivalent. Destination code SG is not the supplied high-risk code AE. Its client is in UAE; client location is not a substitute for destination code. The UK beneficiary-country label conflicts with SG, so record the discrepancy and use the code as required by the exercise. No review trigger is established by the implemented checks; this is not payment-release authorisation.

Sources: [global policy](../reference/policies/global_payment_policy.md), [destination list](../reference/policies/high_risk_jurisdictions.md), [payment records](../reference/payments.csv).

### Q02 — What review applies to P50001 and why?

**Enhanced review, RM review and additional destination review.** The USD 125,000 payment exceeds the global USD 100,000 threshold and the Singapore enhanced-review threshold. Its Singapore client also meets the more-than-USD-75,000 RM rule. Destination AE triggers additional destination review. This single payment alone is not a multiple-transfer structuring pattern.

Sources: [global policy](../reference/policies/global_payment_policy.md), [Singapore procedure](../reference/policies/regional_singapore.md), [destination list](../reference/policies/high_risk_jurisdictions.md).

### Q03 — What risk indicators and additional review apply to P50002?

**RM review and additional destination review.** The USD 85,000 payment exceeds Singapore's USD 75,000 RM threshold, but not the USD 100,000 enhanced-review threshold. Code AE is authoritative and triggers destination review even though the country label says Hong Kong. Record that discrepancy; it is not proof of wrongdoing. The supplied matching group contains only this payment, so no multiple-transfer pattern is established.

Sources: [Singapore procedure](../reference/policies/regional_singapore.md), [destination list](../reference/policies/high_risk_jurisdictions.md), [payment records](../reference/payments.csv).

### Q04 — Is there a possible transaction-splitting pattern for C2003?

**Yes: review the pattern and escalate to Compliance under the Swiss procedure.** On 11 April 2026, C2003 paid Northstar Trading CHF 45,000 (P50003), CHF 35,000 (P50180) and CHF 30,000 (P50181): **CHF 110,000 combined**. Exclude P50182 because it belongs to another client and P50183 because it has a different beneficiary.

The exercise permits explicitly labelled 1:1 currency equivalence and a same-calendar-date approximation to 24 hours. Under those assumptions, the group exceeds the global USD 100,000-equivalent pattern threshold. Approved FX and actual timestamps are missing. This is a potential structuring indicator, not proof of intent. The individual CHF 45,000 payment does not meet Swiss amount-review thresholds; do not confuse the group rule with the CHF 120,000 enhanced-review rule.

Sources: [payment records](../reference/payments.csv), [global policy](../reference/policies/global_payment_policy.md), [Swiss procedure](../reference/policies/regional_switzerland.md).

### Q05 — Which policies should be retrieved for P50001 before recommending release?

Retrieve **`global_payment_policy.md`, `regional_singapore.md`, `high_risk_jurisdictions.md` and `investigation_procedure.md`**. They establish the global amount rule, the client's regional reviews, AE destination treatment and the investigation workflow. Inspect the supporting payment/client facts and unresolved information as well. Policy retrieval does not itself authorise release, and this application does not recommend release while required reviews remain outstanding.

Sources: those four [policy documents](../reference/policies/).

### Q06 — What are facts versus assumptions for P50002?

**Facts:** P50002 belongs to C2002, whose region is Singapore; USD 85,000 was recorded for Pacific Holdings on 27 April 2026; the destination code is AE but the country label is Hong Kong. There is one payment in the matching client/beneficiary/date/currency group. The supplied rules require RM and destination review.

**Assumptions and unknowns:** the same date approximates 24 hours because timestamps are absent. The code-authoritative rule comes from the exercise. Customer intent, supporting documents and actual operational release status are not provided. No currency conversion is needed for this USD amount comparison.

**Recommendation:** prepare an RM request for payment purpose, supporting invoice/agreement, beneficiary relationship and confirmation of intended destination. Record the discrepancy and required reviews without asserting suspicious activity or approving release.

Sources: [payment records](../reference/payments.csv), [client records](../reference/clients.csv), [data notes](../reference/DATA_NOTES.md), [Singapore procedure](../reference/policies/regional_singapore.md).

### Q07 — What information is needed for the potential structuring escalation?

Request the payment purpose, supporting invoices or agreements, relationship with Northstar Trading, reasons for separate transfers, intended destination and actual timestamps. For a production assessment, obtain approved FX evidence rather than assume CHF/USD parity. Attach the exact three-payment group, total, relevant policy clauses and stated assumptions to the Compliance referral. The supplied Swiss policy already requires escalation of potential structuring; collecting information should not be treated as permission to postpone a required escalation indefinitely.

Sources: [Swiss procedure](../reference/policies/regional_switzerland.md), [investigation procedure](../reference/policies/investigation_procedure.md). The document checklist is a proposed evidence request; it is not an additional quoted policy requirement.

### Q08 — What regional threshold applies to P50004?

The client C2003 is in **Switzerland**: payments **above CHF 80,000 equivalent require RM review**, and **above CHF 120,000 equivalent require enhanced review**. P50004 is CHF 48,000 and meets neither amount trigger. The global more-than-USD-100,000-equivalent rule also remains applicable; regional rules do not cancel it. Cross-currency global comparisons in this demo use the explicitly labelled exercise assumption. Thresholds are strictly “above,” not “at or above.”

Sources: [Swiss procedure](../reference/policies/regional_switzerland.md), [global policy](../reference/policies/global_payment_policy.md), [client records](../reference/clients.csv).

### Q09 — What if an amount is below the global threshold but the destination is high-risk?

**Recommend additional destination review regardless of the low amount.** P50005 is CHF 47,000 for a Swiss client, below the applicable amount thresholds under the exercise assumptions, but destination AE is on the supplied high-risk list. Request supporting context and document the destination trigger. Do not infer an enhanced amount review, payment release or wrongdoing from this alone.

Sources: [global policy](../reference/policies/global_payment_policy.md), [destination list](../reference/policies/high_risk_jurisdictions.md), [Swiss procedure](../reference/policies/regional_switzerland.md).

### Q10 — What investigation workflow should be followed?

1. Retrieve P50006 and its client profile; establish amount, currency, region, destination and recorded date.
2. Retrieve applicable supplied policies and retain source evidence.
3. Check amount and destination indicators using deterministic calculations.
4. Inspect client history and group by client, beneficiary, time window and currency.
5. Separate facts from assumptions; identify missing timestamps, FX or documents.
6. Record the grounded recommendation and route it for human review.

P50006 is SGD 24,110.41, client C2023 in the UK, destination HK. There is no supplied UK-specific regional procedure; do not invent one. The current checks establish no review trigger under the explicit exercise assumptions, not permission to release the payment.

Source: [investigation procedure](../reference/policies/investigation_procedure.md), with [payment](../reference/payments.csv) and [client](../reference/clients.csv) records.

## Architecture and official requirements

```text
Working UI / official main.py / this Solution.py
  → shared run_agent(question, payment_id)
  → payment + client + history tools
  → deterministic Decimal amount and grouping calculations
  → cached lexical policy retrieval with original sources
  → optional configured LLM tool loop and output validation
  → grounded answer, citations, facts, tools used, assumptions and mode
```

The [official architecture requirements](https://github.com/Singhacks-2026/juliusbaer-sidequest/blob/main/usecase-1-payment-investigation-agent/AI_ARCHITECTURE_REQUIREMENTS.md) call for policy RAG, structured tools, an LLM agent loop, deterministic calculations, grounding and explicit uncertainty. Payment Clarity implements those layers. The live loop uses scoped read-only tools, strict schemas, citation checks and bounded calls; rejected responses use the labelled evidence engine. The two existing fallbacks mean this artifact should not be described as ten successful live AI investigations. Deterministic-only execution is useful for checks but does not by itself meet the live-agent requirement.

The working prototype uses Python's standard-library HTTP server and vanilla JavaScript/CSS. Its 184 supplied payments, 50 client profiles and policy sources remain in the parent project. Future bank adapters would map authorised payment/client/policy systems to these read-only tool contracts. Production authentication, audit storage, FX and timestamp feeds are still required; integration with every system is not implemented.

### Priorities and impact

P0 is correct review routing with visible evidence, accurate grouping and clear uncertainty. P1 is reducing RM back-and-forth with an editable, reviewable information request. P2 is authenticated integrations and operational measurement.

Illustrative pilot target only: 100 cases/day × 10 minutes less preparation per case = 1,000 minutes, or **16.7 staff-hours/day saved**. Neither that volume nor that saving has been measured at Julius Baer. Measure handling time, repeat document requests, missed review triggers and incorrect escalations before claiming impact. The dataset count is not a bank-wide customer-reach estimate.

## Run the requested package

From the parent `payment-clarity` directory:

```bash
# Generate new answers using the existing configured agent.
python3 -B submission-package/Solution.py

# Offline deterministic checks; write separately so the live snapshot is retained.
python3 -B submission-package/Solution.py --evidence-only --output /tmp/payment-clarity-evidence.json

# Reproduce the included package from the existing run without API calls.
python3 -B submission-package/Solution.py --snapshot submission.json
```

The wrapper validates question IDs, payment IDs, wording, ordering and required fields before writing. It does not select an answer based on a question ID. Credentials remain in the parent's local `.env`; no key is included in this package.

## Official submission format is still Use Case 1

The [official guide](https://github.com/Singhacks-2026/juliusbaer-sidequest/blob/main/usecase-1-payment-investigation-agent/SUBMISSION_GUIDE.md) specifies one result per official question, with `question_id`, `payment_id`, `answer`, `citations`, `facts` and `tools_used`. Including `question` is recommended. The existing official runner remains unchanged:

```bash
python3 main.py --questions questions/questions.json --output submission.json
```

`answers.json` is the filename you requested for this delivery package. It does not replace the official `submission.json` convention, nor make the three-file Use Case 2 contract apply here. For official submission, keep the complete payment project and follow the guide. No GitHub submission or private grading has been performed.

## Verification and remaining limits

Package checks cover exact equality of the linked/official/local question sets, ten matching answer identities, preserved snapshot content, required field types, offline reproduction and delegation to the shared agent. The existing core has 23 Python regression tests and five JavaScript state checks.

Generated AI prose still requires semantic review. Date-only grouping, exercise currency equivalence, missing operational payment status and browser-local review state are prototype limitations. Review gates are not bank authorisations. No component releases funds or sends a customer message.
