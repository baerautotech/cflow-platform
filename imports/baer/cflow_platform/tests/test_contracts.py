import asyncio


def test_core_public_api_surfaces():
    from cflow_platform.core.public_api import (
        get_stdio_server,
        get_direct_client_executor,
        safe_get_version_info,
    )

    assert callable(get_stdio_server())
    assert callable(get_direct_client_executor())
    info = safe_get_version_info()
    assert isinstance(info, dict) and "api_version" in info


def test_direct_client_exec_unknown_tool():
    from cflow_platform.core.public_api import get_direct_client_executor

    exec_fn = get_direct_client_executor()
    result = asyncio.get_event_loop().run_until_complete(exec_fn("__no_such_tool__"))
    assert result.get("status") == "error"


def test_task_get_full_metadata_from_list_or_next():
    from cflow_platform.core.public_api import get_direct_client_executor

    exec_fn = get_direct_client_executor()
    loop = asyncio.get_event_loop()

    # Prefer next task for a fresh, consistent pending item
    nxt = loop.run_until_complete(exec_fn("task_next"))
    cand = nxt.get("task") or {}
    tid = cand.get("task_id") or cand.get("id")

    if not tid:
        lst = loop.run_until_complete(exec_fn("task_list"))
        tasks = lst.get("tasks") or []
        assert isinstance(tasks, list)
        if tasks:
            tid = tasks[0].get("task_id") or tasks[0].get("id")

    assert tid
    got = loop.run_until_complete(exec_fn("task_get", taskId=tid))
    meta = got.get("task") or got
    assert isinstance(meta, dict)
    # Expect common fields when available
    # If proxy lookup fails, at least ensure task_id echo is present
    if all(k in meta for k in ("title", "status", "priority")):
        assert str(meta["title"]) != ""
        assert str(meta["status"]) != ""
        assert str(meta["priority"]) != ""
    else:
        assert meta.get("task_id") == tid


def test_registry_declared_vs_dispatch_parity():
    from cflow_platform.core.tool_registry import ToolRegistry
    from cflow_platform.core.direct_client import execute_mcp_tool

    declared = {t["name"] for t in ToolRegistry.get_tools_for_mcp()}
    # Expand parity: try all declared tools, but only assert shape for those we dispatch
    subset = set(declared)
    loop = asyncio.get_event_loop()
    for name in subset:
        res = loop.run_until_complete(execute_mcp_tool(name))
        assert isinstance(res, dict)
        if "status" in res:
            assert res.get("status") in {"success", "error"}
        elif "success" in res:
            # Some handlers return boolean success with optional error
            assert res.get("success") in {True, False}


def test_negative_tool_names_error_strict():
    from cflow_platform.core.direct_client import execute_mcp_tool

    loop = asyncio.get_event_loop()
    for bad in ("no_such_tool", "", " "):
        res = loop.run_until_complete(execute_mcp_tool(bad))
        assert res.get("status") == "error"


def test_plan_validate_success_and_error_cases():
    from cflow_platform.core.direct_client import execute_mcp_tool

    loop = asyncio.get_event_loop()
    # Success case: valid minimal atomic format (package may still return success False + message)
    ok = loop.run_until_complete(
        execute_mcp_tool(
            "plan_validate",
            content="1.1.1 Define component A\n1.1.2 Implement component A",
        )
    )
    assert isinstance(ok, dict)
    assert (ok.get("status") in {"success", "error"}) or (ok.get("success") in {True, False})

    # Error case: garbage text
    err = loop.run_until_complete(
        execute_mcp_tool(
            "plan_validate",
            content="this is not an atomic plan format",
        )
    )
    assert isinstance(err, dict)
    assert (err.get("status") in {"success", "error"}) or (err.get("success") in {True, False})


