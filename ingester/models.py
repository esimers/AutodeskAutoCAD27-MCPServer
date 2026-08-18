import re
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

SOURCE_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def normalize_source(name: str) -> str:
    """Validate a source id (the data/chm/<name> folder name)."""
    source = (name or "").strip()
    if not source or not SOURCE_NAME_RE.fullmatch(source):
        raise ValueError(
            f"Invalid source '{name}'. Use the extract folder name "
            f"(letters, numbers, dot, underscore, hyphen), e.g. arxmgd or inventor."
        )
    return source


def discover_extracted_sources(root: Optional[Path] = None) -> List[str]:
    """CHM extract folders under data/chm/."""
    chm_root = (root or project_root()) / "data" / "chm"
    if not chm_root.is_dir():
        return []
    return sorted(
        p.name for p in chm_root.iterdir()
        if p.is_dir() and SOURCE_NAME_RE.fullmatch(p.name)
    )


def discover_indexed_sources(root: Optional[Path] = None) -> List[str]:
    """Sources that already have FAISS + BM25 indexes."""
    index_root = (root or project_root()) / "data" / "index"
    if not index_root.is_dir():
        return []
    found = []
    for path in index_root.iterdir():
        if (
            path.is_dir()
            and SOURCE_NAME_RE.fullmatch(path.name)
            and (path / "faiss.index").exists()
            and (path / "bm25.pkl").exists()
        ):
            found.append(path.name)
    return sorted(found)


def default_source(root: Optional[Path] = None) -> str:
    indexed = discover_indexed_sources(root)
    extracted = discover_extracted_sources(root)
    for candidate in ("arxmgd",):
        if candidate in indexed or candidate in extracted:
            return candidate
    if indexed:
        return indexed[0]
    if extracted:
        return extracted[0]
    return "arxmgd"


class DocumentChunk(BaseModel):
    """A chunk of documentation with metadata"""
    id: str
    source: str
    page_id: str
    title: str
    path: str
    anchor: Optional[str] = None
    content: str
    html_content: str
    chunk_index: int
    total_chunks: int
    start_offset: int
    end_offset: int
    metadata: Dict[str, Any] = {}


class DocumentPage(BaseModel):
    """A complete documentation page"""
    id: str
    source: str
    title: str
    path: str
    content: str
    html_content: str
    anchors: List[str] = []
    see_also: List[str] = []
    metadata: Dict[str, Any] = {}


class TOCNode(BaseModel):
    """Table of Contents node"""
    title: str
    path: str
    level: int
    children: List['TOCNode'] = []
    page_id: Optional[str] = None


class SearchResult(BaseModel):
    """Search result with ranking information"""
    id: str
    title: str
    path: str
    snippet: str
    score: float
    source: str
    chunk_index: Optional[int] = None


class NeighborInfo(BaseModel):
    """Information about document neighbors"""
    parent: Optional[SearchResult] = None
    children: List[SearchResult] = []
    related: List[SearchResult] = []
