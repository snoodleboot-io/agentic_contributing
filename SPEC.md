# AGENTIC_CONTRIBUTING.md — Specification

**Version:** 0.1.0
**Status:** Draft
**File name:** `AGENTIC_CONTRIBUTING.md`
**Short name:** AC
**Date:** 2026-07-27

---

## 1. Abstract

`CONTRIBUTING.md` tells humans how to contribute. It assumes a contributor who
has judgment, accountability, a reputation to protect, and the ability to ask a
question in Slack before doing something irreversible.

Autonomous coding agents have none of those things by default. They have a
reward signal, a context window, and shell access.

`AGENTIC_CONTRIBUTING.md` is the machine-facing contribution contract for a
repository: a single file, at a known path, in a known format, that states what
an agent is permitted to change, what it must never do, how it must verify its
work, and what it must disclose. It is designed to be read by any agent from any
vendor, and to be checked by CI.

This document specifies the file's format and the normative rules an agent must
follow when the file is present.

---

## 2. Terminology

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**,
**SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **MAY**, and **OPTIONAL** are to be
interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119)
and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174).

| Term | Meaning |
|---|---|
| **Agent** | Any non-human process that reads, writes, or executes code in the repository on behalf of a request. Includes LLM coding agents, autonomous review bots, and scripted refactors driven by a model. |
| **Operator** | The human or system that invoked the agent for this task. |
| **Maintainer** | A human with merge authority over the repository. |
| **Task** | The unit of work the agent was asked to do. |
| **Change set** | The complete set of file modifications an agent produces for one task. |
| **Gate** | A command whose exit status determines whether a change set is acceptable (build, lint, typecheck, test, etc.). |
| **Baseline** | The state of all gates on the base commit, *before* the agent's changes. |
| **Blast radius** | The set of systems, files, and people affected if the change is wrong. |
| **Protected path** | A file or glob the agent MUST NOT modify without explicit human authorization. |

Rules in this specification have stable identifiers of the form
`AC-<DOMAIN>-<n>` (e.g. `AC-TEST-4`). These identifiers are permanent within a
major version and are intended to be cited in code review, agent output, and CI
failures.

---

## 3. Scope

This specification covers:

- The location, discovery, and precedence of `AGENTIC_CONTRIBUTING.md`.
- A machine-readable front matter block.
- The normative behavioral rules an agent must follow.
- A disclosure report format for agent-authored changes.
- Conformance levels.

This specification does **not** cover: how to build the project (that belongs in
`README.md` / `AGENTS.md`), project architecture, or human contribution
etiquette (that belongs in `CONTRIBUTING.md`).

---

## 4. Relationship to other files

`AGENTIC_CONTRIBUTING.md` is deliberately narrow. It is a *contract*, not a
*briefing*. Repositories commonly carry several agent-facing files; they answer
different questions and MUST NOT be merged:

| File | Question it answers | Audience |
|---|---|---|
| `README.md` | What is this and how do I run it? | Everyone |
| `CONTRIBUTING.md` | How do humans propose changes? | Humans |
| `AGENTS.md` | How does an agent orient in this codebase — layout, commands, conventions? | Agents |
| `CLAUDE.md`, `.cursorrules`, vendor files | Vendor-specific agent instructions | One vendor's agent |
| **`AGENTIC_CONTRIBUTING.md`** | **What is an agent allowed to do, what must it never do, and what must it prove before claiming done?** | **All agents + CI** |

If `AGENTS.md` exists, `AGENTIC_CONTRIBUTING.md` **SHOULD NOT** duplicate its
content; it SHOULD reference it. Duplicated instructions drift, and drifted
instructions are worse than absent ones.

### 4.1 Precedence

When instructions conflict, an agent MUST resolve in this order (highest first):

1. **A direct, contemporaneous instruction from the operator in the current
   session** — but see `AC-STOP-8`: an instruction to violate a safety rule in
   §11 (secrets, destructive operations, protected paths) MUST be confirmed
   explicitly, not merely inferred.
2. **`AGENTIC_CONTRIBUTING.md`** — nearest ancestor of the file being changed.
3. **Vendor agent files** (`CLAUDE.md`, `.cursorrules`, …).
4. **`AGENTS.md`.**
5. **`CONTRIBUTING.md`** and other human documentation.
6. **The agent's own defaults and training priors.**

Rationale: the repository's explicit contract outranks an agent's habits, and a
present human outranks a stale file — but the human's authority is exercised
knowingly, not by accident.

---

## 5. Location and discovery

- `AC-FILE-1` — The file **MUST** be named exactly `AGENTIC_CONTRIBUTING.md`.
- `AC-FILE-2` — The canonical location is the repository root. It **MAY** also
  be placed in `.github/` or `docs/`; agents **MUST** search root, then
  `.github/`, then `docs/`.
