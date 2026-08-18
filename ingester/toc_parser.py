"""
TOC and Index parser for CHM files
"""

import os
import re
from typing import List, Dict, Optional
from pathlib import Path
from bs4 import BeautifulSoup


class TOCTreeNode:
    """TOC tree node"""
    def __init__(self, title: str, path: str, children: List['TOCTreeNode'] = None):
        self.title = title
        self.path = path
        self.children = children or []


class TOCParser:
    """Parser for CHM TOC (HHC) and Index (HHK) files"""
    
    def __init__(self, extraction_root: str):
        self.extraction_root = Path(extraction_root)
    
    def parse_hhc(self, hhc_path: str) -> List[TOCTreeNode]:
        """Parse HHC file and return TOC tree.

        ``hhc_path`` may be a filename or a glob (e.g. ``*.hhc``). CHM
        extracts use different names (``toc.hhc``, ``arxmgd.hhc``, ...).
        """
        if '*' in hhc_path:
            matches = list(self.extraction_root.glob(hhc_path))
            if not matches:
                matches = list(self.extraction_root.rglob(hhc_path))
            if not matches:
                print(f"No HHC files matching {hhc_path} in {self.extraction_root}")
                return []
            hhc_file = max(matches, key=lambda p: p.stat().st_size)
            print(f"Using TOC file: {hhc_file.name}")
        else:
            hhc_file = self.extraction_root / hhc_path
            if not hhc_file.exists():
                return []
        
        with open(hhc_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'lxml')
        root_nodes = []

        # Only walk top-level <LI> entries; children are parsed recursively.
        # find_all('li') would flatten the tree and duplicate every node.
        root_ul = soup.find('ul')
        li_elements = root_ul.find_all('li', recursive=False) if root_ul else []
        
        for li in li_elements:
            node = self._parse_toc_li(li)
            if node:
                root_nodes.append(node)
        
        return root_nodes
    
    def _parse_toc_li(self, li_element) -> Optional[TOCTreeNode]:
        """Parse a single LI element from HHC"""
        # Extract title from text content
        title = li_element.get_text().strip()
        if not title:
            return None
        
        # Extract path from Object tag
        path = ""
        object_tag = li_element.find('object', {'type': 'text/sitemap'})
        if object_tag:
            param_name = object_tag.find('param', {'name': 'Name'})
            param_local = object_tag.find('param', {'name': 'Local'})
            
            if param_name:
                title = param_name.get('value', title)
            if param_local:
                path = param_local.get('value', '')
        
        # Normalize path
        if path:
            path = self._normalize_path(path)
        
        # Parse children
        children = []
        ul = li_element.find('ul')
        if ul:
            child_lis = ul.find_all('li', recursive=False)
            for child_li in child_lis:
                child_node = self._parse_toc_li(child_li)
                if child_node:
                    children.append(child_node)
        
        return TOCTreeNode(title, path, children)
    
    def parse_hhk(self, hhk_path: str) -> Dict[str, List[str]]:
        """Parse HHK file and return index mapping"""
        hhk_file = self.extraction_root / hhk_path
        if not hhk_file.exists():
            return {}
        
        with open(hhk_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'lxml')
        index_map = {}
        
        # Find all <LI> elements (index entries)
        li_elements = soup.find_all('li')
        
        for li in li_elements:
            # Extract term and path
            object_tag = li.find('object', {'type': 'text/sitemap'})
            if object_tag:
                param_name = object_tag.find('param', {'name': 'Name'})
                param_local = object_tag.find('param', {'name': 'Local'})
                
                if param_name and param_local:
                    term = param_name.get('value', '').strip()
                    path = param_local.get('value', '').strip()
                    
                    if term and path:
                        path = self._normalize_path(path)
                        if term not in index_map:
                            index_map[term] = []
                        index_map[term].append(path)
        
        return index_map
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path separators and resolve relative paths"""
        # Normalize slashes
        path = path.replace('\\', '/')
        
        # Remove leading slash if present
        if path.startswith('/'):
            path = path[1:]
        
        # Resolve against extraction root
        full_path = self.extraction_root / path
        
        # Return relative path from extraction root
        try:
            return str(full_path.relative_to(self.extraction_root))
        except ValueError:
            return path
