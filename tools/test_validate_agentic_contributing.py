"""Tests for the AGENTIC_CONTRIBUTING.md validator.

Every constraint is tested in both directions: a document that satisfies it and
a document that violates it. See AGENTIC_CONTRIBUTING.md, "Testing".
"""

from __future__ import annotations

import textwrap
import unittest
from pathlib import Path

from validate_agentic_contributing import REQUIRED_SECTIONS, validate_text

REPO_ROOT = Path(__file__).resolve().parent.parent

SECTIONS = "\n".join(f"## {name.title()}\n\ncontent\n" for name in REQUIRED_SECTIONS)

MINIMAL_FRONT_MATTER = """\
agentic_contributing: "0.1"
autonomy: proposal
verify:
  test: "make test"
"""


def doc(front_matter: str = MINIMAL_FRONT_MATTER, body: str = SECTIONS) -> str:
    return f"---\n{front_matter}---\n\n{body}"


def check(front_matter: str = MINIMAL_FRONT_MATTER, body: str = SECTIONS, strict: bool = False):
    return validate_text(Path("test.md"), doc(front_matter, body), strict=strict)


def rules(messages: list[str]) -> set[str]:
    return {m.split("]")[0].lstrip("[") for m in messages}


class TestMinimalDocument(unittest.TestCase):
    def test_minimal_document_is_valid(self):
        r = check()
        self.assertEqual(r.errors, [])
        self.assertEqual(r.level, "standard")

    def test_declared_conformance_is_reported(self):
        r = check(MINIMAL_FRONT_MATTER + "conformance: strict\n")
        self.assertEqual(r.errors, [])
        self.assertEqual(r.level, "strict")


class TestFrontMatterPresence(unittest.TestCase):
    def test_missing_front_matter_is_an_error(self):
        r = validate_text(Path("test.md"), "# No front matter\n" + SECTIONS, strict=False)
        self.assertFalse(r.ok)
        self.assertIn("no YAML front matter", r.errors[0])

    def test_malformed_yaml_is_an_error(self):
        r = check("agentic_contributing: \"0.1\"\n  bad: [indent\n")
        self.assertFalse(r.ok)

    def test_non_mapping_front_matter_is_an_error(self):
        r = check("- just\n- a\n- list\n")
        self.assertFalse(r.ok)
        self.assertIn("must be a YAML mapping", r.errors[0])


class TestRequiredKeys(unittest.TestCase):
    def test_missing_version_is_an_error(self):
        r = check("autonomy: proposal\nverify:\n  test: \"make test\"\n")
        self.assertIn("AC-FILE-1", rules(r.errors))

    def test_missing_autonomy_is_an_error(self):
        r = check("agentic_contributing: \"0.1\"\nverify:\n  test: \"t\"\n")
        self.assertIn("AC-AUTO-1", rules(r.errors))

    def test_missing_verify_is_an_error(self):
        r = check("agentic_contributing: \"0.1\"\nautonomy: proposal\n")
        self.assertIn("AC-VERIFY-1", rules(r.errors))

    def test_unparseable_version_is_an_error(self):
        r = check("agentic_contributing: draft\nautonomy: proposal\nverify:\n  test: \"t\"\n")
        self.assertIn("AC-FILE-1", rules(r.errors))

    def test_future_major_version_warns_but_passes(self):
        r = check("agentic_contributing: \"9.0\"\nautonomy: proposal\nverify:\n  test: \"t\"\n")
        self.assertTrue(r.ok)
        self.assertIn("AC-FILE-1", rules(r.warnings))


class TestEnums(unittest.TestCase):
    def test_valid_autonomy_levels_accepted(self):
        for level in ("advisory", "proposal", "supervised", "autonomous"):
            fm = f"agentic_contributing: \"0.1\"\nautonomy: {level}\nverify:\n  test: \"t\"\nprotected_paths: [\"x\"]\n"
            self.assertTrue(check(fm).ok, level)

    def test_unknown_autonomy_is_an_error(self):
        r = check("agentic_contributing: \"0.1\"\nautonomy: yolo\nverify:\n  test: \"t\"\n")
        self.assertIn("AC-AUTO-1", rules(r.errors))

    def test_unknown_conformance_is_an_error(self):
        r = check(MINIMAL_FRONT_MATTER + "conformance: paranoid\n")
        self.assertFalse(r.ok)

    def test_unknown_dependency_policy_is_an_error(self):
        r = check(MINIMAL_FRONT_MATTER + "dependencies:\n  policy: whatever\n")
        self.assertIn("AC-DEP-1", rules(r.errors))

    def test_known_dependency_policy_is_accepted(self):
        self.assertTrue(check(MINIMAL_FRONT_MATTER + "dependencies:\n  policy: deny\n").ok)

    def test_unknown_network_policy_is_an_error(self):
        r = check(MINIMAL_FRONT_MATTER + "network:\n  policy: sometimes\n")
        self.assertIn("AC-SEC-4", rules(r.errors))

    def test_unknown_message_style_is_an_error(self):
        r = check(MINIMAL_FRONT_MATTER + "commit:\n  message_style: haiku\n")
        self.assertIn("AC-VCS-5", rules(r.errors))