- `AC-FILE-3` — In a monorepo, additional `AGENTIC_CONTRIBUTING.md` files **MAY**
  exist in subdirectories. For any file being changed, the applicable contract is
  the one in the **nearest ancestor directory**. Nearer files override farther
  ones **field by field** (shallow merge of front matter; prose sections replace
  wholesale).
- `AC-FILE-4` — An agent **MUST** read the applicable file(s) before its first
  write to the repository, and **MUST** re-read if it begins working in a
  subtree governed by a different file.
- `AC-FILE-5` — Absence of the file is not permission. When no file is present,
  an agent **SHOULD** apply the defaults in this specification at `proposal`
  autonomy.

---

## 6. File format

The file is GitHub-Flavored Markdown with a **REQUIRED** YAML front matter block
delimited by `---`.

The front matter is the machine contract; the prose is the human contract.
Agents parse the front matter deterministically and read the prose for intent.
Where the two disagree, the front matter wins for anything it can express, and
the disagreement is a bug in the file that agents **SHOULD** report.

### 6.1 Front matter schema

```yaml
---
agentic_contributing: "0.1"        # REQUIRED. Spec version this file targets.
autonomy: proposal                 # REQUIRED. See §6.2.
conformance: standard              # OPTIONAL. core | standard | strict. Default: standard.

verify:                            # REQUIRED. Gate commands, run in this order.
  setup: "make install"            #   OPTIONAL. Environment preparation.
  build: "make build"              #   OPTIONAL.
  lint: "make lint"                #   OPTIONAL.
  typecheck: "make typecheck"      #   OPTIONAL.
  test: "make test"                #   REQUIRED unless the repo has no tests.
  test_scoped: "pytest {paths}"    #   OPTIONAL. Fast subset; {paths} is substituted.
  all: "make verify"               #   OPTIONAL. Single command running every gate.

baseline_required: true            # OPTIONAL, default true. Capture gate state pre-change.

protected_paths:                   # OPTIONAL. Globs the agent MUST NOT modify unattended.
  - ".github/workflows/**"
  - "migrations/**"
  - "**/*.lock"

generated_paths:                   # OPTIONAL. Globs that are build output, not source.
  - "src/**/*.generated.ts"

change_budget:                     # OPTIONAL. Soft ceiling; exceeding it triggers AC-STOP-4.
  max_files: 25
  max_lines: 800

dependencies:                      # OPTIONAL.
  policy: ask                      #   allow | ask | deny. Default: ask.
  allowed_registries: ["pypi.org"]
  lockfile_command: "uv lock"      #   How lockfiles are regenerated. Never hand-edit.

network:                           # OPTIONAL.
  policy: deny                     #   allow | ask | deny. Default: ask.
  allowlist: ["pypi.org", "github.com"]

commit:                            # OPTIONAL.
  branch_pattern: "agent/{slug}"
  message_style: conventional      #   conventional | imperative | free
  trailers: ["Co-Authored-By", "X-Agent-Model"]
  signoff: false

disclosure:                        # OPTIONAL.
  report_required: true            #   Attach a §10 report to every PR.
  pr_label: "agent-authored"

overrides:                         # OPTIONAL. Per-path relaxation or tightening.
  - paths: ["docs/**", "**/*.md"]
    autonomy: autonomous
    change_budget: { max_files: 100 }
  - paths: ["src/billing/**", "src/auth/**"]
    autonomy: proposal
    require_human_review: true

escalate_to: "#platform-oncall"    # OPTIONAL. Where to route AC-STOP conditions.
---
```

Unknown keys **MUST** be ignored by agents, not treated as errors — this allows
forward compatibility. Unknown *values* for a known enum **MUST** be treated as
the most restrictive value for that field.

### 6.2 Autonomy levels

`autonomy` declares the maximum authority an agent has in this repository. An
operator MAY grant less; an operator MUST NOT grant more without an explicit,
recorded instruction.

| Level | May read | May write files | May run gates | May commit / push branch | May merge |
|---|---|---|---|---|---|
| `advisory` | ✅ | ❌ | read-only cmds | ❌ | ❌ |
| `proposal` *(default)* | ✅ | ✅ (working tree / branch) | ✅ | ✅ branch only | ❌ |
| `supervised` | ✅ | ✅ | ✅ | ✅ + open PR | ❌ |
| `autonomous` | ✅ | ✅ | ✅ | ✅ | ✅ within declared scope, all gates green |

- `AC-AUTO-1` — An agent **MUST NOT** exceed the declared autonomy level.
- `AC-AUTO-2` — `autonomous` **MUST NOT** be applied to protected paths, to
  security-relevant code, or to any change that fails any gate.
