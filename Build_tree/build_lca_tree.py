#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build a dependency tree for LCA markdown pages.

Features:
- Embedded CONFIG (edit ROOT_ID, REPO_ROOT, etc. below)
- Recursively scans repo for pd_*.md and ps_*.md (case-insensitive)
- Parses Technosphere Flow: Production/Consumption (Product/Process)
- Builds a recursive tree with cycle detection and optional reverse producers
- Exports JSON tree, flat edges, Mermaid, and Graphviz DOT
- Mermaid output is "safe": sanitized IDs/labels + de-HTML (fixes '--&gt;' issues)
- Optional: if Mermaid CLI (mmdc) is available, also export graph.svg automatically

Outputs:
  out/tree.json
  out/edges.json
  out/graph.mmd
  out/graph.dot
  out/inventory.json
  out/log.txt
  (optional) out/graph.svg

Author: M365 Copilot for Vincent Corlay
"""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from build_lca_tree_helper import *

# =============================
#           CONFIG
# =============================

#SCRIPT_DIR = Path(__file__).resolve().parent
WORKING_DIR = Path.cwd()
SCRIPT_DIR = WORKING_DIR / "wiki-on-processes-and-products-for-LCA.wiki"
File_name_no_ext = "pd_resistance_production"

CONFIG = {
    "ROOT_ID": "product/" + File_name_no_ext + ".md",  
    # Repo root to scan (defaults to where this script lives)
    "REPO_ROOT": str(SCRIPT_DIR),

    # Include processes that produce a product (reverse lookup from product to processes)
    "INCLUDE_REVERSE_PRODUCERS": False,
    # "SHOW_LISTED_PRODUCED_BY_EDGES": False,  # NEW: hide product→process edges from "List of processes"


    # Limit recursion depth (None for unlimited)
    "MAX_DEPTH": 10,

    # Output directory
    "OUTPUT_DIR": str(SCRIPT_DIR / "out_tree"),

    # Verbose console logging
    "VERBOSE": True,

    # Optional: attempt to export Mermaid SVG using Mermaid CLI (mmdc) if found
    "EXPORT_SVG_WITH_MMDC": True,     # set False to skip
    "MMDC_PATH": None,                # None: auto-detect in PATH; or set explicit path to mmdc
}

# =============================
#        IMPLEMENTATION
# =============================

LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')


def parse_file_links_with_context(path: Path) -> Dict:
    """
    Parse a single markdown file, extracting:
      - title (first '# ...' or 'Process/Product: ...')
      - edges_out with relation inferred from section context
    """
    text = safe_read_text(path)
    node_id = path.stem
    node_type = infer_node_type_from_id(node_id)

    title = None
    for line in text.splitlines():
        if line.startswith('# '):
            title = line[2:].strip()
            break
        if re.match(r'^\s*#+\s+(Process|Product)\s*:', line, flags=re.IGNORECASE):
            title = re.sub(r'^\s*#+\s*', '', line).strip()
            break
    if not title:
        title = node_id

    edges_out = []
    current_h2 = None
    current_h3 = None
    consumption_subcat = None  # 'product'|'process'|None
    chimaera_mode = False

    lines = text.splitlines()
    for raw_line in lines:
        stripped = raw_line.strip()

        # Headings
        if stripped.startswith('## '):
            current_h2 = stripped[3:].strip().lower()
            current_h3 = None
            consumption_subcat = None
            chimaera_mode = 'chimaera' in current_h2
            continue

        if stripped.startswith('### '):
            current_h3 = stripped[4:].strip().lower()
            consumption_subcat = None
            if current_h3 in ('production', 'consumption'):
                chimaera_mode = False
            continue

        # Inside Consumption, detect Product:/Process: subsections
        if current_h2 and 'technosphere' in current_h2 and current_h3 == 'consumption':
            if re.match(r'^\s*product\s*:', stripped, flags=re.IGNORECASE):
                consumption_subcat = 'product'
                continue
            if re.match(r'^\s*process\s*:', stripped, flags=re.IGNORECASE):
                consumption_subcat = 'process'
                continue

        
        if current_h2 and current_h2.lower() == 'list of processes' == 'list of processes' and node_type == 'product':
            if stripped.startswith(('* ', '- ')) and not LINK_PATTERN.search(stripped):
                label = stripped[2:].strip()

                # Try to extract a valid process ID from the label if present
                m_id = re.search(r'\\b(ps_[a-zA-Z0-9_]+)\\b', label)
                if m_id:
                    pseudo_id = m_id.group(1)
                else:
                    pseudo_id = re.sub(r'[^a-zA-Z0-9_]', '_', label.lower())
                    if not pseudo_id.startswith('ps_'):
                        pseudo_id = 'ps_' + pseudo_id

                edges_out.append({
                    'source': node_id,
                    'target': pseudo_id,
                    'source_path': str(path),
                    'source_type': node_type,
                    'target_type': 'process',
                    'rel': 'produced_by',
                    'quantity': None,
                    'unit': None,
                    'database': None,
                    'raw_line': stripped
                })


        if stripped.startswith(('* ', '- ')):
            m = LINK_PATTERN.search(stripped)
            if not m:
                continue
            target_raw = m.group(2).strip()
            target_id = normalize_id_from_target(target_raw)
            if not target_id:
                continue

            # Context → relation
            #rel = 'references'
            rel = 'produced_by' if current_h2 == 'list of processes' and node_type == 'product' else 'references'

            if current_h2 and 'technosphere' in current_h2:
                if current_h3 == 'production':
                    rel = 'produces'  # process -> product
                elif current_h3 == 'consumption':
                    if consumption_subcat == 'product':
                        rel = 'consumes_product'  # process -> product
                    elif consumption_subcat == 'process':
                        rel = 'consumes_process'  # process -> process
                    else:
                        rel = 'consumes'
            elif chimaera_mode:
                rel = 'references'

            trailing = stripped[m.end():]
            qval, qunit, db = parse_quantity_unit(trailing)

            edges_out.append({
                'source': node_id,
                'target': target_id,
                'source_path': str(path),
                'source_type': node_type,
                'target_type': infer_node_type_from_id(target_id),
                'rel': rel,
                'quantity': qval,
                'unit': qunit,
                'database': db,
                'raw_line': stripped
            })

    return {
        'id': node_id,
        'type': node_type,
        'path': str(path),
        'title': title,
        'edges_out': edges_out
    }

def scan_repository(repo_root: Path) -> Dict[str, Dict]:
    """
    Recursively scan repo_root for pd_*.md and ps_*.md (case-insensitive).
    Returns index mapping id -> parsed node info (with edges_out; edges_in filled later).
    """
    index: Dict[str, Dict] = {}
    all_md = [p for p in repo_root.rglob("*") if p.is_file() and p.suffix.lower() == ".md"]

    # Accept stems starting with 'pd_' or 'ps_' (lowercased check)
    candidates = [p for p in all_md if p.stem.lower().startswith(("pd_", "ps_"))]

    for md in candidates:
        nid = md.stem
        if nid in index:
            # If duplicates exist in different folders, we keep first occurrence.
            continue
        info = parse_file_links_with_context(md)
        index[info['id']] = info

    # Fill edges_in
    for node in index.values():
        node['edges_in'] = []
    for node in index.values():
        for e in node.get('edges_out', []):
            tgt = e['target']
            if tgt in index:
                index[tgt]['edges_in'].append(e)

    return index

# def build_tree(root_id: str,
#                index: Dict[str, Dict],
#                include_reverse_producers: bool = True,
#                max_depth: Optional[int] = None,
#                _path_stack: Optional[List[str]] = None) -> Dict:
#     """
#     Recursively build a nested tree from root_id.
#     - include_reverse_producers: if True and node is product, add processes that produce it as children (rel 'produced_by')
#     - max_depth: cap depth (root depth = 0)
#     """
#     if _path_stack is None:
#         _path_stack = []

