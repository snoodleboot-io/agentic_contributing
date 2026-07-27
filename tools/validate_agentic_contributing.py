#!/usr/bin/env python3
"""Reference validator for AGENTIC_CONTRIBUTING.md (spec 0.1).

Checks the machine-readable front matter and the required prose sections, and
reports the conformance level the file actually achieves.

Usage:
    validate_agentic_contributing.py [PATH ...] [--strict] [--quiet]

With no PATH, discovers AGENTIC_CONTRIBUTING.md at the repository root, then
.github/, then docs/ (AC-FILE-2).

Exit codes:
    0  valid
    1  errors found
    2  could not run (no file, unreadable, missing dependency)

Requires PyYAML.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - environment dependent
    sys.stderr.write(
        "error: PyYAML is required.  pip install pyyaml\n"
    )
    raise SystemExit(2)

SPEC_VERSION = "0.1"
FILENAME = "AGENTIC_CONTRIBUTING.md"
SEARCH_DIRS = (".", ".github", "docs")

AUTONOMY_LEVELS = ("advisory", "proposal", "supervised", "autonomous")
CONFORMANCE_LEVELS = ("core", "standard", "strict")
POLICY_VALUES = ("allow", "ask", "deny")
MESSAGE_STYLES = ("conventional", "imperative", "free")

REQUIRED_SECTIONS = (
    "ground rules",
    "definition of done",
    "testing",
    "do not touch",
    "escalation",
)
RECOMMENDED_SECTIONS = (
    "architecture invariants",
    "known landmines",
)

FRONT_MATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
TODO_RE = re.compile(r"\bTODO\b")

FENCE_RE = re.compile(r"^(`{3,}|~{3,}).*?^\1[ \t]*$", re.DOTALL | re.MULTILINE)
INLINE_CODE_RE = re.compile(r"(`+)(?:.|\n)*?\1")


def strip_code(text: str) -> str:
    """Blank out fenced blocks and inline code spans, preserving line numbering.

    A heading or a TODO inside a code span is an example, not a declaration.
    """
    def blank(m: re.Match[str]) -> str:
        return "\n" * m.group(0).count("\n")

    return INLINE_CODE_RE.sub(blank, FENCE_RE.sub(blank, text))


@dataclass
class Result:
    path: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    level: str | None = None

    @property
    def ok(self) -> bool:
        return not self.errors


def _err(r: Result, rule: str, msg: str) -> None:
    r.errors.append(f"[{rule}] {msg}")


def _warn(r: Result, rule: str, msg: str) -> None:
    r.warnings.append(f"[{rule}] {msg}")


def _check_str_map(r: Result, obj, key: str, rule: str) -> dict:
    """Return obj[key] if it is a mapping of str -> str, else record an error."""
    value = obj.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        _err(r, rule, f"`{key}` must be a mapping")
        return {}
    for k, v in value.items():
        if not isinstance(v, str):
            _err(r, rule, f"`{key}.{k}` must be a string command")
    return value


def _check_glob_list(r: Result, obj, key: str, rule: str) -> None:
    value = obj.get(key)
    if value is None:
        return
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        _err(r, rule, f"`{key}` must be a list of glob strings")


def _check_enum(r: Result, obj, key: str, allowed, rule: str) -> None:
    value = obj.get(key)
    if value is None:
        return
    if value not in allowed:
        _err(r, rule, f"`{key}` must be one of {', '.join(allowed)} (got {value!r})")


def _check_budget(r: Result, budget, where: str, rule: str) -> None:
    if budget is None:
        return
    if not isinstance(budget, dict):
        _err(r, rule, f"`{where}` must be a mapping")
        return
    for k, v in budget.items():
        if k not in ("max_files", "max_lines", "max_commits"):
            _warn(r, rule, f"`{where}.{k}` is not a recognized budget key")
        elif not isinstance(v, int) or isinstance(v, bool) or v < 1:
            _err(r, rule, f"`{where}.{k}` must be a positive integer")


def validate_front_matter(r: Result, fm: dict) -> None:
    # AC-FILE / §6.1 required keys
    version = fm.get("agentic_contributing")
    if version is None:
        _err(r, "AC-FILE-1", "missing required key `agentic_contributing`")
    else:
        version = str(version)
        if not re.fullmatch(r"\d+\.\d+(\.\d+)?", version):
            _err(r, "AC-FILE-1", f"`agentic_contributing` is not a version: {version!r}")
        elif version.split(".")[0] != SPEC_VERSION.split(".")[0]:
            _warn(
                r,
                "AC-FILE-1",
                f"file targets spec major version {version}, validator implements {SPEC_VERSION}",
            )

    if "autonomy" not in fm:
        _err(r, "AC-AUTO-1", "missing required key `autonomy`")
    _check_enum(r, fm, "autonomy", AUTONOMY_LEVELS, "AC-AUTO-1")
    _check_enum(r, fm, "conformance", CONFORMANCE_LEVELS, "AC-FILE-1")

    if "verify" not in fm:
        _err(r, "AC-VERIFY-1", "missing required key `verify`")
    verify = _check_str_map(r, fm, "verify", "AC-VERIFY-1")
    if verify and not any(k in verify for k in ("test", "all")):
        _warn(
            r,
            "AC-VERIFY-1",
            "`verify` declares no `test` or `all` gate; agents will have nothing to run",
        )
    scoped = verify.get("test_scoped")
    if isinstance(scoped, str) and "{paths}" not in scoped:
        _warn(r, "AC-VERIFY-5", "`verify.test_scoped` does not contain the {paths} token")

    if "baseline_required" in fm and not isinstance(fm["baseline_required"], bool):
        _err(r, "AC-VERIFY-2", "`baseline_required` must be a boolean")

    _check_glob_list(r, fm, "protected_paths", "AC-PATH-1")
    _check_glob_list(r, fm, "generated_paths", "AC-PATH-3")
    _check_budget(r, fm.get("change_budget"), "change_budget", "AC-SCOPE-7")

    deps = fm.get("dependencies")
    if isinstance(deps, dict):
        _check_enum(r, deps, "policy", POLICY_VALUES, "AC-DEP-1")
    elif deps is not None:
        _err(r, "AC-DEP-1", "`dependencies` must be a mapping")

    net = fm.get("network")
    if isinstance(net, dict):
        _check_enum(r, net, "policy", POLICY_VALUES, "AC-SEC-4")
    elif net is not None:
        _err(r, "AC-SEC-4", "`network` must be a mapping")

    commit = fm.get("commit")
    if isinstance(commit, dict):
        _check_enum(r, commit, "message_style", MESSAGE_STYLES, "AC-VCS-5")
        trailers = commit.get("trailers")
        if trailers is not None and (
            not isinstance(trailers, list) or not all(isinstance(t, str) for t in trailers)
        ):
            _err(r, "AC-VCS-6", "`commit.trailers` must be a list of strings")
    elif commit is not None:
        _err(r, "AC-VCS-5", "`commit` must be a mapping")

    disclosure = fm.get("disclosure")
    if isinstance(disclosure, dict):
        if "report_required" in disclosure and not isinstance(
            disclosure["report_required"], bool
        ):
            _err(r, "AC-DISC-2", "`disclosure.report_required` must be a boolean")
    elif disclosure is not None:
        _err(r, "AC-DISC-2", "`disclosure` must be a mapping")

    overrides = fm.get("overrides")
    if overrides is not None:
        if not isinstance(overrides, list):
            _err(r, "AC-AUTO-3", "`overrides` must be a list")
        else:
            for i, ov in enumerate(overrides):
                where = f"overrides[{i}]"
                if not isinstance(ov, dict):
                    _err(r, "AC-AUTO-3", f"`{where}` must be a mapping")
                    continue
                paths = ov.get("paths")
                if not isinstance(paths, list) or not paths or not all(
                    isinstance(p, str) for p in paths
                ):
                    _err(r, "AC-AUTO-3", f"`{where}.paths` must be a non-empty list of globs")
                _check_enum(r, ov, "autonomy", AUTONOMY_LEVELS, "AC-AUTO-3")
                _check_enum(r, ov, "conformance", CONFORMANCE_LEVELS, "AC-AUTO-3")
                _check_budget(r, ov.get("change_budget"), f"{where}.change_budget", "AC-SCOPE-7")

    if fm.get("autonomy") == "autonomous" and not fm.get("protected_paths"):
        _warn(
            r,
            "AC-AUTO-2",
            "`autonomy: autonomous` with no `protected_paths` grants merge authority "
            "over every file in the repository",
        )


def validate_sections(r: Result, body: str) -> None:
    found = {m.group(1).strip().lower().rstrip(":") for m in H2_RE.finditer(body)}
    for section in REQUIRED_SECTIONS:
        if section not in found:
            _err(r, "AC-FILE-1", f"missing required section `## {section.title()}`")
    for section in RECOMMENDED_SECTIONS:
        if section not in found:
            _warn(r, "AC-FILE-1", f"recommended section `## {section.title()}` is absent")


def validate_text(path: Path, text: str, strict: bool) -> Result:
    r = Result(path=path)

    m = FRONT_MATTER_RE.match(text)
    if not m:
        _err(r, "AC-FILE-1", "no YAML front matter block found (must start with `---`)")
        return r

    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError as exc:
        _err(r, "AC-FILE-1", f"front matter is not valid YAML: {exc}")
        return r

    if fm is None:
        fm = {}
    if not isinstance(fm, dict):
        _err(r, "AC-FILE-1", "front matter must be a YAML mapping")
        return r

    validate_front_matter(r, fm)

    prose = strip_code(text[m.end():])
    validate_sections(r, prose)

    todos = len(TODO_RE.findall(prose))
    if todos:
        msg = f"{todos} unresolved TODO marker(s) in the prose"
        if strict:
            _err(r, "AC-FILE-1", msg)
        else:
            _warn(r, "AC-FILE-1", msg)

    declared = fm.get("conformance", "standard")
    r.level = declared if r.ok else None
    return r


def discover(root: Path) -> Path | None:
    for d in SEARCH_DIRS:
        candidate = root / d / FILENAME
        if candidate.is_file():
            return candidate
    return None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Validate AGENTIC_CONTRIBUTING.md files.")
    p.add_argument("paths", nargs="*", type=Path, help="files to validate")
    p.add_argument("--strict", action="store_true", help="treat TODO markers as errors")
    p.add_argument("--quiet", action="store_true", help="only print problems")
    args = p.parse_args(argv)

    paths = list(args.paths)
    if not paths:
        found = discover(Path.cwd())
        if found is None:
            sys.stderr.write(
                f"error: no {FILENAME} found in {', '.join(SEARCH_DIRS)}\n"
            )
            return 2
        paths = [found]

    failed = False
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            sys.stderr.write(f"error: cannot read {path}: {exc}\n")
            return 2

        r = validate_text(path, text, strict=args.strict)
        for e in r.errors:
            print(f"{path}: error: {e}")
        for w in r.warnings:
            print(f"{path}: warning: {w}")
        if r.ok:
            if not args.quiet:
                print(f"{path}: ok (conformance: {r.level})")
        else:
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