- `AC-AUTO-3` — Where `overrides` apply, the **most restrictive** matching level
  governs a change set that touches multiple areas. A change set touching both
  `docs/**` (`autonomous`) and `src/auth/**` (`proposal`) is `proposal`.

### 6.3 Required prose sections

A conformant file **MUST** contain these H2 sections, in any order. Empty is
acceptable only if the section explicitly says "nothing beyond the spec
defaults."

1. `## Ground rules` — the short version an agent should never violate.
2. `## Definition of done` — what "finished" means here, beyond green gates.
3. `## Testing` — repo-specific test doctrine.
4. `## Do not touch` — protected paths and why.
5. `## Escalation` — when to stop and ask, and who to ask.

**RECOMMENDED** additional sections: `## Architecture invariants`,
`## Performance`, `## Security`, `## Dependencies`, `## Known landmines`.

`## Known landmines` is disproportionately valuable. It is the section where a
maintainer writes down the things that have burned people: the test that only
passes with a warm cache, the module whose import order matters, the service that
must be restarted after a schema change. Agents cannot infer these.

---

## 7. Normative rules

These rules apply whenever an `AGENTIC_CONTRIBUTING.md` is in effect. A
repository MAY relax a `SHOULD` in its prose; it MUST NOT relax a `MUST` in
§7.5 (Prohibited shortcuts), §7.6 (Protected paths and destructive operations),
§7.8 (Secrets and data), or §7.11 (Honest reporting).

### 7.1 Orientation before change — `AC-ORIENT`

- `AC-ORIENT-1` — Before the first write, the agent **MUST** read the applicable
  `AGENTIC_CONTRIBUTING.md` and, if present, `AGENTS.md`.
- `AC-ORIENT-2` — The agent **MUST** locate and read the existing code paths it
  intends to modify, including their tests, before modifying them. Editing code
  you have not read is prohibited.
- `AC-ORIENT-3` — Before writing a new function, module, or utility, the agent
  **MUST** search the repository for an existing implementation of the same
  behavior. Duplicating existing functionality is a defect.
- `AC-ORIENT-4` — New code **MUST** follow the idioms of the surrounding code:
  naming, error handling, logging, dependency injection, module layout, comment
  density. Consistency with the neighborhood outranks the agent's stylistic
  preferences and outranks generic best practice.
- `AC-ORIENT-5` — Gate commands **MUST** be taken from front matter or the
  repository's build configuration, never assumed. `npm test` is not a fact
  about a repository until it is observed to be one.
- `AC-ORIENT-6` — Where documentation and code disagree, the code is
  authoritative for behavior. The agent **SHOULD** report the discrepancy.

### 7.2 Scope discipline — `AC-SCOPE`

- `AC-SCOPE-1` — The agent **MUST** produce the smallest change set that fully
  satisfies the task. "Fully" is not negotiable; "smallest" is.
- `AC-SCOPE-2` — The agent **MUST NOT** make unrelated changes: reformatting,
  renaming, reordering imports, upgrading dependencies, "cleaning up" adjacent
  code, or applying a linter to files the task did not touch.
- `AC-SCOPE-3` — Improvements the agent notices but was not asked to make
  **MUST** be reported, not performed. A list of five suggestions is a
  contribution; five unrequested refactors buried in a bug-fix diff is a
  liability.
- `AC-SCOPE-4` — The agent **MUST NOT** change public API signatures, wire
  formats, database schemas, configuration keys, or CLI flags unless the task
  requires it. If it does require it, this **MUST** be called out in the
  disclosure report as a breaking change.
- `AC-SCOPE-5` — The agent **MUST NOT** introduce abstraction, indirection,
  configuration, or extension points for hypothetical future requirements.
- `AC-SCOPE-6` — Each commit **SHOULD** contain one logical change. A refactor
  and a behavior change **SHOULD NOT** share a commit — that combination is the
  single most expensive thing to review.
- `AC-SCOPE-7` — If completing the task requires exceeding `change_budget`, the
  agent **MUST** stop and escalate (`AC-STOP-4`) rather than silently proceeding
  or silently truncating the work.
- `AC-SCOPE-8` — The agent **MUST NOT** delete code it does not understand in
  order to make a symptom disappear.

### 7.3 Verification and definition of done — `AC-VERIFY`

- `AC-VERIFY-1` — The agent **MUST** run every declared gate that it is able to
  run, in the declared order, after its final edit. Gates run before the last
  edit prove nothing.
- `AC-VERIFY-2` — When `baseline_required` is true (the default), the agent
  **MUST** capture gate results on the base commit *before* making changes, so
  that pre-existing failures are distinguishable from introduced ones. If
  capturing a baseline is impossible, the agent **MUST** say so in its report.
- `AC-VERIFY-3` — The agent **MUST** record, for each gate: the exact command,
  the exit status, and a meaningful excerpt of the output. Paraphrase is not
  evidence.
