from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import os


@dataclass
class InstructionProfile:
    name: str
    description: str
    goals: List[str]
    test_paths: List[str]
    verify_mode: str = "tests"


def _builtin_profiles() -> Dict[str, InstructionProfile]:
    return {
        "quick": InstructionProfile(
            name="quick",
            description="Fast feedback profile running unit tests",
            goals=["plan", "apply", "verify"],
            test_paths=["cflow_platform/tests"],
            verify_mode="tests",
        ),
    }


def _parse_profile_json(data: Dict[str, Any]) -> Optional[InstructionProfile]:
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip() or f"Profile {name}"
    goals = data.get("goals")
    test_paths = data.get("test_paths")
    verify_mode = (data.get("verify_mode") or "tests").strip()

    # Support two shapes:
    # 1) Full InstructionProfile JSON with goals/test_paths
    # 2) Policy-oriented profile with only name/description/policies
    if isinstance(goals, list) and isinstance(test_paths, list):
        try:
            return InstructionProfile(
                name=name,
                description=description,
                goals=[str(g) for g in goals],
                test_paths=[str(p) for p in test_paths],
                verify_mode=verify_mode or "tests",
            )
        except Exception:
            return None

    # If policies-only, derive a usable InstructionProfile with sensible defaults
    if name:
        return InstructionProfile(
            name=name,
            description=description,
            goals=["plan", "apply", "verify"],
            test_paths=["cflow_platform/tests"],
            verify_mode="tests",
        )
    return None


def _discover_project_profiles(repo_root: Path) -> Dict[str, InstructionProfile]:
    profiles: Dict[str, InstructionProfile] = {}
    rules_dir = repo_root / ".cursor" / "rules"
    if not rules_dir.exists() or not rules_dir.is_dir():
        return profiles
    for path in rules_dir.glob("*.profile.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict):
            prof = _parse_profile_json(data)
            if prof:
                profiles[prof.name] = prof
        # Optionally support arrays of profiles in a single file
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    prof = _parse_profile_json(item)
                    if prof:
                        profiles[prof.name] = prof
    return profiles


def load_profiles(repo_root: Optional[Path] = None) -> Dict[str, InstructionProfile]:
    root = repo_root or Path.cwd()
    # Start with builtin defaults
    profiles = dict(_builtin_profiles())
    # Merge project profiles with precedence (project overrides builtin on name match)
    project_profiles = _discover_project_profiles(root)
    profiles.update(project_profiles)
    return profiles


def resolve_profile(profile_name: str, repo_root: Optional[Path] = None) -> Optional[InstructionProfile]:
    profiles = load_profiles(repo_root)
    # Exact match first
    prof = profiles.get(profile_name)
    if prof:
        return prof
    # Fallback: case-insensitive match
    lowered = {k.lower(): v for k, v in profiles.items()}
    return lowered.get(profile_name.lower())