#     node_info = index.get(root_id, {
#         'id': root_id,
#         'type': infer_node_type_from_id(root_id),
#         'path': None,
#         'title': root_id,
#         'edges_out': [],
#         'edges_in': []
#     })

#     node = {
#         'id': node_info['id'],
#         'type': node_info['type'],
#         'title': node_info['title'],
#         'path': node_info['path'],
#         'children': []
#     }

#     # Cycle prevention
#     if root_id in _path_stack:
#         node['cycle'] = True
#         return node

#     # Depth limit
#     if max_depth is not None and len(_path_stack) >= max_depth:
#         node['truncated'] = True
#         return node

#     neighbors = []
#     ##Neighbor seciton
#     # # Forward edges
#     # for e in node_info.get('edges_out', []):
#     #     neighbors.append((e, 'forward'))

#     # Collect forward edges, but drop duplicate produced_by if a produces edge exists
#     produces_pairs = {(e['source'], e['target'])
#                       for e in node_info.get('edges_in', [])
#                       if e.get('rel') == 'produces'}

#     for e in node_info.get('edges_out', []):
#         # Skip product->process produced_by if process->product produces exists
#         if e.get('rel') == 'produced_by' and (e['target'], e['source']) in produces_pairs:
#             continue
#         neighbors.append((e, 'forward'))