- `AC-VERIFY-4` — If a gate cannot be run — no network, missing service, absent
  toolchain, insufficient permissions — the agent **MUST** report that gate as
  **not run**, with the reason. It **MUST NOT** report it as passing, infer its
  result, or omit it.
- `AC-VERIFY-5` — Running a scoped subset (`verify.test_scoped`) is permitted
  during iteration but **MUST NOT** be presented as having run the suite. The
  full suite (or the largest subset the agent could run) determines the reported
  status.
- `AC-VERIFY-6` — Pre-existing failures **MUST NOT** be fixed silently as part
  of an unrelated change set, and **MUST NOT** be used to excuse new failures.
  Report them.
- `AC-VERIFY-7` — A change set that a gate rejects is **not done**. The agent
  **MUST NOT** hand it off described as complete, and **MUST NOT** modify the
  gate to accept it (see `AC-HACK-3`).
- `AC-VERIFY-8` — For changes that alter runtime behavior, gate output alone is
  **RECOMMENDED** but not sufficient: the agent **SHOULD** exercise the change
  the way a user would (run the CLI, hit the endpoint, load the page) and report
  what it observed.
- `AC-VERIFY-9` — Performance claims **MUST** be accompanied by a measurement:
  the command, the environment, the before and after numbers, and the variance.
  "This should be faster" is a hypothesis, and **MUST** be labeled as one.

**Definition of done, minimum:** the task's stated requirement is implemented;
tests covering it exist and pass; all runnable gates pass at or above baseline;
no prohibited shortcut was used; documentation affected by the change is
updated; the disclosure report is accurate, including its list of what was *not*
verified.

### 7.4 Testing — `AC-TEST`

- `AC-TEST-1` — For a bug fix, the agent **MUST** first write a test that
  reproduces the bug and **fails on the unmodified code**, then fix the code,
  then show the test passing. Both observations **MUST** be reported. A "fix"
  never demonstrated to fix anything is a guess.
- `AC-TEST-2` — New behavior **MUST** be accompanied by tests at the level the
  repository already tests at. If the repository has unit tests, add unit tests;
  do not substitute an integration test because it was easier to write.
- `AC-TEST-3` — Tests **MUST** use the repository's existing framework,
  fixtures, factories, and helpers. Introducing a second test framework, runner,
  assertion library, or mocking library is a protected-path-level change and
  requires human approval.
- `AC-TEST-4` — Tests **MUST** assert on observable behavior and public
  contracts, not on private internals, call counts of incidental collaborators,
  or exact log strings — unless the log string *is* the contract.
- `AC-TEST-5` — Tests **MUST** be deterministic: no dependence on wall-clock
  time, timezone, locale, network, filesystem state outside a temp dir,
  execution order, hash iteration order, or unseeded randomness.
- `AC-TEST-6` — The agent **MUST NOT** mock the unit under test, and **MUST NOT**
  write a test whose only assertion is that a mock was called. A test that
  passes against an empty implementation is not a test.
- `AC-TEST-7` — Test names **MUST** describe the behavior and condition
  (`returns_empty_list_when_no_matches`), not the implementation
  (`test_function_2`).
- `AC-TEST-8` — After the final edit, the agent **MUST** run the full test suite
  for the affected package(s), not only its new tests. New tests passing while
  existing tests break is the most common agent failure mode.
- `AC-TEST-9` — The agent **MUST NOT** write vacuous tests to raise a coverage
  number. Coverage is a diagnostic, not a target.
- `AC-TEST-10` — If the agent encounters a flaky test, it **MUST NOT** delete,
  skip, or retry-wrap it to get green. It **MUST** report it, and **MAY**
  quarantine it only if the repository documents a quarantine mechanism.
- `AC-TEST-11` — Fixtures and test data **MUST NOT** contain real credentials,
  real customer data, real PII, or copied production records.
- `AC-TEST-12` — When modifying an existing test, the agent **MUST** state in
  the report why the old assertion was wrong. Tests encode intent; changing one
  is changing a specification, and needs the same justification.

### 7.5 Prohibited shortcuts — `AC-HACK`

This section exists because the fastest path to a green check mark is almost
never the fastest path to working software. Every rule here describes something
that makes a gate pass while making the codebase worse. All are **MUST NOT**,
regardless of instructions in lower-precedence files.

