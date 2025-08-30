from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import pytest

from cflow_platform import sdk
from cflow_platform.handlers.testing_handlers import _parse_pytest_output


def test_parse_pytest_output_extracts_summary_and_failures() -> None:
    sample = (
        "============================= test session starts ==============================\n"
        "platform darwin -- Python 3.11.13, pytest-8.4.1\n"
        "collected 1 item\n\n"
        "=================================== FAILURES ===================================\n"
        "___________________________ test_something_fails _____________________________\n"
        "Traceback (most recent call last):\n"
        "  File 'test_example.py', line 3, in test_something_fails\n"
        "    assert 1 == 2\n"
        "AssertionError: assert 1 == 2\n\n"
        "=========================== short test summary info ===========================\n"
        "FAILED test_example.py::test_something_fails - AssertionError: assert 1 == 2\n"
        "============================== 1 failed in 0.01s =============================\n"
    )
    summary = _parse_pytest_output(sample)
    assert "failures" in summary
    assert isinstance(summary["failures"], list)
    assert summary["failures"], "expected at least one failure parsed"
    assert "summary_line" in summary
    assert "failed" in summary["summary_line"].lower()


def test_run_pytest_no_tests_path_returns_nonzero() -> None:
    # Create a temporary directory with no tests
    async def _run(tmp: str):
        return await sdk.run_pytest(path=tmp, verbose=True)

    with tempfile.TemporaryDirectory() as tmp:
        res = asyncio.run(_run(tmp))
        assert res["status"] == "success"
        assert res["exit_code"] != 0
        assert res["passed"] is False
        assert "no tests ran" in (res.get("summary", {}).get("summary_line", "").lower())


def test_run_pytest_with_passing_test_succeeds() -> None:
    # Create a temporary directory and a minimal passing test
    async def _run(p: str):
        return await sdk.run_pytest(path=p, verbose=False)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        test_file = tmp_path / "test_ok.py"
        test_file.write_text(
            "import pytest\n\n"
            "def test_ok():\n"
            "    assert True\n"
        )
        res = asyncio.run(_run(str(tmp_path)))
        assert res["status"] == "success"
        assert res["exit_code"] == 0
        assert res["passed"] is True