#     ####

#     # Reverse producers (still optional)
#     if include_reverse_producers and node_info['type'] == 'product':
#         for e in node_info.get('edges_in', []):
#             if e.get('rel') == 'produces':
#                 e_copy = dict(e)
#                 e_copy['rel'] = 'produced_by'
#                 neighbors.append((e_copy, 'reverse'))
    


#     # Reverse producers for product nodes
#     if include_reverse_producers and node_info['type'] == 'product':
#         for e in node_info.get('edges_in', []):
#             if e.get('rel') == 'produces':
#                 e_copy = dict(e)
#                 e_copy['rel'] = 'produced_by'
#                 neighbors.append((e_copy, 'reverse'))

#     # Deduplicate by (child_id, rel)
#     seen = set()
#     unique_neighbors = []
#     for e, lab in neighbors:
#         child_id = e['target'] if lab == 'forward' else e['source']
#         key = (child_id, e['rel'])
#         if key not in seen:
#             seen.add(key)
#             unique_neighbors.append((e, lab))

#     # Recurse
#     for e, lab in unique_neighbors:
#         child_id = e['target'] if lab == 'forward' else e['source']
#         child = build_tree(child_id, index, include_reverse_producers, max_depth,
#                            _path_stack=_path_stack + [root_id])

#         node['children'].append({
#             'rel': e['rel'],
#             'source': e['source'],
#             'target': e['target'],
#             'quantity': e.get('quantity'),
#             'unit': e.get('unit'),
#             'database': e.get('database'),
#             'child': child
#         })

#     return node

