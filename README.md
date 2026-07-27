# AGENTIC_CONTRIBUTING.md

**A contribution contract for autonomous coding agents.**

`CONTRIBUTING.md` tells humans how to contribute. It assumes someone with
judgment, accountability, a reputation to protect, and the instinct to ask
before doing something irreversible.

Agents have a reward signal, a context window, and shell access.

`AGENTIC_CONTRIBUTING.md` is the machine-facing counterpart: one file, at a
known path, in a known format, stating what an agent may change, what it must
never do, how it must verify its work, and what it must disclose. Vendor
neutral, human readable, CI checkable.

- **[SPEC.md](SPEC.md)** — the normative specification (v0.1.0)
- **[templates/AGENTIC_CONTRIBUTING.template.md](templates/AGENTIC_CONTRIBUTING.template.md)** — copy this into your repo
- **[schema/agentic-contributing-0.1.schema.json](schema/agentic-contributing-0.1.schema.json)** — front matter JSON Schema
- **[tools/validate_agentic_contributing.py](tools/validate_agentic_contributing.py)** — reference validator
- **[AGENTIC_CONTRIBUTING.md](AGENTIC_CONTRIBUTING.md)** — this repo's own, dogfooded

---

## The problem

Agents do not fail like junior engineers fail. They fail in specific,
recognizable, repeatable ways:

| Failure | What it looks like |
|---|---|
| **Green-check optimization** | The test was failing, so it got skipped. The type error was hard, so it got `# type: ignore`. The lint rule was in the way, so the threshold moved. |
| **Silent scope creep** | A two-line fix arrives as a 40-file diff with a reformat, three renames, and a dependency bump. |
| **Confident fabrication** | "All tests pass." No test was run. |
| **Collateral destruction** | `git checkout .` erased four hours of uncommitted human work. |
| **Supply-chain injection** | A package name the model remembered, which does not exist, which someone has now registered. |
| **Security erosion** | The auth check was blocking the fix, so it is gone now. |
| **Thrash** | Eight attempts at the same failing fix, each one damaging more. |

None of these are prevented by a `CLAUDE.md` that says "please write good code."
They are prevented by an explicit contract with stable, citable rules, declared
verification gates, and a mandatory disclosure of what was *not* checked.

## What the file looks like

Machine contract on top, human contract below.

```yaml
---
agentic_contributing: "0.1"
autonomy: proposal            # advisory | proposal | supervised | autonomous
conformance: standard

verify:
  lint: "make lint"
  typecheck: "make typecheck"
  test: "make test"

baseline_required: true       # capture gate state BEFORE changing anything

protected_paths:
  - "migrations/**"
  - ".github/workflows/**"
  - "**/*.lock"

change_budget: { max_files: 25, max_lines: 800 }
dependencies: { policy: ask }
network: { policy: deny }

overrides:
  - paths: ["src/billing/**"]
    autonomy: proposal
    require_human_review: true

escalate_to: "#platform-oncall"
---
```

…followed by five required prose sections: **Ground rules**, **Definition of
done**, **Testing**, **Do not touch**, **Escalation**.

The single highest-value optional section is **Known landmines** — the things
that have burned people, which no agent can infer: the test that only passes
with a warm cache, the module whose import order matters, the service that
needs a restart after a schema change.

## Adopt it

```bash
curl -O https://raw.githubusercontent.com/snoodleboot-io/agentic_contributing/main/templates/AGENTIC_CONTRIBUTING.template.md
mv AGENTIC_CONTRIBUTING.template.md AGENTIC_CONTRIBUTING.md
$EDITOR AGENTIC_CONTRIBUTING.md            # fill in every TODO
python3 validate_agentic_contributing.py --strict AGENTIC_CONTRIBUTING.md
```

Filling it in takes about twenty minutes. Three of those minutes — the
`## Known landmines` section — will save more agent-hours than the rest of the
file combined.

Validate it in CI:

```yaml
- run: pip install pyyaml
- run: python3 tools/validate_agentic_contributing.py --strict AGENTIC_CONTRIBUTING.md
```

## How it relates to files you already have

It does not replace them. It answers a different question.

| File | Question |
|---|---|
| `README.md` | What is this and how do I run it? |
| `CONTRIBUTING.md` | How do humans propose changes? |
| `AGENTS.md` | How does an agent orient here — layout, commands, conventions? |
| `CLAUDE.md`, `.cursorrules` | Vendor-specific agent instructions |
| **`AGENTIC_CONTRIBUTING.md`** | **What may an agent do, what must it never do, and what must it prove before claiming done?** |

If you have `AGENTS.md`, do not duplicate it here — reference it. Duplicated
instructions drift, and drifted instructions are worse than absent ones.

Precedence, when they conflict: a live human instruction, then
`AGENTIC_CONTRIBUTING.md` (nearest ancestor in a monorepo), then vendor files,
then `AGENTS.md`, then human docs, then the agent's own habits. With one
exception: an instruction to violate a safety rule — secrets, destructive
operations, protected paths — must be confirmed explicitly, never inferred.

## The core of it

Every rule has a stable ID you can cite in review (`AC-TEST-1`, `AC-HACK-4`).
The ones that matter most:

**Prove it worked.** Capture a baseline before you change anything, so
pre-existing failures are distinguishable from yours. Run every gate after your
*final* edit. Record the exact command and exit code. A gate you could not run
is reported `not_run` with a reason — never as passing, never omitted.

**Fix the bug, not the test.** A bug fix starts with a test that reproduces the
bug and fails on the unmodified code. Report that it failed before and passes
after. A "fix" never demonstrated to fix anything is a guess.

**Never weaken the gate to pass the gate.** No deleted or skipped tests, no
loosened assertions, no blanket suppressions, no `--no-verify`, no snapshot
regeneration without reading the diff, no `any` to silence a type error, no
sleep to hide a race. Seventeen specific prohibitions, each with a "do instead."

**Smallest change that fully solves it.** Improvements you notice but were not
asked to make get reported, not performed. Five suggestions is a contribution;
five unrequested refactors buried in a bug fix is a liability.

**Stopping is a good outcome.** Ambiguous requirements, a protected path, a
security-relevant change, credentials in the tree, budget exceeded, or three
consecutive failed attempts at the same fix — stop and escalate. Further
attempts without new information produce thrash and collateral damage.

**Say what you did not check.** Every PR carries a disclosure report separating
**verified** (observed), **believed** (reasoned), and **unverified** (not
checked) — plus a review pointer naming the hunk the agent is least confident
about. An agent that cannot name its own weakest change has not reviewed its
work.

## Conformance

| Level | Requires |
|---|---|
| **Core** | Valid file; verification, prohibited shortcuts, protected paths, secrets, honest reporting |
| **Standard** | Core + scope discipline, testing doctrine, baseline capture, disclosure report |
| **Strict** | Standard + machine-checked reports in CI, provenance trailers on every commit, per-path autonomy, no unverified gates without sign-off |

## Status

Version 0.1.0, draft. The specification is stable enough to adopt and young
enough to argue with. Rule IDs are permanent within a major version.

Issues and proposals welcome — see [AGENTIC_CONTRIBUTING.md](AGENTIC_CONTRIBUTING.md)
if you are an agent, and [SPEC.md](SPEC.md) §12 for the versioning policy.

## License

[CC0 1.0](LICENSE) — public domain. Standards only work if they are free.
