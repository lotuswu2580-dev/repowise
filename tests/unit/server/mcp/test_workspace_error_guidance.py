"""Bad MCP arguments name the correction rather than suggesting a retrieval miss."""

import pytest

from tests.unit.server.test_mcp_workspace import workspace_mcp  # noqa: F401

pytestmark = pytest.mark.usefixtures("workspace_mcp")


async def test_why_all_without_query_names_both_supported_calls():
    from repowise.server.mcp_server import get_why

    result = await get_why(repo="all")
    assert "query" in result["error"]
    assert "repo alias" in result["error"]
    assert "backend" in result["error"] and "frontend" in result["error"]
    searched = await get_why(query="React", repo="all")
    assert "error" not in searched


@pytest.mark.parametrize("include", [None, ["evidence"]])
async def test_answer_all_error_is_not_a_retrieval_miss(include):
    from repowise.server.mcp_server import get_answer

    result = await get_answer("how does routing work", repo="all", include=include)
    assert "get_answer" in result["error"]
    assert "backend" in result["error"]
    assert "answer" not in result
    assert "next_action_hint" not in result


@pytest.mark.parametrize("tool", ["get_risk", "get_context", "get_health"])
async def test_unknown_target_alias_is_named_with_valid_aliases(tool):
    import repowise.server.mcp_server as mcp

    target = "zzz:foo.py"
    result = await getattr(mcp, tool)(targets=[target])
    cards = result.get("targets")
    card = cards.get(target) if isinstance(cards, dict) else None
    if card is None:
        card = next(row for row in result["unresolved"] if row["target"] == target)
    assert "zzz" in card["hint"]
    assert "backend" in card["hint"] and "frontend" in card["hint"]
    assert "Unknown" in card["hint"]


@pytest.mark.parametrize("finding_id", ["fix1_x", "act_x", "plain_missing_finding"])
async def test_finding_miss_only_redirects_fix_and_action_ids(finding_id):
    from repowise.server.mcp_server import get_health

    result = await get_health(finding_id=finding_id, repo="backend")
    assert result["finding"] is None and result["resolved"] is False
    if finding_id.startswith(("fix", "act_")):
        assert "fix_id" in result["next_action"]
    else:
        assert "next_action" not in result


async def test_unknown_symbol_alias_gets_the_same_correction():
    from repowise.server.mcp_server import get_symbol

    result = await get_symbol("zzz:foo.py::missing")
    assert "zzz" in result["hint"]
    assert "backend" in result["hint"] and "frontend" in result["hint"]


@pytest.mark.parametrize("target", [
    "missing.py", "missing.py:1-2", "src/missing.py::missing",
    "backend:missing.py", "BACKEND:missing.py", "module:missing",
    "C:/missing.py", r"C:\missing.py", "/missing.py",
])
async def test_path_and_symbol_syntax_does_not_become_an_unknown_alias(target):
    from repowise.server.mcp_server import get_context

    result = await get_context(targets=[target])
    assert "Unknown workspace repo alias" not in str(result)
    if target == "missing.py":
        assert 'search_codebase(query=..., repo="all")' in result["targets"][target]["hint"]