def build_tree(root_id: str,
               index: Dict[str, Dict],
               include_reverse_producers: bool = True,
               max_depth: Optional[int] = None,
               _path_stack: Optional[List[str]] = None) -> Dict:
    """
    Recursively build a nested tree from root_id.
    Deduplicates product-process pairs: keeps only one edge (prefers 'produces').
    """
    if _path_stack is None:
        _path_stack = []

    node_info = index.get(root_id, {
        'id': root_id,
        'type': infer_node_type_from_id(root_id),
        'path': None,
        'title': root_id,
        'edges_out': [],
        'edges_in': []
    })

    node = {
        'id': node_info['id'],
        'type': node_info['type'],
        'title': node_info['title'],
        'path': node_info['path'],
        'children': []
    }

    # Prevent infinite cycles
    if root_id in _path_stack:
        node['cycle'] = True
        return node

    # Depth limit
    if max_depth is not None and len(_path_stack) >= max_depth:
        node['truncated'] = True
        return node

    neighbors = []

    # Collect forward edges
    for e in node_info.get('edges_out', []):
        neighbors.append((e, 'forward'))

    # Add reverse producers (for products)
    if include_reverse_producers and node_info['type'] == 'product':
        for e in node_info.get('edges_in', []):
            if e.get('rel') == 'produces':
                e_copy = dict(e)
                e_copy['rel'] = 'produced_by'
                neighbors.append((e_copy, 'reverse'))

    # ---- Deduplicate product-process pairs ----
    seen_pairs = set()
    unique_neighbors = []
    for e, lab in neighbors:
        # Normalize pair direction for deduplication
        if e['rel'] in ('produces', 'produced_by'):
            # Identify product & process regardless of edge direction
            product = e['source'] if e['source_type'] == 'product' else e['target']
            process = e['source'] if e['source_type'] == 'process' else e['target']
            key = (product, process)

            if key in seen_pairs:
                # Already added a produces/produced_by for this pair -> skip
                continue
            seen_pairs.add(key)

            # Prefer to keep produces if available
            if e['rel'] == 'produced_by':
                # Check if a produces edge exists in neighbors for the same pair
                produces_exists = any(
                    ((ne['source'] if ne['source_type'] == 'product' else ne['target']) == product and
                     (ne['source'] if ne['source_type'] == 'process' else ne['target']) == process and
                     ne['rel'] == 'produces')
                    for ne, _ in neighbors
                )
                if produces_exists:
                    continue  # skip produced_by if produces exists

        unique_neighbors.append((e, lab))

    # Recurse
    for e, lab in unique_neighbors:
        child_id = e['target'] if lab == 'forward' else e['source']
        child = build_tree(child_id, index, include_reverse_producers, max_depth,
                           _path_stack=_path_stack + [root_id])

        node['children'].append({
            'rel': e['rel'],
            'source': e['source'],
            'target': e['target'],
            'quantity': e.get('quantity'),
            'unit': e.get('unit'),
            'database': e.get('database'),
            'child': child
        })

    return node



def collect_reachable_edges(tree: Dict, edges: Optional[List[Dict]] = None) -> List[Dict]:
    if edges is None:
        edges = []
    for ch in tree.get('children', []):
        edges.append({
            'rel': ch['rel'],
            'source': ch['source'],
            'target': ch['target'],
            'quantity': ch.get('quantity'),
            'unit': ch.get('unit'),
            'database': ch.get('database')
        })
        collect_reachable_edges(ch['child'], edges)
    return edges

