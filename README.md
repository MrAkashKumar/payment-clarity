# Payment Clarity

**A local payment-investigation workspace for payment operations, relationship managers (RMs), and Compliance.** It explains which reviews a payment requires, shows supporting policy and transaction evidence, and helps prepare a focused information request for human review.

This implements **Use Case 1 — Payment Investigation Agent** from the [Julius Baer sidequest](https://github.com/Singhacks-2026/juliusbaer-sidequest), using supplied synthetic data. It does not approve, release, block or execute payments, or send customer messages.

## Contents

- [Quick start](#quick-start)
- [How to use the app](#how-to-use-the-app)
- [Configure live AI](#configure-live-ai)
- [Project structure](#project-structure)
- [Architecture](#architecture)
- [Generate submissions](#generate-submissions)
- [Local API](#local-api)
- [Checks](#checks)
- [Troubleshooting](#troubleshooting)
- [Limitations and further documentation](#limitations-and-further-documentation)

## Quick start

### Requirements

| Requirement | When needed |
|---|---|
| Python 3.10 or newer | App, investigation core and submission runner |
| A browser | Local interface |
| Node.js | Only for JavaScript checks; not for running the app |
| Provider credentials and internet | Only for live AI investigations |

**No `pip install`, `npm install`, database setup or frontend build is required.** The Python runtime uses only the standard library; `requirements.txt` documents this choice.

Commands use macOS/Linux shell syntax. On Windows, use your Python 3.10+ command (`py` or `python`) and equivalent environment-variable syntax.

### 1. Open the project directory

From the directory containing the project:

```bash
cd payment-clarity
python3 --version
```

If you copied the project elsewhere, use that directory instead. Keep the complete folder, including `reference/`. Copying just `web/` or the three-file submission package is insufficient.

### 2. Start the application

```bash
python3 server.py --port 8780
```

Expected output:

```text
Payment Clarity is running at http://127.0.0.1:8780
Local synthetic-data demo. Press Ctrl+C to stop.
```

Open **[http://127.0.0.1:8780](http://127.0.0.1:8780)**. Keep the terminal running while using the app. Stop it with **Ctrl+C**.

The server uses live AI when all provider settings are present; otherwise it uses deterministic evidence mode. To explicitly run **without API calls**, even if `.env` already contains a key:

```bash
LLM_API_KEY= python3 server.py --port 8780
```

The empty environment variable overrides the file value for this process only; it does not edit `.env`.

### 3. Check availability

In a second terminal:

```bash
curl http://127.0.0.1:8780/api/health
```

The response includes `status`, input `version`, `live_ai_configured`, `payments` and `clients`. The supplied snapshot has **184 payments and 50 client profiles**. A true configuration flag means settings exist; it does not verify authentication, quota or provider availability.

## How to use the app

1. **Select a payment.** Search by payment ID, client ID, beneficiary or currency. P50002 is selected initially.
2. **Ask a question.** For example, “What review is required and what is the next action?” Select **Investigate**.
3. **Inspect the result.** Read required checks, payment facts, related transfers, assumptions and discrepancies. Select **View policy evidence** to inspect the supporting clause.
4. **Prepare the handoff.** Select **Prepare RM request**, or **Prepare analyst note** for cases without an external information request.
5. **Edit and review.** Customer preview requires a reviewed draft and a case that needs an external request. Editing invalidates review. Preview does not send the message.
6. **Export the case.** **Export case** downloads the investigation, local draft and review history as JSON.

Drafts and review events are kept in the current browser's local storage, scoped by payment and source version. They are not shared across users, devices, browsers or different localhost origins/ports. Clearing browser storage removes them. Restart after changing source files; a changed source version invalidates earlier review state.

### Demo cases

| Payment | Scenario | Expected review outcome |
|---|---|---|
| **P50002** | USD 85,000; Singapore client; code AE conflicts with Hong Kong label | RM review + destination review |
| **P50003** | Three matching transfers to Northstar Trading total CHF 110,000 | Potential structuring review + Compliance escalation under the stated exercise assumptions |
| **P50001** | USD 125,000; Singapore client; destination AE | Enhanced review + RM review + destination review |
| **P50000** | USD 12,000; no trigger established by the implemented checks | Analyst review; no automatic release authorisation |

P50003 groups with P50180 and P50181. P50182 has a different client; P50183 has a different beneficiary. They are excluded.

## Configure live AI

AI is optional for exploring the app, but the official Use Case 1 challenge requires an LLM agent. Evidence-only execution does not satisfy that requirement by itself.

### Configuration file

From the project directory, create `.env` only if it is missing:

```bash
if [ ! -f .env ]; then
  cp .env.example .env
fi
chmod 600 .env
```

Edit `.env` in your editor using these settings:

```dotenv
LLM_API_KEY=replace-with-your-own-key
LLM_MODEL=gpt-4.1-mini
LLM_CHAT_URL=https://api.openai.com/v1/chat/completions
```

Do not overwrite a working key with the placeholder. `.env` is excluded by `.gitignore`; never commit or share it. It is not served to the browser. Already-set `LLM_` environment variables take precedence over the file.

Restart the server and reload the browser after changes. This OpenAI endpoint is the tested configuration. Other providers must support the adapter's chat-completions, strict tool-calling and structured-output contracts; changing the URL alone does not guarantee compatibility.

Live mode sends the selected synthetic case, question and tool evidence to the provider and may incur API charges. The adapter requests `store: false`; that is not a zero-retention guarantee.

### Execution modes

| Label | Meaning |
|---|---|
| **Evidence mode · no live AI** | Deterministic checks ran without the model; the result is a case checklist rather than a model-authored response to the question. |
| **Live AI + verified checks** | The model used tools and its explanation passed implemented validation. Human semantic review is still necessary. |
| **Evidence mode · AI unavailable** | A provider call or output check failed. Verified case checks remain available and the result records a sanitised `ai_error_code`. |

The model must first call a tool. Calls are scoped to the selected payment, client and beneficiary. Output schemas and citations are checked; Python calculates the numbers. The adapter rejects several unsupported narrative patterns and allows one rewrite within its time/call budget. These checks do not prove that every accepted sentence is correct.

## Project structure

```text
payment-clarity/
├── README.md                    # Setup, usage and structure
├── PRD.md                       # Product requirements and target design
├── VERIFICATION.md              # Earlier verification record
├── server.py                    # Local HTTP server and API
├── main.py                      # Unchanged official runner
├── requirements.txt             # Standard-library-only runtime note
├── .env.example                 # Safe provider configuration template
├── .env                         # Local credentials, if configured; ignored
├── .gitignore
├── web/
│   ├── index.html               # Working interface
│   ├── styles.css               # Responsive styles
│   ├── app.js                   # Investigation, draft and review workflow
│   └── favicon.svg
├── agent/
│   └── agent.py                 # Live tool loop, validation and fallback
├── core/
│   ├── data.py                  # Source validation and versioning
│   └── investigation.py         # Deterministic checks and results
├── tools/
│   ├── payment_tools.py         # Payment/history lookup and grouping
│   ├── client_tools.py          # Client profile lookup
│   └── policy_tools.py          # Policy retrieval interface
├── rag/
│   └── pipeline.py              # Cached lexical policy index
├── reference/
│   ├── clients.csv
│   ├── payments.csv
│   ├── policies/                # Five relevant policies + four decoys
│   ├── questions.json           # Reference copy
│   ├── DATA_NOTES.md
│   ├── SUBMISSION_GUIDE.md
│   ├── EVALUATION_CRITERIA.md
│   └── UPSTREAM-LICENSE
├── questions/
│   └── questions.json           # Ten questions used by main.py
├── submission.json              # Latest official-runner output
├── submission-package/
│   ├── Solution.py              # Wrapper requiring the parent project
│   ├── answers.json             # Separately saved answer snapshot
│   └── README.md                # Detailed question-by-question answers
├── scripts/
│   └── audit_reference.py       # Read-only data audit
├── tests/
│   ├── test_core.py
│   ├── test_live_adapter.py
│   └── test_frontend.cjs
├── reference-audit.json         # Saved audit result
├── reference-manifest.json      # Snapshot provenance
└── design/                      # Earlier concepts, not the running app
```

Package initialisers and Python cache files are omitted. The neighbouring `incident-clarity` folder belongs to Use Case 2 and is not needed to run this app.

## Architecture

```text
Browser UI → server.py ──┐
main.py ────────────────┼─→ agent.run_agent(question, payment_id)
Solution.py ────────────┘       ├─ deterministic investigation core
                               │   ├─ payment/client/history tools
                               │   ├─ Decimal amount/grouping calculations
                               │   └─ policy retrieval + source clauses
                               └─ configured LLM tool loop
                                   ├─ scoped read-only tools
                                   ├─ explanation validation
                                   └─ live result or labelled fallback
```

The loader validates inputs and computes a source version. The retrieval layer indexes short policy documents locally. The core evaluates global/regional rules, destination codes and related transfers, retaining source evidence and explicit assumptions. The model adds qualitative explanation; it does not replace tool-calculated numbers.

The shared interface is `run_agent(question, payment_id)`. The evidence-only core is `investigate(payment_id, question)`. Note their different argument order when importing directly.

| Component | Current technology |
|---|---|
| Backend | Python `ThreadingHTTPServer` |
| Interface | HTML, CSS and vanilla JavaScript |
| Retrieval | Cached lexical index; no external vector database |
| Arithmetic | Python `Decimal` |
| Inputs | Local CSV and Markdown files |
| Draft storage | Browser local storage |
| Optional AI | HTTP chat-completions adapter, tested with OpenAI |

This implementation uses a smaller stack than the target FastAPI/React design in the PRD. Production authentication, bank connectors and shared workflow storage are not implemented.

## Generate submissions

Run these commands from the **`payment-clarity` directory**.

### Official ten-question output

```bash
python3 main.py --questions questions/questions.json --output submission.json
```

This invokes the shared agent for each official question and **overwrites `submission.json`** when complete. With credentials configured, it makes live provider calls. The runner may remain quiet while processing.

The result is a JSON array of ten objects containing `question_id`, `payment_id`, `answer`, `citations`, `facts` and `tools_used`, plus question text and investigation details. Do not change official question IDs, payment IDs or wording. Inspect every `mode` and any `ai_error_code` before submitting. See the [submission guide](reference/SUBMISSION_GUIDE.md).

To run without API usage and preserve the live artifact:

```bash
LLM_API_KEY= python3 main.py \
  --questions questions/questions.json \
  --output /tmp/payment-clarity-evidence.json
```

### Three-file package

The package uses the complete parent project and cannot run standalone.

```bash
# Generate new package answers with the configured agent.
python3 -B submission-package/Solution.py

# Generate offline answers to a separate file.
python3 -B submission-package/Solution.py \
  --evidence-only --output /tmp/payment-clarity-package-evidence.json

# Refresh the package from the official output, without API calls.
python3 -B submission-package/Solution.py --snapshot submission.json
```

The last command validates and copies the saved results; it does not rerun investigations. `answers.json` is the requested package filename. The official Use Case 1 convention remains `submission.json`.

### Saved results at this documentation update

Checked **7 September 2026**:

| Artifact | Answers | Modes |
|---|---:|---|
| `submission.json` | 10 | 7 live AI; 3 fallbacks: Q01, Q02, Q09 |
| `submission-package/answers.json` | 10 | Earlier snapshot: 8 live AI; 2 fallbacks: Q01, Q09 |

These are different runs and are not automatically synchronised. `VERIFICATION.md` describes an earlier run. Inspect the actual JSON for current results; counts can change when regenerated. No private grading key has been run.

## Local API

The server binds to `127.0.0.1`, accepts local hostnames and rejects foreign-origin writes. It is a single-user demo, not an authenticated public API.

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/health` | Availability, input version, configuration flag and record counts |
| GET | `/api/payments` | Supplied payment records |
| POST | `/api/investigate` | Investigate a payment using the shared agent |

With the server running:

```bash
curl --request POST http://127.0.0.1:8780/api/investigate \
  --header 'Content-Type: application/json' \
  --data '{"payment_id":"P50002","question":"What review is required and why?"}'
```

This uses the server's current mode and may call the provider. The API accepts JSON requests up to 8 KB. A supplied question must be 1–2000 characters after trimming; an omitted question uses the server default. Unknown payment IDs return 404; invalid input returns 400. An AI fallback can return HTTP 200 with `mode: "fallback"`; HTTP success alone does not establish live AI success.

## Checks

```bash
python3 -m unittest discover -s tests -v
node tests/test_frontend.cjs
node --check web/app.js
python3 scripts/audit_reference.py
```

The Python suite contains 23 tests covering the source records, review rules, threshold boundaries, grouping exclusions, missing/changed policies and provider guards. Live-adapter tests use mocks rather than billable calls. Five JavaScript checks exercise review gating, editing, persistence, source changes and internal-only cases. They are not a full browser/accessibility audit. The audit script prints JSON without changing the source files.

## Troubleshooting

| Symptom | Action |
|---|---|
| `python3` not found | Install/select Python 3.10+ or use your system's equivalent command. |
| `Address already in use` | Stop the previous server with Ctrl+C, or use `python3 server.py --port 8781` and open `http://127.0.0.1:8781`. |
| Browser cannot connect | Keep the terminal running, check the port and `/api/health`. Open the HTTP URL, not `web/index.html` directly. |
| Configuration changes do not appear | Restart Python and reload the browser; check environment variables overriding `.env`. |
| `authentication` / `access_denied` | Check the local key and provider project access without exposing credentials in logs. |
| `quota_or_rate_limit` | Check the provider account limits; evidence mode remains available. |
| `model_or_endpoint` | Check the configured model and HTTPS endpoint. |
| `timeout` / `network` | Check connectivity and retry, or use evidence-only mode. |
| `response_validation` | AI wording failed a guard. Inspect deterministic evidence and the optional `ai_error_reason`. |
| Customer preview disabled | Review a non-empty draft; internal-only cases do not enable customer preview. |
| Missing files or import errors | Run from the complete project with the documented structure. |
| Source edits not visible | Restart to reload cached data and the policy index. |

## Limitations and further documentation

- The policies are synthetic exercise rules, not production banking policy or legal conclusions. A policy trigger does not establish suspicious activity.
- Same-date grouping approximates a rolling 24-hour window. Cross-currency thresholds use disclosed exercise-only 1:1 equivalence; production requires approved FX and timestamps.
- Actual release status, ownership, deadlines, settlement state and customer documents are absent.
- Browser-local review history is demonstration state, not an immutable bank audit trail or authorisation. No payment mutation or external messaging tool exists.
- Accepted AI prose still requires semantic review. Implemented guards cannot guarantee every statement's correctness.
- SSO, live bank integrations, shared storage, production hosting and a full device/accessibility evaluation are not included. Real bank data needs approved access, processing and retention controls.
- Bank-wide reach, accuracy rates and time savings have not been measured.

Further reading:

- [PRD](PRD.md): requirements, priorities, target architecture and impact assumptions.
- [Detailed answers and package guide](submission-package/README.md).
- [Verification record](VERIFICATION.md): earlier checks and their limits.
- [Data notes](reference/DATA_NOTES.md): source interpretation and exercise assumptions.
- [Evaluation criteria](reference/EVALUATION_CRITERIA.md) and [submission guide](reference/SUBMISSION_GUIDE.md).
- [Source license](reference/UPSTREAM-LICENSE).
- Adapter references: [function calling](https://developers.openai.com/api/docs/guides/function-calling), [structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs), [GPT-4.1 mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini).
