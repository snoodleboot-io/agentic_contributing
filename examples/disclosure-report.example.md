# Worked example — a disclosure report

This is the PR body an agent produced working against
[`AGENTIC_CONTRIBUTING.example.md`](AGENTIC_CONTRIBUTING.example.md).

It is deliberately **not** a clean success. The agent hit a protected path,
stopped on that part, shipped the rest, and said so. That is the outcome the
specification is designed to produce: a partial result you can trust beats a
complete result you cannot.

---

## fix(posting): serialize idempotent transfer retries

Concurrent retries of `POST /v1/transfers` carrying the same `Idempotency-Key`
could both pass the "already posted?" check and produce two postings. The check
read from the replica and the write went to the primary, so a retry arriving
inside replication lag saw no prior posting.

This change moves the idempotency check onto the primary inside the posting
transaction, using `SELECT ... FOR UPDATE` on the idempotency row so the second
request blocks until the first commits and then returns the stored response.

**Not fixed here:** the unique index that would make this safe against
multi-process races requires a migration. Migrations are a protected path
(`AC-PATH-7`), so I stopped on that part and did not write it. Proposed DDL is
at the bottom. Without it, this fix closes the window within a process but not
across processes.

<!-- agentic-contributing:report v0.1 -->
```yaml
spec: "0.1"
agent: "claude-code"
model: "claude-opus-5"
autonomy: proposal        # downgraded from repo default `supervised`: touches src/ledger/posting/**
task: "Duplicate postings when a transfer is retried with the same Idempotency-Key (LEDGER-2291)"
completion: partial       # complete | partial

scope:
  files_changed: 4
  lines_added: 96
  lines_removed: 21
  budget: "20 files / 600 lines — within budget"
  out_of_scope_changes: none

verification:
  baseline:
    captured: true
    commit: "7f1c9ab"
    command: "make verify"
    failing_before:
      - "src/ledger/events/publish_test.py::test_retries_on_broker_timeout"
    note: "Pre-existing failure, unrelated to this change, unchanged after. Not fixed here (AC-VERIFY-6). Filed LEDGER-2298."
  gates:
    - name: setup
      command: "uv sync --frozen"
      status: pass
      exit_code: 0
    - name: lint
      command: "uv run ruff check . && uv run ruff format --check ."
      status: pass
      exit_code: 0
    - name: typecheck
      command: "uv run mypy src"
      status: pass
      exit_code: 0
    - name: test
      command: "uv run pytest -q"
      status: pass
      exit_code: 0
      output: "412 passed, 1 failed, 3 skipped in 94.2s"
      note: "The 1 failure is the pre-existing baseline failure above. 412 passed vs 411 at baseline (+1 new test... see testing)."
    - name: e2e
      command: "make e2e"
      status: not_run
      reason: "Requires staging credentials (LEDGER_STAGING_TOKEN), not present in this environment. Not inferred, not assumed passing (AC-VERIFY-4)."

testing:
  reproduction_test: "src/ledger/posting/idempotency_test.py::test_concurrent_retry_posts_once"
  failed_before_fix: true
  failure_before: "AssertionError: expected 1 posting, found 2"
  passes_after_fix: true
  repeated_runs: "100x with `pytest --count=100`, no failures"
  tests_added: 2
  tests_modified: 1
  tests_removed: 0
  modified_test_justification: >
    `test_duplicate_key_returns_cached_response` asserted the replica was read
    (`assert mock_replica.called`). That assertion encoded the bug: reading the
    replica is exactly what made this unsafe. Replaced with an assertion on
    observable behavior — same response body, one posting (AC-TEST-4, AC-TEST-12).

claims:
  verified:
    - "Two concurrent same-key requests in one process produce exactly one posting (new test, 100 runs)"
    - "The second request returns the first request's stored response body and 200, not a 409"
    - "Full suite is at baseline: same single pre-existing failure, no new failures"
    - "import-linter still passes; no new posting -> api import"
  believed:
    - "Latency impact is negligible: the row lock is uncontended unless a retry is actually in flight, which is rare in production traffic"
    - "The lock cannot deadlock against the posting transaction, because it is acquired first and both paths acquire in the same order"
  unverified:
    - "Behavior across processes / pods — not reproducible locally, and the unique index that would guarantee it is not in this PR"
    - "Lock-wait behavior under the production connection pool size (we run 8 locally, 64 in prod)"
    - "End-to-end path through the API gateway — `make e2e` could not run"

assumptions:
  - "The idempotency row is written in the same transaction as the posting (per src/ledger/posting/engine.py:141). If that is not true on some path I did not find, this fix is incomplete."
  - "`Idempotency-Key` is scoped per tenant, not global — inferred from the composite index in models.py:88."

risks:
  - "Adds a row-level lock held for the duration of the posting transaction. A slow posting now blocks retries of that same key rather than racing them. This is the intended trade, but it converts a correctness bug into a latency tail for repeated keys."
  - "Without the unique index (see below), a multi-pod race is still possible. This PR narrows the window; it does not close it."

review_pointers:
  - file: "src/ledger/posting/idempotency.py"
    lines: "44-71"
    why: >
      Least confident change. The lock is taken before the posting transaction's
      savepoint. I convinced myself the ordering is consistent with
      engine.post() but I could not construct a test that would fail if it were
      not. If anyone knows a path that opens the posting transaction first,
      this is wrong.
  - file: "src/ledger/posting/idempotency_test.py"
    lines: "88-104"
    why: >
      The concurrency test uses two threads against one connection pool. It
      reproduces the bug reliably on my runs, but thread-based concurrency
      tests are the kind of thing that passes for the wrong reason.

stopped_on:
  - what: "Unique index on (tenant_id, idempotency_key)"
    rule: "AC-STOP-2"
    why: "Requires a migration; src/ledger/migrations/** is a protected path (AC-PATH-7)"
    proposed: |
      CREATE UNIQUE INDEX CONCURRENTLY idx_idem_tenant_key
        ON posting_idempotency (tenant_id, idempotency_key);
      -- CONCURRENTLY because the table is ~40M rows and this runs in prod.
      -- Needs a human: index build time and lock behavior are not something
      -- I can measure from here.

deviations:
  - rule: "AC-AUTO-1"
    what: "Ran at `proposal` rather than the repository default `supervised`; did not open the PR as auto-mergeable"
    why: "Change touches src/ledger/posting/**, which overrides to proposal + require_human_review"

dependencies_added: []
breaking_changes: []
documentation:
  - "CHANGELOG.md: entry under ## Unreleased"
  - "docs/idempotency.md: replaced the 'reads from replica' paragraph, which is now wrong"
  - "openapi.json: unchanged — no response shape changed"
```

---

## Why this report is the shape it is

Each field exists because of a specific way agent-authored changes go wrong.

| Field | Failure it catches |
|---|---|
| `baseline.failing_before` | "Your change broke the build" / "that was already broken" — an argument nobody can settle after the fact |
| `status: not_run` + `reason` | A gate silently reported as passing, or silently omitted |
| `failed_before_fix` | A fix that was never demonstrated to fix anything |
| `modified_test_justification` | A test quietly rewritten to match the bug (`AC-HACK-17`) |
| `claims.believed` vs `verified` | Reasoning presented as observation |
| `claims.unverified` | The thing that breaks in production, known and unmentioned |
| `assumptions` | A guess that a reviewer could have corrected in ten seconds |
| `review_pointers` | Reviewer attention spent uniformly across a diff instead of on the risky part |
| `stopped_on` | Work silently dropped, or a protected path quietly edited |
| `deviations` | Rules bent without anyone knowing which |
| `completion: partial` | "Done" meaning "some of it" |

The two doing the most work are `claims.unverified` and `review_pointers`. An
agent that cannot name what it failed to check, or which of its own hunks is
weakest, has not reviewed its work — and a report full of confident green is
less informative than one that says where to look.