def to_mermaid(tree: Dict, index: Dict[str, Dict]) -> str:
    """
    Produce a Mermaid flowchart with safe IDs and labels.
    Edge labels use 'rel\\nqty unit' format (no parentheses).
    """    
    lines = []
    # Remove "Product: " or "Process: " (and variants with -, —, –) from titles for display
    def strip_type_prefix(s: str) -> str:
        return re.sub(r'^\s*(product|process)\s*[:\-—–]\s*', '', s, flags=re.I).strip()

    # Avoid HTML label quirks in some renderers
    lines.append("%%{init: {'flowchart': {'htmlLabels': false}} }%%")
    lines.append("graph TD")
    lines += [
        "  classDef product fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20,stroke-width:1px;",
        "  classDef process fill:#e3f2fd,stroke:#1565c0,color:#0d47a1,stroke-width:1px;",
        "  classDef unknown fill:#fff3e0,stroke:#ef6c00,color:#e65100,stroke-width:1px;",        
        "  classDef multi_producer_product fill:#ffebee,stroke:#c62828,color:#b71c1c,stroke-width:2px;"
    ]

    seen_nodes = set()
    seen_edges = set()
    node_classes = {}

    def add_node(node_id: str):
        if node_id in seen_nodes:
            return
        info = index.get(node_id, {'id': node_id, 'type': infer_node_type_from_id(node_id), 'title': node_id})
        # label = f"{info['title']}\\n({info['type']})"
        
        max_label_length = 30  # or whatever length you prefer
        title = strip_type_prefix(info['title'])
        if len(title) > max_label_length:
            title = title[:max_label_length - 3] + "..."
        label = f"{title}\n({info['type']})"

        nid = sanitize_mermaid_id(node_id)
        safe_label = esc_quotes(label)
        lines.append(f'  {nid}["{safe_label}"]')
        #node_classes[nid] = info['type'] if info['type'] in ('product', 'process') else 'unknown'

        # Detect multi-producer products:
        if info['type'] == 'product':
            produces_in = [e for e in index.get(node_id, {}).get('edges_in', []) if e.get('rel') == 'produces']
            print(f"{node_id} has {len(produces_in)} produces edges: {[e['source'] for e in produces_in]}")
            if len(produces_in) > 1: # more than one process produces this product WARINING the list of processes in a product may be incomplete
                node_classes[nid] = 'multi_producer_product'
            else:
                node_classes[nid] = 'product'
        elif info['type'] == 'process':
            node_classes[nid] = 'process'
        else:
            node_classes[nid] = 'unknown'

        seen_nodes.add(node_id)

    def edge_label(ch: Dict) -> str:
        rel = sanitize_mermaid_label(ch.get('rel', ''))
        q = ch.get('quantity')
        u = ch.get('unit') or ''
        if q is None:
            return rel
        qpart = sanitize_mermaid_label(f"{q} {u}".strip())
        return f"{rel}\\n{qpart}" if qpart else rel

    def walk(n: Dict):
        add_node(n['id'])
        for ch in n.get('children', []):
            #  Skip edges with rel == "produced_by"
            src = sanitize_mermaid_id(ch['source'])
            tgt = sanitize_mermaid_id(ch['target'])
            add_node(ch['source'])
            add_node(ch['target'])
            # if ch.get('rel') != "produces":  # ✅ draw edge only if not produced_by
            eid = (src, tgt, ch['rel'])
            if eid not in seen_edges:
                lbl = esc_quotes(edge_label(ch))
                lines.append(f'  {src} -->|{lbl}| {tgt}')
                seen_edges.add(eid)

            walk(ch['child'])

    walk(tree)
    for nid, cls in node_classes.items():
        lines.append(f"  class {nid} {cls};")
    return "\n".join(lines)