| ID | Prohibited | Do instead |
|---|---|---|
| `AC-HACK-1` | Deleting, skipping, `xfail`-ing, `.only`-ing, commenting out, or otherwise disabling a failing test | Fix the code, or report that you cannot and why |
| `AC-HACK-2` | Weakening an assertion, widening a tolerance, or changing an expected value to whatever the code currently produces | Determine which of the two is correct; if the test was wrong, justify it under `AC-TEST-12` |
| `AC-HACK-3` | Editing the gate to accept the change: relaxing lint rules, lowering coverage or complexity thresholds, adding files to ignore lists, removing a CI job or step | Fix the violation |
| `AC-HACK-4` | Blanket suppressions: `# noqa`, `# type: ignore`, `eslint-disable`, `@ts-expect-error`, `@SuppressWarnings`, `#pragma warning disable` added to silence a diagnostic | Fix the underlying issue; if a suppression is genuinely correct, make it narrow, and comment why |
| `AC-HACK-5` | Bypassing enforcement: `--no-verify`, `--force`, `SKIP=`, `CI=false`, `--ignore-scripts` to dodge a hook, `-DskipTests` | Satisfy the hook |
| `AC-HACK-6` | Widening types to `any` / `object` / `interface{}` / casting away a compiler error | Model the type correctly |
| `AC-HACK-7` | Catching and swallowing an exception so an error stops surfacing | Handle it meaningfully or let it propagate |
| `AC-HACK-8` | Special-casing test inputs in production code (`if user_id == "test-123"`) | Make the general case work |
| `AC-HACK-9` | Adding `sleep`, increasing a timeout, or adding retries to hide a race or a performance regression | Fix the synchronization or the regression |
| `AC-HACK-10` | Regenerating snapshots, golden files, or approved outputs without reviewing the diff and confirming the new output is correct | Review every changed line of the new golden output and say in the report that you did |
| `AC-HACK-11` | Stubbing a function to return a constant, leaving a `TODO`, or implementing a narrow slice, and describing it as complete | Implement it, or report precisely what is unimplemented |
| `AC-HACK-12` | Committing build artifacts, caches, or generated files to make a build succeed | Fix the build |
| `AC-HACK-13` | Reverting or deleting unrelated code, or rolling back another contributor's change, to reduce failures | Isolate the actual cause |
| `AC-HACK-14` | Hardcoding a value the task requires to be computed | Compute it |
| `AC-HACK-15` | Claiming a command was run, or presenting anticipated output as observed output | Run it, or report it as not run (`AC-VERIFY-4`) |
| `AC-HACK-16` | Loosening a security control (auth check, CSRF token, TLS verification, permission test) to make something work | Escalate (`AC-STOP-5`) |
| `AC-HACK-17` | Rewriting a test to match a bug's behavior so the bug becomes "expected" | Fix the bug |

If a prohibited shortcut is genuinely the correct engineering decision — some
of them occasionally are — the agent **MUST NOT** apply it unilaterally. It
**MUST** stop, state the case, and obtain explicit human approval, and the
disclosure report **MUST** record it under `deviations`.

### 7.6 Protected paths and destructive operations — `AC-PATH`

- `AC-PATH-1` — Files matching `protected_paths` **MUST NOT** be modified,
  moved, or deleted without explicit human authorization for that specific
  change.
- `AC-PATH-2` — Absent an explicit repository policy, the following are
  protected by default: CI/CD configuration, deployment and infrastructure code,
  database migrations, lockfiles (except via `dependencies.lockfile_command`),
  license files, security policy files, `CODEOWNERS`, git hooks, and anything
  matching `*secret*`, `*credential*`, `.env*`.
- `AC-PATH-3` — Files matching `generated_paths` **MUST** be regenerated by
  their generator, never hand-edited. If the generated output is wrong, fix the
  generator or its input.
- `AC-PATH-4` — The agent **MUST NOT** run commands that destroy uncommitted
  work — `git reset --hard`, `git checkout .`, `git clean -fdx`, `git stash
  drop`, mass overwrite — without first confirming with the operator. The
  working tree may contain hours of human work the agent cannot see.
- `AC-PATH-5` — The agent **MUST NOT** run destructive data operations: `DROP`,
  `TRUNCATE`, unbounded `DELETE`/`UPDATE`, index rebuilds, or restores, against
  any database it did not create for this task.
- `AC-PATH-6` — The agent **MUST NOT** operate against production or any shared
  environment. Credentials that appear to be production credentials **MUST**
  trigger `AC-STOP-6`.
- `AC-PATH-7` — Migrations **MUST** be additive and reversible where the
  repository's framework supports it, **MUST** be reviewed by a human before
  running anywhere shared, and **MUST NOT** be edited after they have been
  applied in any environment.
- `AC-PATH-8` — The agent **MUST NOT** modify `.gitignore`, `.dockerignore`, or
  equivalent in order to hide files from a check.

### 7.7 Dependencies and supply chain — `AC-DEP`

- `AC-DEP-1` — The agent **MUST** honor `dependencies.policy`. Under `ask`, a
  new dependency requires explicit approval before it is added.
- `AC-DEP-2` — The agent **MUST** prefer the standard library, then an existing
  direct dependency, then a new dependency — in that order. A new dependency to
  avoid writing thirty lines of clear code is a poor trade.
