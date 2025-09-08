from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
import os
import hashlib

from cflow_platform.core.services.llm.openrouter_client import chat_completion


@dataclass
class CodegenConstraints:
    minimal_edits: bool = True
    strict_single_match: bool = True
    atomic: bool = True
    allowlist: Optional[List[str]] = None
    max_edits: int = 10
    max_snippet_chars: int = 4000


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _is_allowed(path: Path, allowlist: Optional[List[str]]) -> bool:
    if not allowlist:
        return True
    p = path.resolve().as_posix()
    rel = path.as_posix()
    for rule in allowlist:
        rule = (rule or "").replace("\\", "/").rstrip("/")
        if not rule:
            continue
        if p == rule or rel == rule:
            return True
        if p.startswith(rule + "/") or rel.startswith(rule + "/"):
            return True
    return False


def _extract_json_block(text: str) -> Optional[Dict[str, Any]]:
    try:
        # Fast path
        return json.loads(text)
    except Exception:
        pass
    # Try to locate the outermost JSON object in the text
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        frag = text[start : end + 1]
        try:
            return json.loads(frag)
        except Exception:
            return None
    return None


class CodegenHandlers:
    """Generate minimal EditPlan[] using an LLM and write .cerebraflow/edits.json.

    Enforces AEMI/VEG constraints: allowlist, atomic intent, strict single match, caps.
    """

    async def handle_generate_edits(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        task: str = (arguments.get("task") or "").strip()
        if not task:
            return {"status": "error", "message": "task is required"}

        context_files: List[str] = [str(p) for p in (arguments.get("context_files") or [])]
        apis: List[Dict[str, Any]] = list(arguments.get("apis", []) or [])
        tests: List[str] = [str(p) for p in (arguments.get("tests") or [])]
        constraints_in: Dict[str, Any] = dict(arguments.get("constraints", {}) or {})
        success_criteria: List[Dict[str, Any]] = list(arguments.get("success_criteria", []) or [])

        constraints = CodegenConstraints(
            minimal_edits=bool(constraints_in.get("minimal_edits", True)),
            strict_single_match=bool(constraints_in.get("strict_single_match", True)),
            atomic=bool(constraints_in.get("atomic", True)),
            allowlist=[str(x) for x in (constraints_in.get("allowlist") or [])] or [Path.cwd().resolve().as_posix()],
            max_edits=int(constraints_in.get("max_edits", 10) or 10),
            max_snippet_chars=int(constraints_in.get("max_snippet_chars", 4000) or 4000),
        )

        # Build a compact, ranked context bundle (simple pass-through for now)
        files_for_prompt: List[str] = []
        for p in context_files:
            try:
                pp = Path(p)
                if pp.is_file() and pp.stat().st_size < 200_000:
                    files_for_prompt.append(p)
            except Exception:
                continue
        files_for_prompt = files_for_prompt[:20]

        # Prepare prompt
        system = (
            "You are a senior engineer. Produce a minimal, bounded edit plan. "
            "Only output strict JSON with keys: edits, self_check. Edits entries have: file, original_snippet, replacement_snippet. "
            "Respect constraints: minimal edits, strict_single_match, atomic intent, and repository allowlist."
        )
        instruction: Dict[str, Any] = {
            "task": task,
            "constraints": {
                "minimal_edits": constraints.minimal_edits,
                "strict_single_match": constraints.strict_single_match,
                "atomic": constraints.atomic,
                "allowlist": constraints.allowlist,
                "max_edits": constraints.max_edits,
                "max_snippet_chars": constraints.max_snippet_chars,
            },
            "context_files": files_for_prompt,
            "apis": apis[:20],
            "tests": tests[:20],
            "success_criteria": success_criteria,
        }
        user = (
            "Task:\n" + task + "\n\n"
            + "Context files (paths only):\n" + "\n".join(files_for_prompt) + "\n\n"
            + "Constraints:\n" + json.dumps(instruction["constraints"], indent=2)
            + "\n\nOutput JSON exactly in this schema:\n"
            + json.dumps({
                "edits": [
                    {
                        "file": "path/to/file.py",
                        "original_snippet": "old text",
                        "replacement_snippet": "new text",
                    }
                ],
                "self_check": {"touched_files": ["path/to/file.py"], "notes": "..."},
            }, indent=2)
        )

        prompt_digest = _digest(user)

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

        # Call model
        try:
            completion = await chat_completion(messages)
        except Exception as e:
            return {"status": "error", "message": f"codegen call failed: {e}"}

        content: str = ""
        try:
            content = (completion.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
        except Exception:
            content = ""
        data = _extract_json_block(content) or {}
        edits = [
            {
                "file": str(it.get("file", "")).strip(),
                "original_snippet": str(it.get("original_snippet", ""))[: constraints.max_snippet_chars],
                "replacement_snippet": str(it.get("replacement_snippet", ""))[: constraints.max_snippet_chars],
            }
            for it in (data.get("edits") or [])
            if isinstance(it, dict)
        ]

        # Enforce constraints locally
        errors: List[str] = []
        validated: List[Dict[str, str]] = []
        seen_files: List[str] = []
        for e in edits[: constraints.max_edits]:
            f = e.get("file", "")
            if not f:
                continue
            p = Path(f)
            if not _is_allowed(p, constraints.allowlist):
                errors.append(f"file not allowed: {f}")
                continue
            if not p.exists():
                errors.append(f"missing file: {f}")
                continue
            if len(e.get("original_snippet", "")) == 0 or len(e.get("replacement_snippet", "")) == 0:
                errors.append(f"empty snippet for: {f}")
                continue
            validated.append({
                "file": f,
                "original_snippet": e["original_snippet"],
                "replacement_snippet": e["replacement_snippet"],
            })
            seen_files.append(f)

        result_obj = {
            "edits": validated,
            "self_check": {
                "touched_files": seen_files,
                "notes": (data.get("self_check", {}) or {}).get("notes", ""),
            },
            "prompt_digest": prompt_digest,
            "model": completion.get("model"),
            "usage": completion.get("usage"),
        }

        # Write to .cerebraflow/edits.json
        out_dir = Path(".cerebraflow")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "edits.json"
        out_path.write_text(json.dumps(result_obj, indent=2))

        status = "success" if validated else "error"
        message = None if validated else ("no valid edits produced" if not errors else "; ".join(errors[:5]))
        return {
            "status": status,
            "message": message,
            "count": len(validated),
            "prompt_digest": prompt_digest,
            "output_file": str(out_path),
            "errors": errors,
        }

