# Changelog

## 1.1.0

Grok-compatible AutoCAD documentation MCP server that can be used from any folder.

- Advertise MCP tools as `docs_search`, `docs_get`, `docs_toc`, `docs_neighbors`, `docs_list_sources`, and `docs_health`. Dotted names such as `docs.search` are rejected by Grok (0 tools after a successful handshake).
- Add `scripts/register_grok.py` to write a **user-scope** Grok entry. User-scope servers load in every working directory. The script updates only the local user config; clone paths stay out of git.
- Keep the server id `autocad-sdk` so it can run next to `inventor-sdk`.
- Document setup with placeholders only. Machine paths belong in the gitignored `.grok/config.toml` or the user Grok config.
- Stop tracking machine-specific Cursor sample config and `.DS_Store`.
