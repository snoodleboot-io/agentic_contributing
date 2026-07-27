# Examples

One worked example, end to end.

| File | What it is |
|---|---|
| [`AGENTIC_CONTRIBUTING.example.md`](AGENTIC_CONTRIBUTING.example.md) | A fully filled-in contract for `ledger-api`, a fictional double-entry billing service (FastAPI + Postgres + Kafka). No placeholders. Strict-conformant. |
| [`disclosure-report.example.md`](disclosure-report.example.md) | The PR an agent produced working under that contract — including the part it could not finish, and why. |

Read them in that order. Together they show the loop the specification
describes: a repository declares its contract, an agent works inside it, and
the agent hands back an account of what it did that a reviewer can act on.

## What to steal from the contract

The front matter is mechanical — copy it and change the commands. The parts
worth reading closely are the ones no template can write for you:

- **`overrides`** puts `docs/**` at `autonomous` and `src/ledger/posting/**` at
  `proposal`. Autonomy is not a property of a repository; it is a property of a
  directory. Almost every repo has areas where an agent should merge freely and
  areas where it should not touch anything without a human.
- **`## Do not touch`** gives a reason for every entry. The reason is what lets
  an agent reason about the case you did not enumerate. "Migrations are applied
  in production the hour they merge" generalizes; "do not edit migrations" does
  not.
- **`## Known landmines`** is the highest-value section in the file and the one
  most likely to be left empty. Every entry there is a real hour someone lost:
  the formatter that rewrites files mid-stage, the fixture that does not reset
  sequences, the regeneration that is unstable across patch versions. An agent
  cannot infer any of it, and will otherwise rediscover each one by breaking
  something.
- **Ground rule 4** — "amounts are `Decimal`, never `float`" — is a domain
  invariant stated as an absolute. One line, and it forecloses an entire class
  of plausible-looking wrong change.

## What to steal from the report

That it is not a clean success. The agent fixed the race, stopped at the
migration because migrations are a protected path, proposed the DDL, and marked
itself `completion: partial`. It reported a gate it could not run as `not_run`
rather than assuming, separated what it observed from what it reasoned, and
named the hunk it was least sure about.

A report full of confident green tells a reviewer nothing about where to look.
This one tells them exactly where.

## Validating

Both files are checked in CI. The contract must pass strict validation with no
unresolved placeholders — an example that has rotted is worse than no example:

```bash
make check-examples
```
