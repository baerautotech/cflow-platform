from __future__ import annotations

from cflow_platform.core.failure_parser import parse_pytest_failures


def test_parse_pytest_failures_from_sample_output() -> None:
    sample = (
        "============================= test session starts ==============================\n"
        "collected 1 item\n\n"
        "=================================== FAILURES ===================================\n"
        "___________________________ test_something_fails _____________________________\n"
        "\n"
        "test_example.py:3: in test_something_fails\n"
        "    assert 1 == 2\n"
        "E   AssertionError: assert 1 == 2\n"
        "\n"
        "=========================== short test summary info ===========================\n"
        "FAILED test_example.py::test_something_fails - AssertionError: assert 1 == 2\n"
        "============================== 1 failed in 0.01s =============================\n"
    )
    result = parse_pytest_failures(sample)
    assert isinstance(result, dict)
    assert "summary_line" in result
    assert "failures" in result and isinstance(result["failures"], list)
    assert result["failures"], "expected at least one failure entry"
    first = result["failures"][0]
    assert first.get("file_path") == "test_example.py"
    assert first.get("node_id") == "test_something_fails"
    assert "AssertionError" in (first.get("error_type") or "AssertionError")
    assert isinstance(first.get("top_trace"), list)


