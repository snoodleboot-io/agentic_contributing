---
agentic_contributing: "0.2"
autonomy: proposal
conformance: strict

verify:
  lint: "make lint"
  test: "make test"
  all: "make verify"

baseline_required: true

protected_paths:
  - "SPEC.md"
  - "schema/**"
  - ".github/workflows/**"

generated_paths: []

change_budget:
  max_files: 10
  max_lines: 400

dependencies:
  policy: deny

network:
  policy: deny

commit:
  branch_pattern: "agent/{slug}"
  message_style: imperative
  trailers: ["Co-Authored-By", "X-Agent-Model", "X-Agentic-Contributing"]

disclosure:
  report_required: true
  pr_label: "agent-authored"

overrides:
  - paths: ["examples/**"]
    autonomy: supervised

escalate_to: "open an issue and tag @snoodleboot"
---

# Agentic contributing

This repository defines the `AGENTIC_CONTRIBUTING.md` standard. This file is
also the standard applied to itself — if a rule is awkward to follow here, that
is evidence about the rule, and worth an issue.

The normative document is [`SPEC.md`](SPEC.md). Rule IDs below (`AC-*`) refer
to it.

## Ground rules

1. **The spec is protected.** `SPEC.md` and `schema/` are in `protected_paths`.
   Propose changes in an issue first; a normative change is a language change,
   not an edit (`AC-PATH-1`).
2. **Rule IDs are permanent.** Within a major version, never renumber, reuse,
   or repurpose an `AC-*` identifier. People cite these in code review. Adding
   a rule means appending; removing one means retiring the ID, not filling the
   gap (§12).
3. **Normative language is load-bearing.** MUST, SHOULD, and MAY are not
   stylistic choices. Do not "improve" a SHOULD into a MUST, or soften a MUST,
   as part of an editing pass.
4. **Every rule earns its place.** A rule that cannot be violated concretely,
   or whose violation a reviewer cannot recognize, is a slogan. Cut it.
5. **Spec and template stay in sync.** A new front matter field means updating
   `SPEC.md` §6.1, `schema/agentic-contributing-0.2.schema.json`,
   `tools/validate_agentic_contributing.py`, and
   `templates/AGENTIC_CONTRIBUTING.template.md` in the same change set. The
   validator's tests exist to catch you forgetting one.

## Definition of done

- `make verify` passes.
- Any new or changed front matter field appears in all four places listed in
  ground rule 5.
- Any new `AC-*` rule has: a unique ID, normative keyword, a concrete
  prohibited-or-required behavior, and — if it is a §7.5 prohibition — a "do
  instead" column entry.
- Prose changes keep the document's register: direct, specific, no filler.
  Rationale is welcome; exhortation is not.
- The disclosure report (§10) is attached to the PR, including what you did
  not verify.

## Testing

- Test command: `make test` (`python3 -m unittest discover -s tools -p 'test_*.py'`)
- Framework: `unittest` from the standard library. Do not add pytest or any
  other dependency — this repository's whole runtime dependency budget is
  PyYAML, and that is for the validator (`AC-DEP-1`, `dependencies: deny`).
- Tests live alongside the code in [`tools/`](tools/).

Rules:

- Validator bug fixes start with a failing test that reproduces the bad
  acceptance or the false rejection (`AC-TEST-1`). Report the before and after.
- Every new front matter constraint gets two tests: one document that satisfies
  it and one that violates it. A constraint tested only in the passing
  direction is not tested.
- Tests construct documents as inline strings. Do not read fixture files from
  disk — it makes failures harder to read and couples tests to layout
  (`AC-TEST-5`).
- Run the full suite after your final edit, not just the test you added
  (`AC-TEST-8`).
- The validator distinguishes errors from warnings. Do not downgrade an error
  to a warning to make a document pass; that is `AC-HACK-3` applied to our own
  tooling.

## Do not touch

- `SPEC.md` — the normative document. Issue first.
- `schema/` — the published schema. A change here breaks every consumer that
  pinned it.
- `.github/workflows/` — CI is the enforcement surface for a standard about
  enforcement. Human review, always.
- Rule IDs anywhere. See ground rule 2.

## Escalation

Stop and open an issue when:

- A proposed rule conflicts with an existing one, or two rules can both apply
  with different outcomes.
- A change would alter what an existing `AC-*` ID means (`AC-STOP-8`).
- The spec and the validator disagree about what is valid — one of them is
  wrong, and deciding which is a maintainer call, not an editing call.
- Any stop condition in §7.12 applies.

Route to: open an issue and tag `@snoodleboot`.

## Architecture invariants

- The front matter is the machine contract; the prose is the human contract.
  Anything an agent must act on deterministically belongs in front matter.
  Anything requiring judgment belongs in prose. Do not encode judgment as
  configuration.
- The validator has exactly one runtime dependency (PyYAML) and no network
  access. It must run offline, in CI, in under a second.
- The spec must remain vendor-neutral. No rule may depend on a specific agent,
  model, IDE, or hosting provider.

## Known landmines

- `templates/AGENTIC_CONTRIBUTING.template.md` deliberately contains `TODO`
  markers. `make lint` runs `--strict` on this repository's own file only;
  running `--strict` against the template will fail by design.
- The template's front matter must stay *valid*, not just illustrative — the
  test suite validates it. Placeholder values go in prose comments, never in
  front matter values that the schema constrains.
- The validator blanks fenced blocks and inline code spans before scanning for
  headings and placeholder markers, so examples do not count as declarations.
  If you
  change `strip_code`, the two `TestCodeStripping` tests are what stop this
  file from failing its own lint.
- Assert on the specific rule ID, not on `warnings == []`. Every document
  missing an optional section carries warnings, so a blanket emptiness
  assertion fails for reasons unrelated to the test.
