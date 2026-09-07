# Payment Clarity

**A working local payment-investigation app using the supplied synthetic data.**

## Start the app

Requires Python 3.10 or newer. No package installation, database, or API key is needed for evidence mode.

```bash
cd /Users/akash/Engineering/Codex-App-work/SingHacks/payment-clarity
python3 server.py --port 8780
```

Open [Payment Clarity](http://127.0.0.1:8780). Stop with Ctrl+C. If that port is occupied, choose another port with `--port`.

## What works

- Search all 184 payment records by payment ID, client, beneficiary, or currency.
- Calculate global/regional amount checks and destination-review requirements.
- Inspect matching related transfers, exact Decimal totals, and underlying payment IDs.
- Retrieve relevant policy documents with a cached lexical index; exclude irrelevant administrative notes.
- Show conflicts, source clauses, assumptions, and actual tool activity.
- Prepare an editable RM request or internal analyst note.
- Mark a draft reviewed and preview customer wording. Editing or changing the source version invalidates review.
- Save synthetic drafts/review events on this browser and export a case as JSON.
- Run the unchanged official command-line entry point against ten supplied questions.

**Default mode is deterministic evidence mode.** It returns the complete structured investigation checklist for the selected payment. It is not a live natural-language LLM agent and does not satisfy the challenge's live-LLM requirement on its own. Questions are sent to the model only when the optional provider is configured.

## Optional live AI

Copy `.env.example` to `.env` and enter the endpoint, model, and key for an approved tool-calling provider that supports the chat-completions request/response contract:

```text
LLM_CHAT_URL=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4.1-mini
LLM_API_KEY=your-key
```

This configuration uses OpenAI. Supply your own key in the local `.env` file. Restart the server after configuring it. Never share or commit `.env`.

The adapter sends the selected synthetic case, verified evidence, and question to that provider. It requires initial tool use, uses strict tool/output schemas, restricts citations to verified filenames, and rejects numerical prose, threshold prose, and several unsupported pattern or review-type phrases. Exact threshold comparisons stay in the deterministic evidence panel. One rewrite is allowed within the shared time and tool-call budget. Authentication, quota/rate-limit, network, and validation failures have sanitised error codes. Redirects are rejected to prevent credential forwarding. Requests use `store: false`; this is not a claim of zero data retention. If the model fails, skips tool use, or returns invalid output, the app falls back to the labelled evidence engine. The local OpenAI integration has been tested with synthetic cases. Qualitative AI prose still needs human review; structural validation is not a guarantee of semantic correctness.

## Run the checks

```bash
python3 -m unittest discover -s tests -v
node tests/test_frontend.cjs
node --check web/app.js
python3 scripts/audit_reference.py
```

Node is needed only for the JavaScript checks, not to run the app. The Python suite includes all 184 payments, the four core cases, strict thresholds, grouping distractors, changed/missing policy, mixed currencies, and model failures. Frontend tests exercise draft/review persistence and source-version invalidation using the actual app code.

## Generate the ten-question artifact

```bash
python3 main.py --questions questions/questions.json --output submission.json
```

The provided `main.py` remains unchanged. The included `submission.json` records the execution mode for each question. The final verification run produced eight live AI responses and two labelled evidence fallbacks; see `VERIFICATION.md`. Inspect every result and any `ai_error_code` before presenting it as an LLM-enabled challenge submission. The private grading key has not been run.

## Architecture and implementation choices

```text
Browser interface → loopback JSON API → shared Python investigation core
                                          ├─ validated source lookups
                                          ├─ exact grouping / rule checks
                                          ├─ cached policy retrieval
                                          └─ optional tool-calling LLM
```

For fast, reproducible local delivery, this version uses Python's standard-library HTTP server and a dependency-free browser UI instead of the proposed FastAPI/React stack. Both the UI and official runner use the same Python rules, tools, and agent adapter. This is a deliberate prototype simplification; it adds no deployment or pip/npm setup requirement.

The server binds only to loopback, rejects unexpected hosts and cross-origin writes, and serves only allowlisted web assets. No endpoint serves `.env` or source files. No payment mutation or external-message tool exists. This is a single-user synthetic demo, not authenticated production banking software.

## Limitations

- Exercise rules are synthetic, not production banking policy or legal conclusions.
- Date-only groups approximate 24 hours. Nonmatching threshold currencies explicitly use the exercise's allowed 1:1 equivalence; production requires approved FX and timestamps.
- Live payment status, deadlines, assignment, customer documents, and settlement state are absent.
- Browser-local reviews are demonstration state, not immutable bank audit records or authorised approvals.
- Cached input/policy versions are established at startup; restart after editing reference files.
- No bank integration, deployed service, real customer messaging, or payment decision is implemented.
- Responsive CSS is provided; a comprehensive browser/device and accessibility audit has not been performed.

## Project contents

- [PRD](PRD.md): full target specification; [build verification](VERIFICATION.md): delivered scope and checks.
- `server.py`, `web/`: local API and working interface.
- `core/`, `tools/`, `rag/`, `agent/`: shared calculations, retrieval, and optional AI adapter.
- `main.py`, `questions/`, `submission.json`: official-runner workflow.
- `reference/`, `reference-audit.json`, `reference-manifest.json`: source snapshot and provenance.
- `scripts/`, `tests/`: audit and regression checks.
- `design/`: earlier UI concept and editable fragment; the working application is in `web/`.

Everything is kept inside this standalone project folder. Other projects remain unchanged.

## OpenAI integration references

The adapter uses the documented [function-calling interface](https://developers.openai.com/api/docs/guides/function-calling), [structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs), and [GPT-4.1 mini model](https://developers.openai.com/api/docs/models/gpt-4.1-mini). The API key stays server-side in a locally ignored file with owner-only permissions. This is a synthetic-data demo: real bank data requires approved processing, retention and access controls before use.