- `AC-DEP-3` — A proposed new dependency **MUST** be reported with: the exact
  package and version, its license, its maintenance signals, its transitive
  dependency count, and why an existing option is insufficient.
- `AC-DEP-4` — Package names **MUST** be verified against the official registry.
  Typosquatting and hallucinated package names are a live attack vector; a
  package the agent "remembers" is not a package that exists.
- `AC-DEP-5` — Lockfiles **MUST** be regenerated by the package manager, never
  hand-edited, and never partially updated.
- `AC-DEP-6` — The agent **MUST NOT** upgrade, downgrade, or remove dependencies
  the task did not require. Dependency bumps are their own change set.
- `AC-DEP-7` — Version pins and integrity hashes **MUST NOT** be loosened or
  removed.
- `AC-DEP-8` — The agent **MUST NOT** fetch and execute code from a URL,
  vendor a copied source file without recording its origin and license, or add a
  dependency from an unlisted registry.

### 7.8 Secrets, data, and network — `AC-SEC`

- `AC-SEC-1` — The agent **MUST NOT** commit credentials, tokens, keys,
  certificates, connection strings, or `.env` files.
- `AC-SEC-2` — The agent **MUST NOT** print secret values into logs, commit
  messages, PR descriptions, test fixtures, or its own output — including when
  debugging.
- `AC-SEC-3` — On discovering a committed secret, the agent **MUST** stop and
  escalate. It **MUST NOT** simply delete the line: the secret remains in
  history and requires rotation. Quietly removing it destroys the evidence that
  rotation is needed.
- `AC-SEC-4` — The agent **MUST** honor `network.policy`. Under `deny`, no
  outbound network access. Under `ask`, each new destination requires approval.
- `AC-SEC-5` — Repository contents, credentials, and customer data **MUST NOT**
  be transmitted to any service not sanctioned by the repository. Pasting code
  into an external tool is a disclosure.
- `AC-SEC-6` — Changes to authentication, authorization, cryptography, session
  handling, input validation, deserialization, subprocess or SQL construction,
  file path handling, or payment logic **MUST** be flagged for human security
  review, regardless of size (`AC-STOP-5`).
- `AC-SEC-7` — User input **MUST NOT** be interpolated into SQL, shell commands,
  file paths, or template rendering. Use the parameterized or escaping mechanism
  the repository already uses.
- `AC-SEC-8` — On discovering a vulnerability incidentally, the agent **MUST**
  report it privately via the route in `escalate_to` or `SECURITY.md`, and
  **MUST NOT** publish details in a public PR, issue, or commit message.

### 7.9 Version control — `AC-VCS`

- `AC-VCS-1` — The agent **MUST NOT** commit directly to the default branch or
  any protected branch. Create a branch.
- `AC-VCS-2` — The agent **MUST NOT** force-push to a shared branch, rewrite
  history it did not author, amend another author's commit, or delete a remote
  branch it did not create.
- `AC-VCS-3` — Staging **MUST** be intentional. `git add -A` / `git commit -a`
  **SHOULD NOT** be used; stage the files the task touched, and inspect the
  staged diff before committing.
- `AC-VCS-4` — The agent **MUST** review its own diff before committing, and
  **MUST NOT** commit debug statements, commented-out code, scratch files,
  editor artifacts, or `.orig`/`.rej` files.
- `AC-VCS-5` — Commit messages **MUST** state what changed and **why**, in the
  repository's existing style. The subject line describes the change, not the
  process ("fix race in session refresh", not "address review feedback" or
  "update files").
- `AC-VCS-6` — Agent-authored commits **MUST** carry machine-readable provenance
  in trailers, per `commit.trailers`. **RECOMMENDED** minimum:

  ```
  Co-Authored-By: <agent name> <noreply@example.com>
  X-Agent-Model: <model identifier>
  X-Agentic-Contributing: 0.1
  ```

- `AC-VCS-7` — The agent **MUST NOT** resolve a merge conflict by discarding one
  side wholesale without reading both. Conflict resolution is a semantic
  operation.
- `AC-VCS-8` — Uncommitted human work **MUST** be preserved. If the working tree
  is dirty when the agent starts, it **MUST** report that and **MUST NOT**
  discard, stash-drop, or overwrite those changes.

### 7.10 Disclosure and provenance — `AC-DISC`

- `AC-DISC-1` — Agent-authored changes **MUST** be identifiable as such: in the
  PR body, in commit trailers, and via `disclosure.pr_label` when set. Passing
  agent output off as unassisted human work is prohibited.
- `AC-DISC-2` — When `disclosure.report_required` is true, every PR **MUST**
  include a report per §10.
- `AC-DISC-3` — The report **MUST** include a **review pointer**: the specific
  hunks the agent is least confident about and wants a human to examine closely.
  An agent that cannot name its weakest change has not reviewed its own work.