class TestVerifyBlock(unittest.TestCase):
    def test_non_string_command_is_an_error(self):
        r = check("agentic_contributing: \"0.1\"\nautonomy: proposal\nverify:\n  test: 42\n")
        self.assertIn("AC-VERIFY-1", rules(r.errors))

    def test_verify_without_test_or_all_warns(self):
        r = check("agentic_contributing: \"0.1\"\nautonomy: proposal\nverify:\n  lint: \"l\"\n")
        self.assertTrue(r.ok)
        self.assertIn("AC-VERIFY-1", rules(r.warnings))

    def test_verify_all_satisfies_the_gate_check(self):
        r = check("agentic_contributing: \"0.1\"\nautonomy: proposal\nverify:\n  all: \"make verify\"\n")
        self.assertNotIn("AC-VERIFY-1", rules(r.warnings))

    def test_test_scoped_without_paths_token_warns(self):
        r = check(MINIMAL_FRONT_MATTER + "  test_scoped: \"pytest -q\"\n")
        self.assertIn("AC-VERIFY-5", rules(r.warnings))

    def test_test_scoped_with_paths_token_is_clean(self):
        r = check(MINIMAL_FRONT_MATTER + "  test_scoped: \"pytest {paths}\"\n")
        self.assertNotIn("AC-VERIFY-5", rules(r.warnings))


class TestPathsAndBudget(unittest.TestCase):
    def test_protected_paths_must_be_strings(self):
        r = check(MINIMAL_FRONT_MATTER + "protected_paths:\n  - 42\n")
        self.assertIn("AC-PATH-1", rules(r.errors))

    def test_generated_paths_must_be_a_list(self):
        r = check(MINIMAL_FRONT_MATTER + "generated_paths: \"src/**\"\n")
        self.assertIn("AC-PATH-3", rules(r.errors))

    def test_budget_must_be_positive_integers(self):
        r = check(MINIMAL_FRONT_MATTER + "change_budget:\n  max_files: 0\n")
        self.assertIn("AC-SCOPE-7", rules(r.errors))

    def test_budget_rejects_non_integer(self):
        r = check(MINIMAL_FRONT_MATTER + "change_budget:\n  max_lines: \"lots\"\n")
        self.assertIn("AC-SCOPE-7", rules(r.errors))

    def test_valid_budget_is_accepted(self):
        r = check(MINIMAL_FRONT_MATTER + "change_budget:\n  max_files: 25\n  max_lines: 800\n")
        self.assertTrue(r.ok)

    def test_unknown_budget_key_warns(self):
        r = check(MINIMAL_FRONT_MATTER + "change_budget:\n  max_coffee: 3\n")
        self.assertTrue(r.ok)
        self.assertIn("AC-SCOPE-7", rules(r.warnings))


class TestOverrides(unittest.TestCase):
    def test_valid_override_is_accepted(self):
        fm = MINIMAL_FRONT_MATTER + textwrap.dedent(
            """\
            overrides:
              - paths: ["docs/**"]
                autonomy: supervised
                change_budget: { max_files: 100 }
            """
        )
        self.assertTrue(check(fm).ok)

    def test_override_without_paths_is_an_error(self):
        fm = MINIMAL_FRONT_MATTER + "overrides:\n  - autonomy: supervised\n"
        self.assertIn("AC-AUTO-3", rules(check(fm).errors))

    def test_override_with_empty_paths_is_an_error(self):
        fm = MINIMAL_FRONT_MATTER + "overrides:\n  - paths: []\n"
        self.assertIn("AC-AUTO-3", rules(check(fm).errors))

    def test_override_with_bad_autonomy_is_an_error(self):
        fm = MINIMAL_FRONT_MATTER + "overrides:\n  - paths: [\"docs/**\"]\n    autonomy: godmode\n"
        self.assertIn("AC-AUTO-3", rules(check(fm).errors))

    def test_overrides_must_be_a_list(self):
        fm = MINIMAL_FRONT_MATTER + "overrides:\n  paths: [\"docs/**\"]\n"
        self.assertIn("AC-AUTO-3", rules(check(fm).errors))


