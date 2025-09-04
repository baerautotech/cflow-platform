from __future__ import annotations

from pathlib import Path
import json
import tempfile

from cflow_platform.core.profiles import load_profiles, resolve_profile, InstructionProfile


def _write(dir_path: Path, rel: str, content: str) -> Path:
    path = dir_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_load_profiles_includes_builtin() -> None:
    profiles = load_profiles(Path.cwd())
    assert "quick" in profiles
    prof = profiles["quick"]
    assert isinstance(prof, InstructionProfile)
    assert prof.verify_mode == "tests"


def test_project_profile_overrides_builtin() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Seed a default .cursor/rules profile overriding name "quick"
        data = {
            "name": "quick",
            "description": "Override quick",
            "goals": ["plan", "apply", "verify"],
            "test_paths": ["tests/fast"],
            "verify_mode": "tests",
        }
        _write(root, ".cursor/rules/quick.profile.json", json.dumps(data))
        profiles = load_profiles(root)
        assert "quick" in profiles
        assert profiles["quick"].description == "Override quick"
        assert profiles["quick"].test_paths == ["tests/fast"]


def test_policies_only_profile_is_accepted() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = {
            "name": "strict",
            "description": "Policies-only profile",
            "policies": {
                "minimal_edits": True,
                "fail_closed_lint": True,
            },
        }
        _write(root, ".cursor/rules/strict.profile.json", json.dumps(data))
        profiles = load_profiles(root)
        assert "strict" in profiles
        prof = profiles["strict"]
        assert isinstance(prof, InstructionProfile)
        assert prof.test_paths  # defaulted


def test_resolve_profile_case_insensitive() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        data = {
            "name": "Custom",
            "description": "Custom",
            "goals": ["plan", "apply", "verify"],
            "test_paths": ["tests/custom"],
        }
        _write(root, ".cursor/rules/custom.profile.json", json.dumps(data))
        prof = resolve_profile("custom", root)
        assert prof is not None
        assert prof.test_paths == ["tests/custom"]


