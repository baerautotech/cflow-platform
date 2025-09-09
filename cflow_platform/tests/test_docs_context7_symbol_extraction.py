from __future__ import annotations

from cflow_platform.core.docs_context7 import extract_symbols_from_failure_report


def test_extract_symbols_basic_patterns():
    report = {
        "failures": [
            {
                "error_type": "AttributeError: module 'numpy' has no attribute 'arrayz'",
                "message": "ImportError: cannot import name 'DataFrame' from 'pandas'",
                "top_trace": [
                    "ModuleNotFoundError: No module named 'scipy.optimize'",
                    "TypeError: my_func(1, 2)",
                    "NameError: name 'missing' is not defined",
                ],
            }
        ]
    }
    syms = extract_symbols_from_failure_report(report, max_symbols=10)
    # Expect representative symbols
    assert any(s.startswith("numpy.") for s in syms)
    assert any(s.startswith("pandas.") for s in syms)
    assert any("scipy" in s for s in syms)
    assert "my_func" in syms
    assert "missing" in syms