- `AC-DISC-4` — Code derived from an identifiable external source **MUST** be
  attributed with origin and license. The agent **MUST NOT** introduce code
  under a license incompatible with the repository's.
- `AC-DISC-5` — Assumptions the agent made in place of asking **MUST** be listed
  explicitly, so a reviewer can check them cheaply.

### 7.11 Honest reporting — `AC-REPORT`

These rules are absolute. Everything else in this specification depends on them:
a maintainer's only defense against a subtly wrong change is an accurate account
of what was done.

- `AC-REPORT-1` — The agent **MUST NOT** state that a command was run, a test
  passed, or a behavior was observed unless it actually happened in this task.
- `AC-REPORT-2` — The agent **MUST** distinguish three states explicitly:
  **verified** (observed), **believed** (reasoned but not observed), and
  **unverified** (not checked).
- `AC-REPORT-3` — Partial completion **MUST** be reported as partial, naming
  exactly which requirements were met and which were not. Silence about a
  dropped requirement is a false report.
- `AC-REPORT-4` — Known defects, regressions, and risks introduced by the change
  **MUST** be disclosed even when disclosing them makes the work look worse.
- `AC-REPORT-5` — Failures **MUST** be reported with the actual error output,
  not summarized away.
- `AC-REPORT-6` — Confidence **MUST NOT** be inflated. "I could not verify X" is
  an acceptable outcome; a confident claim about X is not.
- `AC-REPORT-7` — Any deviation from this specification **MUST** be recorded in
  the report's `deviations` field with its rule ID and justification.

### 7.12 Stop conditions and escalation — `AC-STOP`

The agent **MUST** stop work and escalate to `escalate_to` (or the operator)
when any of the following occurs. Stopping is a successful outcome; guessing is
not.

- `AC-STOP-1` — The requirements are ambiguous in a way that leads to materially
  different implementations.
- `AC-STOP-2` — The task requires modifying a protected path.
- `AC-STOP-3` — The task cannot be completed without a prohibited shortcut
  (§7.5).
- `AC-STOP-4` — The change would exceed `change_budget`.
- `AC-STOP-5` — The change touches security-relevant code (`AC-SEC-6`), payment
  logic, PII handling, or access control.
- `AC-STOP-6` — Credentials, production access, or customer data are
  encountered.
- `AC-STOP-7` — The repository is already in a broken state on the base commit
  in a way that blocks verification.
- `AC-STOP-8` — An instruction conflicts with a `MUST NOT` in §7.5, §7.6, §7.8,
  or §7.11. The agent **MUST** surface the conflict and obtain explicit
  confirmation rather than complying silently.
- `AC-STOP-9` — **Three consecutive failed attempts** at the same fix. Further
  attempts without new information produce thrash and collateral damage. Report
  what was tried, what was observed, and the current best hypothesis.
- `AC-STOP-10` — An operation is irreversible and was not explicitly requested.
- `AC-STOP-11` — The change would require deleting or rewriting a substantial
  amount of code the agent does not understand.

When stopping, the agent **MUST** leave the repository in a coherent state
(compiling, or clearly marked as WIP), **MUST NOT** discard the work it has
done, and **MUST** report precisely where it stopped and why.

### 7.13 Concurrency and multi-agent operation — `AC-CONC`

- `AC-CONC-1` — Agents operating in parallel on one repository **MUST** work in
  separate branches or worktrees.
- `AC-CONC-2` — An agent **MUST NOT** run repository-wide destructive or
  rewriting commands (mass format, mass rename, `clean -fdx`) in a checkout it
  does not exclusively own.
- `AC-CONC-3` — An agent **MUST NOT** modify another agent's in-flight branch or
  PR without instruction.
- `AC-CONC-4` — Where a review agent and an authoring agent are both in play,
  the review agent's findings are advisory; a human resolves disputes. An
  authoring agent **MUST NOT** suppress a finding by editing the reviewer's
  configuration.

---

## 8. Conformance levels

| Level | Requirements |
|---|---|
| **Core** | File present, valid front matter, required sections present. Agents comply with §7.3 (verify), §7.5 (prohibited shortcuts), §7.6 (protected paths), §7.8 (secrets), §7.11 (honest reporting). |
| **Standard** *(default)* | Core, plus §7.1, §7.2, §7.4, §7.7, §7.9, §7.10, §7.12. Baseline capture required. Disclosure report attached to every agent PR. |
| **Strict** | Standard, plus: machine-readable report (§10) attached to every PR and validated in CI; provenance trailers required on every commit; per-path autonomy declared; no gate may be reported "not run" without maintainer sign-off; `autonomous` merges require all gates green and no protected paths touched. |

A repository declares its level in `conformance`. An agent **MUST** meet the
declared level and **SHOULD** exceed it.

