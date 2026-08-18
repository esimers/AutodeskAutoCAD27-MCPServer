#!/usr/bin/env python3
"""
CHM ingestion pipeline for SDK documentation
"""

import sys
from pathlib import Path
from typing import List
import argparse
from tqdm import tqdm

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent))

from ingester.models import (
    default_source,
    discover_extracted_sources,
    normalize_source,
    project_root,
)
from ingester.toc_parser import TOCParser
from ingester.topic_parser import TopicParser
from ingester.link_graph import LinkGraphBuilder
from ingester.chunker import HeadingAwareChunker
from ingester.indexer import HybridIndexer


class CHMIngestionPipeline:
    """Complete pipeline for ingesting CHM files into searchable indices"""
    
    def __init__(self, 
                 source: str = None,
                 embedding_model: str = "all-MiniLM-L6-v2"):
        self.source = normalize_source(source or default_source())
        self.embedding_model = embedding_model
        
        root = project_root()
        self.extraction_root = root / "data" / "chm" / self.source
        self.index_dir = root / "data" / "index" / self.source
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.toc_parser = TOCParser(str(self.extraction_root))
        self.topic_parser = TopicParser(str(self.extraction_root), self.source)
        self.link_builder = LinkGraphBuilder(self.source)
        self.chunker = HeadingAwareChunker()
        self.indexer = HybridIndexer(embedding_model, self.source)
    
    def ingest_source(self) -> int:
        """Ingest the configured CHM source"""
        print(f"\n=== Ingesting {self.source} ===")
        
        if not self.extraction_root.exists():
            print(f"Error: Extraction directory {self.extraction_root} not found.")
            print("Extract the CHM file using 7-zip first:")
            print(f'7z x path\\to\\{self.source}.chm "-o{self.extraction_root}"')
            return 0
        
        print("Parsing TOC...")
        toc_nodes = self.toc_parser.parse_hhc("*.hhc")
        
        print("Parsing topics...")
        pages = self.topic_parser.parse_all_topics()
        print(f"Extracted {len(pages)} pages")
        
        print("Building link graph...")
        self.link_builder.build_graph(toc_nodes, pages)
        self.link_builder.save_graph(self.index_dir / "graph.json")
        
        print("Chunking pages...")
        all_chunks = []
        for page in tqdm(pages, desc="Chunking"):
            chunks = self.chunker.chunk_page(page)
            for chunk in chunks:
                chunk.total_chunks = len(chunks)
            all_chunks.extend(chunks)
        
        print(f"Created {len(all_chunks)} chunks")
        
        print("Building search index...")
        anchor_map = self.chunker.get_anchor_map()
        self.indexer.build_index(all_chunks, anchor_map)
        
        return len(all_chunks)


def main():
    """Main entry point for the ingestion pipeline"""
    parser = argparse.ArgumentParser(description="Ingest SDK CHM documentation")
    parser.add_argument(
        "--source",
        help="Source id = folder name under data/chm/ (e.g. arxmgd, inventor)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Ingest every extracted folder under data/chm/",
    )
    parser.add_argument("--embedding-model", default="all-MiniLM-L6-v2",
                       help="Sentence transformer model for embeddings")
    parser.add_argument("--list-sources", action="store_true", 
                       help="List extracted CHM folders and exit")
    
    args = parser.parse_args()
    
    if args.list_sources:
        available = discover_extracted_sources()
        print("Extracted CHM sources (data/chm/<name>):")
        if not available:
            print("  (none)")
        for source in available:
            print(f"  - {source}")
        return
    
    if args.all:
        sources = discover_extracted_sources()
        if not sources:
            print("No extracted CHM folders found under data/chm/")
            return
    elif args.source:
        sources = [normalize_source(args.source)]
    else:
        sources = [default_source()]
    
    for source in sources:
        pipeline = CHMIngestionPipeline(
            source=source,
            embedding_model=args.embedding_model
        )
        chunk_count = pipeline.ingest_source()
        print(f"\n=== Ingestion Complete ===")
        print(f"{source}: {chunk_count} chunks indexed")


if __name__ == "__main__":
    main()
