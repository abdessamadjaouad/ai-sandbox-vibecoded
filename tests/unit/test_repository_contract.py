from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_project_rules_and_skills_exist() -> None:
    """Ensure the repository keeps core OpenCode instruction files in place."""
    root = _repo_root()
    agents_file = root / "AGENTS.md"
    skills_root = root / ".opencode" / "skills"

    assert agents_file.exists(), "AGENTS.md is required at repository root."
    assert skills_root.is_dir(), "Expected .opencode/skills directory to exist."

    skill_files = sorted(skills_root.glob("*/SKILL.md"))
    assert skill_files, "Expected at least one skill definition under .opencode/skills."


def test_skill_frontmatter_has_required_fields() -> None:
    """Validate that each skill declares required OpenCode metadata."""
    root = _repo_root()
    skill_files = sorted((root / ".opencode" / "skills").glob("*/SKILL.md"))

    for skill_file in skill_files:
        text = skill_file.read_text(encoding="utf-8")
        assert "name:" in text, f"Missing frontmatter name in {skill_file}"
        assert "description:" in text, f"Missing frontmatter description in {skill_file}"
