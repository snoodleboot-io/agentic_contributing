---
agentic_contributing: "0.1"
autonomy: proposal          # advisory | proposal | supervised | autonomous
conformance: standard       # core | standard | strict

verify:
  setup: "make install"
  lint: "make lint"
  typecheck: "make typecheck"
  test: "make test"
  test_scoped: "make test ARGS={paths}"
  all: "make verify"

baseline_required: true

protected_paths:
  - ".github/workflows/**"
  - "infra/**"
  - "migrations/**"
  - "**/*.lock"
  - ".env*"

generated_paths: []

change_budget:
  max_files: 25
  max_lines: 800

dependencies:
  policy: ask               # allow | ask | deny
  lockfile_command: "make lock"

network:
  policy: ask               # allow | ask | deny

commit:
  branch_pattern: "agent/{slug}"
  message_style: imperative
  trailers: ["Co-Authored-By", "X-Agent-Model"]

disclosure:
  report_required: true
  pr_label: "agent-authored"

overrides:
  - paths: ["docs/**", "**/*.md"]
    autonomy: supervised

escalate_to: "TODO: team, channel, or person to contact"
---

# Agentic contributing

This file is the contract for automated contributors to this repository. It
follows [AGENTIC_CONTRIBUTING.md v0.1](https://github.com/TODO/agentic-contributing).
Rule IDs below (`AC-*`) refer to that specification; the front matter above is
authoritative for anything it can express.

Human contributors: see [`CONTRIBUTING.md`](CONTRIBUTING.md).
Codebase orientation, layout, and commands: see [`AGENTS.md`](AGENTS.md).

## Ground rules

1. Read before you write. Read the file you are changing and its tests
   (`AC-ORIENT-2`).
2. Smallest change that fully solves the task. No drive-by refactors, renames,
   or reformatting (`AC-SCOPE-1`, `AC-SCOPE-2`).
3. Never make a gate pass by weakening the gate. No skipped tests, no loosened
   assertions, no blanket suppressions, no `--no-verify` (§7.5).
4. Never claim you ran something you did not run (`AC-REPORT-1`).
5. When in doubt, stop and ask. Stopping is a good outcome (§7.12).

<!-- TODO: add the two or three rules specific to this codebase that you would
     tell a new hire on day one. -->

## Definition of done

A change is done when all of the following are true:

- The stated requirement is implemented — not stubbed, not partially.
- Tests covering the new behavior exist and pass.
- Every gate in `verify` that can be run has been run, after the final edit,
  and passes at or above baseline (`AC-VERIFY-1`, `AC-VERIFY-2`).
- Any gate that could not be run is reported as `not_run` with a reason
  (`AC-VERIFY-4`).
- Documentation affected by the change is updated.
- The disclosure report is attached and accurate, including what was *not*
  verified (§10).

<!-- TODO: anything else that counts as "done" here — changelog entry, feature
     flag registration, metric added, translation keys, API docs regenerated. -->

## Testing

- Test command: `TODO`
- Test framework: `TODO`
- Where tests live: `TODO`

Rules:

- Bug fixes start with a failing test that reproduces the bug (`AC-TEST-1`).
  Report that it failed before and passes after.
- Use the existing framework, fixtures, and helpers. Do not introduce a new
  test library (`AC-TEST-3`).
- Tests must be deterministic: no wall clock, no network, no unseeded random,
  no order dependence (`AC-TEST-5`).
- Assert on behavior, not internals. Do not assert that a mock was called
  (`AC-TEST-4`, `AC-TEST-6`).
- Run the full suite for the affected package after your final edit, not just
  your new test (`AC-TEST-8`).
- Found a flaky test? Report it. Do not skip it (`AC-TEST-10`).

<!-- TODO: known slow suites, how to run a subset, required services, how to
     seed a test database, snapshot update procedure and when it is legitimate. -->

## Do not touch

Beyond `protected_paths` in the front matter:

<!-- TODO: list files or areas that require a human, and say why. The "why" is
     what lets an agent reason about edge cases you did not enumerate.
     Examples:
       - `src/billing/**` — money. Any change needs review by @finance-eng.
       - `schema/events/*.avsc` — wire format consumed by three other services.
       - `scripts/backfill_*.py` — these run against production data.
-->

## Escalation

Stop and ask when any stop condition in §7.12 applies — in particular:
ambiguous requirements, a protected path, a security-relevant change, budget
exceeded, credentials encountered, or three failed attempts at the same fix.

Route to: `TODO`

When you stop: leave the tree coherent, do not discard your work, and report
exactly where you stopped and why.

## Architecture invariants

<!-- OPTIONAL but high value. Things that must remain true, which an agent
     cannot infer from any single file. Examples:
       - The domain layer must not import from the web layer.
       - All outbound HTTP goes through `http/client.py` so retries and
         timeouts are uniform.
       - Every table has a tenant_id and every query filters on it.
-->

## Known landmines

<!-- OPTIONAL and the most valuable section in this file. The things that have
     burned people. Examples:
       - `test_import_ordering` passes locally and fails in CI unless
         `PYTHONHASHSEED=0`.
       - The dev server caches templates; a template change needs a restart.
       - `make lint` autoformats. Run it before staging or your diff will
         change under you.
-->
