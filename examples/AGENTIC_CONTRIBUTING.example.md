---
agentic_contributing: "0.1"
autonomy: supervised
conformance: strict

verify:
  setup: "uv sync --frozen"
  lint: "uv run ruff check . && uv run ruff format --check ."
  typecheck: "uv run mypy src"
  test: "uv run pytest -q"
  test_scoped: "uv run pytest -q {paths}"
  e2e: "make e2e"
  all: "make verify"

baseline_required: true

protected_paths:
  - ".github/workflows/**"
  - "infra/**"
  - "src/ledger/migrations/**"
  - "src/ledger/events/schemas/*.avsc"
  - "uv.lock"
  - ".env*"
  - "CODEOWNERS"

generated_paths:
  - "src/ledger/api/openapi.json"
  - "src/ledger/db/models_generated.py"

change_budget:
  max_files: 20
  max_lines: 600

dependencies:
  policy: ask
  allowed_registries: ["pypi.org"]
  lockfile_command: "uv lock"

network:
  policy: deny

commit:
  branch_pattern: "agent/{slug}"
  message_style: conventional
  trailers: ["Co-Authored-By", "X-Agent-Model", "X-Agentic-Contributing"]
  signoff: false

disclosure:
  report_required: true
  pr_label: "agent-authored"

overrides:
  - paths: ["docs/**", "**/*.md"]
    autonomy: autonomous
    change_budget: { max_files: 60 }
  - paths: ["src/ledger/posting/**", "src/ledger/auth/**"]
    autonomy: proposal
    require_human_review: true

escalate_to: "#ledger-oncall (Slack), or @ledger-maintainers on the PR"
---

# Agentic contributing — ledger-api

`ledger-api` is the double-entry ledger behind billing. It is a FastAPI service
on Postgres, publishing events to Kafka. Money moves through the code in
`src/ledger/posting/`; treat that directory as if a mistake there is a
customer-visible incident, because it is.