class TestSections(unittest.TestCase):
    def test_missing_required_section_is_an_error(self):
        body = "\n".join(f"## {n.title()}\n\nx\n" for n in REQUIRED_SECTIONS[:-1])
        r = check(body=body)
        self.assertFalse(r.ok)
        self.assertTrue(any("Escalation" in e for e in r.errors))

    def test_section_matching_is_case_insensitive(self):
        body = "\n".join(f"## {n.upper()}\n\nx\n" for n in REQUIRED_SECTIONS)
        self.assertTrue(check(body=body).ok)

    def test_recommended_sections_only_warn(self):
        r = check()
        self.assertTrue(r.ok)
        self.assertTrue(any("Known Landmines" in w for w in r.warnings))


class TestStrictMode(unittest.TestCase):
    def test_todo_is_a_warning_by_default(self):
        r = check(body=SECTIONS + "\nTODO: fill this in\n")
        self.assertTrue(r.ok)
        self.assertTrue(any("TODO" in w for w in r.warnings))

    def test_todo_is_an_error_under_strict(self):
        r = check(body=SECTIONS + "\nTODO: fill this in\n", strict=True)
        self.assertFalse(r.ok)

    def test_todo_in_front_matter_does_not_trigger_strict(self):
        fm = MINIMAL_FRONT_MATTER + "escalate_to: \"TODO\"\n"
        self.assertTrue(check(fm, strict=True).ok)

    def test_todo_inside_inline_code_is_not_a_todo(self):
        r = check(body=SECTIONS + "\nThe template still contains `TODO` markers.\n", strict=True)
        self.assertTrue(r.ok, r.errors)

    def test_todo_inside_a_fenced_block_is_not_a_todo(self):
        body = SECTIONS + "\n```yaml\nescalate_to: TODO\n```\n"
        self.assertTrue(check(body=body, strict=True).ok)


class TestCodeStripping(unittest.TestCase):
    def test_heading_inside_a_fence_is_not_a_section(self):
        body = "\n".join(f"## {n.title()}\n\nx\n" for n in REQUIRED_SECTIONS[:-1])
        body += "\n```markdown\n## Escalation\n```\n"
        r = check(body=body)
        self.assertFalse(r.ok)
        self.assertTrue(any("Escalation" in e for e in r.errors))

    def test_fence_stripping_preserves_headings_after_the_fence(self):
        body = "```python\nprint('hi')\n```\n\n" + SECTIONS
        self.assertTrue(check(body=body).ok)


class TestAutonomousWarning(unittest.TestCase):
    def test_autonomous_without_protected_paths_warns(self):
        fm = "agentic_contributing: \"0.1\"\nautonomy: autonomous\nverify:\n  test: \"t\"\n"
        r = check(fm)
        self.assertTrue(r.ok)
        self.assertIn("AC-AUTO-2", rules(r.warnings))

    def test_autonomous_with_protected_paths_is_clean(self):
        fm = (
            "agentic_contributing: \"0.1\"\nautonomy: autonomous\n"
            "verify:\n  test: \"t\"\nprotected_paths: [\"migrations/**\"]\n"
        )
        self.assertNotIn("AC-AUTO-2", rules(check(fm).warnings))


class TestForwardCompatibility(unittest.TestCase):
    def test_unknown_top_level_keys_are_ignored(self):
        r = check(MINIMAL_FRONT_MATTER + "future_field:\n  nested: true\n")
        self.assertTrue(r.ok)


class TestRepositoryFiles(unittest.TestCase):
    """The spec's own artifacts must satisfy the spec (AC-FILE-1)."""

    def test_repository_own_file_is_strict_valid(self):
        path = REPO_ROOT / "AGENTIC_CONTRIBUTING.md"
        r = validate_text(path, path.read_text(encoding="utf-8"), strict=True)
        self.assertEqual(r.errors, [], f"{path} failed strict validation")

    def test_template_is_valid_with_todos_allowed(self):
        path = REPO_ROOT / "templates" / "AGENTIC_CONTRIBUTING.template.md"
        r = validate_text(path, path.read_text(encoding="utf-8"), strict=False)
        self.assertEqual(r.errors, [], f"{path} failed validation")


if __name__ == "__main__":
    unittest.main()
