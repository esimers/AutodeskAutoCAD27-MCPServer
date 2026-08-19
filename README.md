# AutoCAD Documentation MCP Server

An MCP (Model Context Protocol) server that exposes Autodesk AutoCAD SDK documentation taken from CHM files distributed together with the official Autodesk Autocad SDK documenation, enabling AI agents to query and retrieve structured documentation content.

## Architecture

```
CHM Files → 7-zip → HTML → Parser → Chunker → Indexer → MCP Server → AI Agent
    ↓         ↓       ↓        ↓        ↓         ↓          ↓
  arxmgd.chm  Extract  Topics  Chunks  FAISS+BM25  Tools   AI Agent
```

### Components

- **TOC Parser**: Parses HHC/HHK files for table of contents and index
- **Topic Parser**: Extracts HTML content using BeautifulSoup
- **Link Graph Builder**: Builds parent/children/see_also relationships
- **Heading-Aware Chunker**: Splits content while preserving document structure
- **Hybrid Indexer**: Builds FAISS vector index and BM25 lexical index
- **MCP Server**: Exposes search tools via Model Context Protocol

## Grok: use from any folder

Register the server in the **user** Grok config (`~/.grok/config.toml`). That is what makes it available in every working directory.

```powershell
py -3.12 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements-runtime.txt
.\venv\Scripts\python.exe scripts\register_grok.py
```

Start a new Grok session (or refresh `/mcps`). You should see `autocad-sdk` tools:

- `autocad-sdk__docs_search`
- `autocad-sdk__docs_get`
- `autocad-sdk__docs_toc`
- `autocad-sdk__docs_neighbors`
- `autocad-sdk__docs_list_sources`
- `autocad-sdk__docs_health`

Tool names use underscores. Dots (`docs.search`) are rejected by Grok and by the MCP spec.

The register script writes this machine's clone path only into the local user config. That file is not part of the repository.

To diagnose:

```powershell
grok mcp list
grok mcp doctor autocad-sdk
```

## New machine (clone + existing indexes)

`data/` is not in git. Copy that folder from a machine that already ingested the 2027 CHMs, then:

```powershell
git clone <repository-url>
cd AutodeskAutoCAD27-MCPServer
py -3.12 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements-runtime.txt
.\venv\Scripts\python.exe scripts\register_grok.py
```

You need **both** `data/index/` (search indexes) and `data/chm/` (extracted HTML). Skip `venv/` when copying — recreate it as above. First search downloads the MiniLM embedding model into that user's Hugging Face cache.

Optional project-only setup (this folder only): copy `.grok/config.toml.example` to `.grok/config.toml` and replace `ROOT` with this clone's absolute path. Prefer the register script for any-folder use.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd <repo-folder>
   ```

2. **Install dependencies**:
   ```bash
   # For ingestion (heavy dependencies)   
   pip install -r requirements-ingestion.txt # (sorry it is dirty)
   
   # OR for runtime only (lightweight)
   pip install -r requirements-runtime.txt
   ```

3. **Extract CHM files** using 7-zip. The folder name under `data/chm/` **is** the source id (any SDK, not just AutoCAD):
   ```bash
   7z x path\to\arxmgd.chm -odata/chm/arxmgd/
   7z x path\to\inventor.chm -odata/chm/inventor/
   ```

## Usage

### 1. Ingest CHM Documentation

**First, install ingestion dependencies:**
```bash
pip install -r requirements-ingestion.txt
```

**Then build search indices:**
```bash
# List extracted folders under data/chm/
python -m ingester.ingest --list-sources

# Ingest one source (folder name)
python -m ingester.ingest --source inventor

# Ingest every extracted folder
python -m ingester.ingest --all
```

Each source is just a directory name: `data/chm/<name>/` → `data/index/<name>/`. Use that same `<name>` in Grok config (`--source inventor`) and in `docs.search` / `docs.get`. Keep different products in separate extract folders. Do not mix two SDKs into one folder.

### 2. Run the MCP Server

**Install lightweight runtime dependencies:**
```bash
pip install -r requirements-runtime.txt
```

**Start the server:**
```bash
# Run with default source (arxmgd)
python -m server.mcp_server

# Run with specific source
python -m server.mcp_server --source arxdev
```

## Example Queries

Here are example queries that AI agents can use:

- **"What class represents a revision cloud?"**
- **"What are the ways to construct AcDbArc?"**
- **"What methods are available on AcDbBlockReference?"**
- **"How does AcDbDimension store information about text size?"**

## MCP Tools

The server exposes the following tools:

Grok names them `autocad-sdk__<tool>`. The server advertises:

### `docs_search`
Search documentation using hybrid semantic and lexical search.

**Parameters**:
- `query` (required): Search query
- `k` (optional): Number of results (default: 10)
- `source` (optional): CHM source to search (arxmgd, arxdev, etc.)

**Example**:
```json
{
  "query": "revision cloud",
  "k": 5,
  "source": "arxmgd"
}
```

### `docs_get`
Get full content of a documentation topic by ID.

**Parameters**:
- `id` (required): Document chunk ID
- `format` (optional): Content format ("text" or "html", default: "text")
- `source` (optional): CHM source filter

### `docs_toc`
Get table of contents for a CHM source.

**Parameters**:
- `source` (optional): CHM source (default: "arxmgd")

### `docs_neighbors`
Get related documentation (parent, children, see also).

**Parameters**:
- `id` (required): Document chunk ID
- `source` (optional): CHM source filter

### `docs_list_sources`
List available CHM documentation sources.

### `docs_health`
Get server health and version information.

## Project Structure

```
AutodeskAutoCAD27-MCPServer/
├── data/                  # Not in git (CHM extract + indexes)
├── ingester/              # Parse, chunk, and index CHM HTML
├── server/mcp_server.py   # MCP server
├── scripts/register_grok.py
├── tests/
├── requirements-runtime.txt
├── requirements-ingestion.txt
└── README.md
```

## Configuration

### Embedding Model

The default embedding model is `all-MiniLM-L6-v2`. You can change it in the ingestion pipeline:

```bash
python -m ingester.ingest --embedding-model "sentence-transformers/all-mpnet-base-v2"
```

### Chunking Parameters

Default chunking parameters:
- Target tokens: 1000
- Overlap tokens: 200
- Minimum chunk tokens: 200

These can be modified in `ingester/chunker.py`.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
