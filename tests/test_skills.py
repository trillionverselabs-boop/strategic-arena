"""R2 — the preset packs ship as plugin skills, not prefilled text.

Skills are a normal Hermes surface: no new capability, no manifest change.
"""

from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
PACKS = ["upfront-launch", "upfront-pricing", "upfront-deprecation", "upfront-openweight"]


def _frontmatter(md: Path) -> dict:
    text = md.read_text()
    assert text.startswith("---"), f"{md} has no frontmatter"
    end = text.index("\n---", 3)
    return yaml.safe_load(text[3:end])


@pytest.mark.parametrize("pack", PACKS)
def test_pack_exists_with_valid_frontmatter(pack):
    md = SKILLS / pack / "SKILL.md"
    assert md.exists(), f"missing {md}"
    fm = _frontmatter(md)
    assert fm["name"] == pack, "name must match the directory"
    assert isinstance(fm["description"], str) and 1 <= len(fm["description"]) <= 1024


@pytest.mark.parametrize("pack", PACKS)
def test_pack_teaches_a_checklist_and_states_the_boundary(pack):
    body = (SKILLS / pack / "SKILL.md").read_text()
    assert "- [ ]" in body, "every pack needs a checklist the agent can tick"
    assert "not a prediction" in body.lower(), "the boundary must be stated once"
    assert "upfront_run" in body, "the pack must say which tool runs the review"
    lines = body.splitlines()
    assert 35 <= len(lines) <= 110, f"{pack} is {len(lines)} lines (target 40-80)"


def test_all_packs_register_under_the_plugin_namespace():
    from upfront import register

    class Ctx:
        llm = None

        def __init__(self):
            self.skills = {}
            self.tools = {}

        def has_capability(self, _name):
            return False

        def register_tool(self, name, toolset, schema, handler):
            self.tools[name] = schema

        def register_skill(self, name, path):
            self.skills[name] = path

        def log(self, *_a):
            pass

    c = Ctx()
    register(c)
    for pack in PACKS + ["upfront-review"]:
        assert pack in c.skills, f"{pack} did not register"


def test_skills_add_no_capability():
    manifest = yaml.safe_load((REPO / "plugin.yaml").read_text())
    assert manifest["capabilities"] == ["llm.model_override"]
