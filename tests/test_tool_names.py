#!/usr/bin/env python3
"""Guard MCP tool names so Grok and the MCP spec will accept them."""

import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from server.mcp_server import AutoCADMCPServer, _canonical_tool_name

TOOL_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def test_advertised_tool_names_are_spec_safe():
    tools = AutoCADMCPServer()._tool_definitions()
    names = [tool.name for tool in tools]
    assert names, "server must advertise at least one tool"
    for name in names:
        assert TOOL_NAME_RE.fullmatch(name), f"invalid MCP tool name: {name!r}"
        assert "." not in name


def test_dotted_aliases_still_dispatch():
    assert _canonical_tool_name("docs.search") == "docs_search"
    assert _canonical_tool_name("docs_search") == "docs_search"


if __name__ == "__main__":
    test_advertised_tool_names_are_spec_safe()
    test_dotted_aliases_still_dispatch()
    print("tool name checks passed")