This file follows [AGENTIC_CONTRIBUTING.md v0.1](https://github.com/snoodleboot-io/agentic_contributing).
Rule IDs below (`AC-*`) refer to that specification.

Codebase layout, local setup, and command reference: [`AGENTS.md`](AGENTS.md).
Human contribution process: [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Ground rules

1. **Read the module and its tests before editing it** (`AC-ORIENT-2`). Our
   test files sit next to the code (`src/ledger/posting/entry_test.py`), not in
   a separate tree — if you did not find a test file, look again before
   concluding there is none.
2. **Money code is proposal-only.** `src/ledger/posting/**` and
   `src/ledger/auth/**` require human review regardless of how small the diff
   is (`AC-AUTO-3`).
3. **Never weaken a gate to pass it** (§7.5). Our CI is the only thing standing
   between a rounding error and a restatement.
4. **Amounts are `Decimal`, never `float`.** If a change introduces a float in
   a code path that touches an amount, that change is wrong, and no test result
   makes it right.
5. **Never claim you ran something you did not run** (`AC-REPORT-1`). `make e2e`
   needs staging credentials that are usually absent locally; report it
   `not_run` rather than guessing (`AC-VERIFY-4`).
6. **Stop and ask beats guessing** (§7.12). `#ledger-oncall` is staffed.

## Definition of done

- The stated requirement is implemented — not stubbed, not narrowed.
- Tests exist at the level we already test at, and pass (`AC-TEST-2`).
- A baseline was captured on the base commit before any edit (`AC-VERIFY-2`).
- Every runnable gate ran **after the final edit** and passes at or above
  baseline (`AC-VERIFY-1`).
- Gates that could not run are reported `not_run` with a reason.
- If the change alters an HTTP response, `src/ledger/api/openapi.json` is
  regenerated with `make openapi` — never hand-edited (`AC-PATH-3`).
- If the change alters a published event, the version was bumped and the
  compatibility test in `src/ledger/events/compat_test.py` passes.
- A `CHANGELOG.md` entry exists under `## Unreleased`.
- The disclosure report (§10) is attached to the PR, including the
  `review_pointers` and everything under `unverified`.

## Testing

- Full suite: `uv run pytest -q` (~90s)
- Scoped: `uv run pytest -q src/ledger/posting`
- Integration tests need Postgres: `make db-up` first. They are marked
  `@pytest.mark.integration` and are **included** in the default run.
- End-to-end: `make e2e`. Requires staging credentials. Expect this to be
  `not_run` in most agent environments — that is fine, and reporting it as
  passing is not.

Rules:

- **Bug fixes start with a failing test** (`AC-TEST-1`). Write the reproduction,
  watch it fail on unmodified code, then fix. Report both observations. A fix
  never demonstrated to fix anything is a guess.
- Use `pytest`, our `factories/` builders, and the `ledger_db` fixture. Do not
  introduce another test framework, another mocking library, or `unittest`
  style (`AC-TEST-3`).
- **Never mock `posting.engine`.** Posting logic is tested against a real
  transaction on the test database. A posting test that passes with the engine
  mocked out is testing nothing (`AC-TEST-6`).
- Assert on ledger state and API responses, not on internal call counts
  (`AC-TEST-4`).
- Deterministic only: use the `frozen_clock` fixture instead of
  `datetime.now()`, and seed any randomness (`AC-TEST-5`).
- Fixtures must not contain real account numbers, real customer names, or
  copied production rows (`AC-TEST-11`).
- Found a flaky test? Report it in `#ledger-oncall`. Do not skip it, do not
  wrap it in a retry (`AC-TEST-10`).
- Changing an existing assertion means changing a specification. Say in the
  report why the old assertion was wrong (`AC-TEST-12`).

## Do not touch

Beyond `protected_paths` in the front matter:

- **`src/ledger/migrations/**`** — migrations are applied in production the hour
  they merge and are immutable afterwards. Propose the migration in the PR
  description; a human writes and runs it (`AC-PATH-7`).
- **`src/ledger/events/schemas/*.avsc`** — the wire format three other services
  consume. A field rename here is an outage there.
- **`src/ledger/posting/engine.py`** — the double-entry invariant lives in
  `_assert_balanced`. Changing it requires two approvals, one from
  `@ledger-maintainers` and one from `@finance-eng`.
- **`scripts/backfill_*.py`** — these run against production data. Read them
  for context; do not edit or execute them.
- **`uv.lock`** — regenerate with `uv lock`, never hand-edit, never partially
  update (`AC-DEP-5`).

## Dependencies

`dependencies.policy: ask`. Before proposing a new package, state its exact
version, license, transitive dependency count, last release date, and why
`httpx`, `pydantic`, `sqlalchemy`, or the standard library cannot do it
(`AC-DEP-3`). Verify the package exists on PyPI — do not add a package you
remember rather than looked up (`AC-DEP-4`).

Do not upgrade unrelated packages as part of another change (`AC-DEP-6`).
Dependency bumps go in their own PR.

## Security

Changes to `src/ledger/auth/**`, token handling, tenant scoping, or anything
constructing SQL are security-relevant and require human review regardless of
size (`AC-SEC-6`).

- Every query against a tenant-scoped table must filter on `tenant_id`. We have
  no row-level security; the filter is the control.
- Use SQLAlchemy parameter binding. Never build SQL with f-strings
  (`AC-SEC-7`).
- If you find a credential in the tree or in history, stop and escalate
  privately (`AC-SEC-3`, `AC-SEC-8`). Do not delete the line and move on — the
  secret is still in history and needs rotation, and a quiet deletion destroys
  the evidence that rotation is needed.

## Escalation

Stop and post in `#ledger-oncall` when:

- Requirements are ambiguous in a way that changes the implementation
  (`AC-STOP-1`).
- The task needs a migration, an event schema change, or any protected path
  (`AC-STOP-2`).
- The only way forward is a prohibited shortcut (`AC-STOP-3`).
- The change exceeds 20 files or 600 lines (`AC-STOP-4`).
- The change touches posting, auth, or tenant scoping (`AC-STOP-5`).
- Three consecutive attempts at the same fix have failed (`AC-STOP-9`). Report
  what you tried, what you observed, and your current best hypothesis. A fourth
  attempt without new information will not work either.

Leave the tree coherent, keep your work, and say exactly where you stopped.

## Architecture invariants

- **Double entry:** every posting is a set of entries summing to zero per
  currency. `_assert_balanced` enforces it at write time and must never be
  bypassed, even in tests.
- **Amounts are `Decimal`** with explicit quantization at the API boundary
  only. No float arithmetic anywhere in `src/ledger/posting/`.
- **Layering:** `api/` may import `posting/`; `posting/` must never import
  `api/`. Enforced by `import-linter` in the lint gate.
- **Idempotency:** every write endpoint takes an `Idempotency-Key` and must be
  safe to retry. New write endpoints without one will be rejected in review.
- **All outbound HTTP goes through `src/ledger/http/client.py`** so timeouts,
  retries, and tracing stay uniform.

## Known landmines

- `pytest` is configured with `-p no:randomly` because
  `posting/reconcile_test.py` depends on insertion order. If you re-enable
  random ordering, that suite fails for reasons unrelated to your change.
- `make lint` runs `ruff format`, which **rewrites files**. Run it before you
  stage, or your staged diff will not match your working tree.
- The `ledger_db` fixture truncates tables between tests but does **not** reset
  sequences. Do not assert on specific primary key values.
- Integration tests fail with a confusing `connection refused` if `make db-up`
  has not run. That is not a code error.
- `openapi.json` regeneration is not stable across `pydantic` patch versions.
  If the diff is enormous and unrelated to your change, your local `pydantic`
  drifted from the lockfile — run `uv sync --frozen` and regenerate.
- The first `uv run` after a dependency change compiles wheels and takes
  several minutes. It is not hung.