def main():
    repo_root = Path(CONFIG["REPO_ROOT"]).resolve()
    out_dir = Path(CONFIG["OUTPUT_DIR"]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    log(f"[INFO] Script dir    : {SCRIPT_DIR}")
    log(f"[INFO] Repo root     : {repo_root}")
    log(f"[INFO] Working dir   : {Path.cwd()}")

    # Scan repository
    index = scan_repository(repo_root)
    products_found = sum(1 for k in index if k.startswith('pd_'))
    processes_found = sum(1 for k in index if k.startswith('ps_'))
    log(f"[INFO] Indexed nodes : {len(index)} (products: {products_found}, processes: {processes_found})")

    # Save inventory for debugging
    # (out_dir / 'inventory.json').write_text(
    #     json.dumps({k: {'path': v['path'], 'type': v['type']} for k, v in index.items()},
    #                indent=2, ensure_ascii=False),
    #     encoding='utf-8'
    # )

    # Resolve root
    root_arg = CONFIG["ROOT_ID"]
    root_id = None

    # If ROOT_ID is a .md path (absolute or relative), parse it and use its stem as root_id
    try_path = Path(root_arg)
    if try_path.suffix.lower() == '.md':
        # Absolute path
        if try_path.is_absolute() and try_path.exists():
            info = parse_file_links_with_context(try_path)
            index[info['id']] = info
            root_id = info['id']
            log(f"[INFO] Using absolute root path: {try_path}")
        else:
            # Relative to repo_root
            rel_path = (repo_root / try_path).resolve()
            if rel_path.exists():
                info = parse_file_links_with_context(rel_path)
                index[info['id']] = info
                root_id = info['id']
                log(f"[INFO] Using relative root path (from repo_root): {rel_path}")
            else:
                log(f"[WARN] ROOT_ID path not found: {try_path} (checked {rel_path})")

    # Otherwise, ROOT_ID is a stem like 'pd_...'
    if root_id is None:
        candidate_stem = str(root_arg)
        if candidate_stem in index:
            root_id = candidate_stem
        else:
            # Try the common product path directly
            common_path = repo_root / 'product' / f'{candidate_stem}.md'
            if common_path.exists():
                info = parse_file_links_with_context(common_path)
                index[info['id']] = info
                root_id = info['id']
                log(f"[INFO] Using common product path: {common_path}")
            else:
                cands = suggest_ids(index, candidate_stem)
                msg = [
                    f"Root id/path '{root_arg}' not found in the scanned repository.",
                    f"Repo scanned: {repo_root}",
                    f"Tried common path: {common_path}",
                    "Tip: set ROOT_ID to the .md path (e.g., 'product/pd_....md').",
                    ("Close matches: " + ", ".join(cands)) if cands else "No close matches found."
                ]
                raise SystemExit("\n".join(msg))

    # Rebuild edges_in in case we added root on the fly
    for node in index.values():
        node['edges_in'] = []
    for node in index.values():
        for e in node.get('edges_out', []):
            if e['target'] in index:
                index[e['target']]['edges_in'].append(e)

    log(f"[INFO] Building tree from root: {root_id}")
    tree = build_tree(root_id, index,
                      include_reverse_producers=CONFIG["INCLUDE_REVERSE_PRODUCERS"],
                      max_depth=CONFIG["MAX_DEPTH"])

    edges = collect_reachable_edges(tree)

    # Write outputs
    # (out_dir / 'tree.json').write_text(json.dumps(tree, indent=2, ensure_ascii=False), encoding='utf-8')
    # (out_dir / 'edges.json').write_text(json.dumps(edges, indent=2, ensure_ascii=False), encoding='utf-8')

    mermaid = to_mermaid(tree, index)
    # Guard against any HTML entities (fixes '--&gt;' etc.)
    mermaid = (mermaid
               .replace('&gt;', '>')
               .replace('&lt;', '<')
               .replace('&amp;', '&'))
    mmd_path = out_dir / f'graph_{File_name_no_ext}.mmd'
    mmd_path.write_text(mermaid, encoding='utf-8')

    # dot = to_dot(edges, index)
    # (out_dir / 'graph.dot').write_text(dot, encoding='utf-8')

    # Optional: export SVG via Mermaid CLI if available
    # try_export_svg_with_mmdc(mmd_path, out_dir / 'graph.svg')

    summary = {
        "script_dir": str(SCRIPT_DIR),
        "repo_root": str(repo_root),
        "cwd": str(Path.cwd()),
        "root_id": root_id,
        "nodes_indexed": len(index),
        "products_found": products_found,
        "processes_found": processes_found
    }
    (out_dir / f'log_{File_name_no_ext}.text').write_text(
        "\n".join([f"{k}: {v}" for k, v in summary.items()]),
        encoding='utf-8'
    )

    # log(f"[OK] Wrote: {out_dir/'tree.json'}")
    # log(f"[OK] Wrote: {out_dir/'edges.json'}")
    log(f"[OK] Wrote: {out_dir/f'graph_{File_name_no_ext}.mmd'}") 
    # log(f"[OK] Wrote: {out_dir/'graph.dot'}")
    # if CONFIG.get("EXPORT_SVG_WITH_MMDC", False):
    #     log(f"[OK] SVG attempt done (see above for status).")
    # log(f"[OK] Inventory: {out_dir/'inventory.json'}")
    log(f"[OK] Log: {out_dir/'log.txt'}")

if __name__ == '__main__':
    main()
