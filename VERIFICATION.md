# Payment Clarity — implementation verification

Verified 5 September 2026.

## Delivered

A running loopback-only local application, shared Python investigation core, deterministic tools, cached policy retrieval, optional tool-calling provider adapter, searchable source records, evidence/assumption views, RM draft editing, local review state, customer preview, case export, and unchanged official runner.

Implementation differs from the target stack: standard-library HTTP server and browser JavaScript/CSS replace FastAPI/React for this fast dependency-free prototype. Bank integrations and protected shared workflow storage remain outside the delivered scope.

## Passed checks

- 23 Python regression tests, including a sweep of all 184 supplied payments and all ten official questions.
- Four specific case outcomes, strict amount boundaries, exact CHF 110,000 aggregate, and both distractor exclusions.
- Currency/date grouping, incomplete cross-currency assessment, missing and changed policy mappings, unknown IDs, irrelevant policy exclusion, output citation/number validation, and simulated provider timeout.
- Five JavaScript state-transition checks against the actual app script: preview review gate, invalidation on edit, persisted same-version review, invalidation on source change, and internal-only preview prevention.
- Python compilation and JavaScript syntax checks.
- Official runner generated exactly ten JSON objects with OpenAI configured: eight accepted live AI responses and two labelled evidence fallbacks (Q01: unsupported review-type wording; Q09: threshold prose). Total agent durations were 3.0–7.1 seconds in this final run. This is a small synthetic sample, not a production latency benchmark.
- Live HTTP and structured browser-tool checks confirmed OpenAI-enabled investigations. The visible preview was updated to a live AI P50002 result.
- Strict tool and output schemas, required initial tool use, bounded rewrite, rejection of cross-case tool calls, unsupported review types, threshold prose, and spelled quantities were checked. Authentication/quota diagnostics are sanitised and redirects are denied.
- The local credential file has owner-only 0600 permissions and an explicit `.gitignore` exclusion; HTTP access returns 404. The workspace has no Git repository yet, so no Git tracking assertion is made.
- Local HTTP checks: root and assets respond successfully, P50003 returns the correct total, unknown ID returns 404, invalid input returns 400, foreign-origin request returns 403, and `.env` is not served.
- Structured browser-tool registration confirmed. Actual browser state read-back verified P50002, switching to P50003 with the correct group total, staging a local draft, and rejecting an unknown payment ID.

## Scope of evidence

These checks do not prove the absence of every bug. The private competition answer key, full browser/device matrix, complete accessibility criteria, and production controls have not been tested. OpenAI GPT-4.1 mini was tested with supplied synthetic cases. Earlier live runs exposed unsupported narrative details; the adapter now rejects several known failure classes and attempts one rewrite. These guards cannot prove semantic correctness: every AI explanation remains marked for human review, and exact policy comparisons stay in deterministic evidence. Live results vary between requests; two final-run fallbacks remain visible in the artifact.

The browser interaction check used the optional structured app tools; no broad screenshot/click-based UI QA was performed on this implementation. The earlier design concept had separate visual checks and should not be mistaken for full application QA.

Reference files retain their original content and license. The content-hash manifest records the local snapshot, not a pinned upstream commit.