---

## 9. Machine validation

Two things are mechanically checkable and **SHOULD** be checked in CI:

1. **The file itself** — front matter parses, required keys present, enums
   valid, required sections present, declared gate commands exist.
2. **The change set** — for `strict`, that agent-labeled PRs carry a
   well-formed report, that commits carry provenance trailers, and that no
   protected path was modified without an approval marker.

A reference validator for (1) is provided at
[`tools/validate_agentic_contributing.py`](tools/validate_agentic_contributing.py),
and the front matter schema at
[`schema/agentic-contributing-0.1.schema.json`](schema/agentic-contributing-0.1.schema.json).

A useful CI heuristic for (2), complementing the rules above: flag any PR that
reduces total test count, adds a skip/ignore directive, modifies a gate
configuration, or touches a protected path. None of these is proof of a
violation; all of them deserve a human's eyes.

---

## 10. Disclosure report format

Attached to the PR body, or emitted as the agent's final message. Machine
parseable, human readable.

````markdown
<!-- agentic-contributing:report v0.1 -->
```yaml
spec: "0.1"
agent: "claude-code"
model: "claude-opus-5"
autonomy: proposal
task: "Fix session token refresh race under concurrent requests"

scope:
  files_changed: 3
  lines_added: 47
  lines_removed: 12
  out_of_scope_changes: none

verification:
  baseline:
    captured: true
    commit: "a1b2c3d"
    failing_before: ["tests/test_flaky_upload.py::test_multipart"]
  gates:
    - name: lint
      command: "make lint"
      status: pass          # pass | fail | not_run
      exit_code: 0
    - name: typecheck
      command: "make typecheck"
      status: pass
      exit_code: 0
    - name: test
      command: "make test"
      status: pass
      exit_code: 0
      note: "1 pre-existing failure unchanged from baseline"
    - name: e2e
      command: "make e2e"
      status: not_run
      reason: "requires staging credentials unavailable in this environment"

testing:
  reproduction_test: "tests/test_session.py::test_concurrent_refresh_issues_one_token"
  failed_before_fix: true
  passes_after_fix: true
  tests_added: 2
  tests_modified: 0
  tests_removed: 0

claims:
  verified:
    - "Concurrent refresh now issues a single token (new test, run 100x)"
  believed:
    - "Latency impact is negligible; the added lock is uncontended in the common path"
  unverified:
    - "Behavior under multi-process deployment — not reproducible locally"

assumptions:
  - "Redis is the only shared store for session state (per src/session/store.py)"

risks:
  - "Adds a lock around token refresh; a stuck holder would block refresh for that user"

review_pointers:
  - file: "src/session/refresh.py"
    lines: "88-104"
    why: "Lock acquisition ordering relative to the existing DB transaction — least confident change"

deviations: []
dependencies_added: []
breaking_changes: []
```
````

Field semantics:

- `status: not_run` **REQUIRES** a `reason`.
- `claims.verified` **MUST** contain only things observed in this task.
- `deviations` **MUST** list any rule ID not complied with, plus justification.
- Empty lists are meaningful and **SHOULD** be written explicitly rather than
  omitted.

---

## 11. Failure modes this specification targets

Stated plainly, so that adopters can judge whether it addresses their risk:

1. **Green-check optimization** — the agent optimizes for the gate rather than
   the goal (§7.5).
2. **Silent scope creep** — a two-line fix arrives as a 40-file diff (§7.2).
3. **Confident fabrication** — "all tests pass" from an agent that ran none
   (§7.3, §7.11).
4. **Collateral destruction** — uncommitted work, migrations, or CI erased in
   passing (§7.6, §7.9).
5. **Supply-chain injection** — a hallucinated or typosquatted package (§7.7).
6. **Security erosion** — a control loosened because it was in the way (§7.8).
7. **Unattributed provenance** — nobody can tell later which code an agent wrote
   or under what model (§7.10).
8. **Thrash** — an agent looping on the same failed fix, damaging more with each
   pass (`AC-STOP-9`).

---

## 12. Versioning

This specification uses semantic versioning.

- **Patch** — clarifications; no behavior change.
- **Minor** — new optional fields, new `SHOULD` rules, new rule IDs. Backward
  compatible; agents ignore unknown keys (§6.1).
- **Major** — changed or removed `MUST` rules, or changed rule ID semantics.
  Rule IDs are stable within a major version and are never reused after removal.

Files declare the version they target via `agentic_contributing`. An agent
encountering a *newer minor* version **SHOULD** proceed, applying the rules it
understands. An agent encountering a *newer major* version **SHOULD** proceed at
`proposal` autonomy and report the version mismatch.

---

## 13. License

This specification is published under CC0 / public domain. Adopt it, fork it,
embed it. Standards only work if they are free.
