import json
import re
from pathlib import Path
from typing import Dict, List, Optional

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

        if current_h2 and current_h2.lower() == 'list of processes' and node_type == 'product':
            if stripped.startswith(('* ', '- ')) and not LINK_PATTERN.search(stripped):
                label = stripped[2:].strip()
                m_id = re.search(r'\b(ps_[a-zA-Z0-9_]+)\b', label)
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
    index: Dict[str, Dict] = {}
    all_md = [p for p in repo_root.rglob("*") if p.is_file() and p.suffix.lower() == ".md"]
    candidates = [p for p in all_md if p.stem.lower().startswith(("pd_", "ps_"))]
    for md in candidates:
        nid = md.stem
        if nid in index:
            continue
        info = parse_file_links_with_context(md)
        index[info['id']] = info
    for node in index.values():
        node['edges_in'] = []
    for node in index.values():
        for e in node.get('edges_out', []):
            tgt = e['target']
            if tgt in index:
                index[tgt]['edges_in'].append(e)
    return index

def build_tree(root_id: str,
               index: Dict[str, Dict],
               include_reverse_producers: bool = True,
               max_depth: Optional[int] = None,
               _path_stack: Optional[List[str]] = None) -> Dict:
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
    if root_id in _path_stack:
        node['cycle'] = True
        return node
    if max_depth is not None and len(_path_stack) >= max_depth:
        node['truncated'] = True
        return node
    neighbors = []
    for e in node_info.get('edges_out', []):
        neighbors.append((e, 'forward'))
    if include_reverse_producers and node_info['type'] == 'product':
        for e in node_info.get('edges_in', []):
            if e.get('rel') == 'produces':
                e_copy = dict(e)
                e_copy['rel'] = 'produced_by'
                neighbors.append((e_copy, 'reverse'))
    seen_pairs = set()
    unique_neighbors = []
    for e, lab in neighbors:
        if e['rel'] in ('produces', 'produced_by'):
            product = e['source'] if e['source_type'] == 'product' else e['target']
            process = e['source'] if e['source_type'] == 'process' else e['target']
            key = (product, process)
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            if e['rel'] == 'produced_by':
                produces_exists = any(
                    ((ne['source'] if ne['source_type'] == 'product' else ne['target']) == product and
                     (ne['source'] if ne['source_type'] == 'process' else ne['target']) == process and
                     ne['rel'] == 'produces')
                    for ne, _ in neighbors
                )
                if produces_exists:
                    continue
        unique_neighbors.append((e, lab))
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
from build_lca_tree import CONFIG
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def log(msg: str):
    if CONFIG.get("VERBOSE", True):
        print(msg)

def normalize_id_from_target(target: str) -> str:
    """
    Normalize a markdown link target to a stem 'pd_xxx' or 'ps_xxx'
    Accepts 'pd_xxx', 'pd_xxx.md', 'product/pd_xxx.md', with #anchor or ?query removed.
    """
    t = target.strip()
    t = t.split('#')[0].split('?')[0]
    base = os.path.basename(t)
    if base.lower().endswith('.md'):
        base = base[:-3]
    return base

def infer_node_type_from_id(node_id: str) -> str:
    if node_id.startswith('pd_'):
        return 'product'
    if node_id.startswith('ps_'):
        return 'process'
    return 'unknown'

def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8')
    except Exception:
        try:
            return path.read_text(encoding='utf-8-sig')
        except Exception:
            return ""
        
def sanitize_mermaid_id(s: str) -> str:
    """
    Mermaid node IDs must be safe tokens. Keep [A-Za-z0-9_]; prefix if starting with a digit.
    """
    nid = re.sub(r'[^0-9A-Za-z_]', '_', s)
    if re.match(r'^\d', nid):
        nid = f"n_{nid}"
    return nid

def sanitize_mermaid_label(text: str) -> str:
    """
    Make labels Mermaid-safe:
    - remove '|' and replace [] with ()
    - strip parentheses (some builds are sensitive)
    - collapse whitespace and trim
    - shorten if too long
    """
    if text is None:
        return ""
    t = str(text)
    t = t.replace('|', '/')
    t = t.replace('[', '(').replace(']', ')')
    t = t.replace('(', '').replace(')', '')
    t = re.sub(r'\s+', ' ', t).strip()
    if len(t) > 80:
        t = t[:77] + '...'
    return t

def esc_quotes(s: str) -> str:
    return str(s).replace('"', '\\"')


def parse_quantity_unit(text: str) -> Tuple[Optional[float], Optional[str], Optional[str]]:
    """
    From trailing text like:
      " - Quantity: 12.5 kg - Database: ecoinvent"
      " - Quantity: None unit"
      " - Quantity: Not specified - Database: Not specified"
    Return (value, unit, database).
    """
    qty_raw = None
    unit = None
    db = None

    mdb = re.search(r'Database:\s*([^-;\n]+)', text, flags=re.IGNORECASE)
    if mdb:
        db = mdb.group(1).strip()

    mqty = re.search(r'Quantity:\s*([^-;\n]+)', text, flags=re.IGNORECASE)
    if mqty:
        qty_raw = mqty.group(1).strip()
        mnum = re.match(r'([+-]?(\d+(\.\d+)?|\.\d+)([eE][+-]?\d+)?)\s*(.*)$', qty_raw)
        if mnum:
            try:
                val = float(mnum.group(1))
            except Exception:
                val = None
            tail = mnum.group(5).strip() if mnum.group(5) else None
            unit = tail if tail else None
            return val, unit, db
        return None, None, db

    return None, None, db

def to_dot(edges: List[Dict], index: Dict[str, Dict]) -> str:
    """
    Graphviz DOT for the reachable subgraph.
    """
    out = []
    out.append('digraph G {')
    out.append('  rankdir=LR;')
    out.append('  node [shape=box, style=rounded, fontsize=10];')

    nodes = set()
    for e in edges:
        nodes.add(e['source']); nodes.add(e['target'])

    for nid in sorted(nodes):
        info = index.get(nid, {'id': nid, 'type': infer_node_type_from_id(nid), 'title': nid})
        # label = f"{info['title']}\\n({info['type']})"
        max_label_length = 30  # or whatever length you prefer
        title = info['title']
        if len(title) > max_label_length:
            title = title[:max_label_length - 3] + "..."
        label = f"{title}\n({info['type']})"

        shape = 'oval' if info['type'] == 'product' else 'box'
        fillcolor = '#e8f5e9' if info['type'] == 'product' else ('#e3f2fd' if info['type'] == 'process' else '#fff3e0')
        color = '#2e7d32' if info['type'] == 'product' else ('#1565c0' if info['type'] == 'process' else '#ef6c00')
        out.append(f'  "{esc_quotes(nid)}" [label="{esc_quotes(label)}", shape={shape}, style="filled,rounded", fillcolor="{fillcolor}", color="{color}"];')

    for e in edges:
        label = e['rel']
        if e.get('quantity') is not None:
            label = f'{label} ({e["quantity"]} {e.get("unit") or ""})'.strip()
        out.append(f'  "{esc_quotes(e["source"])}" -> "{esc_quotes(e["target"])}" [label="{esc_quotes(label)}", fontsize=9];')

    out.append('}')
    return "\n".join(out)

def suggest_ids(index: Dict[str, Dict], wanted: str, limit: int = 12) -> List[str]:
    w = wanted.lower()
    cands = [nid for nid in index.keys() if w in nid.lower()]
    cands.sort()
    return cands[:limit]

def try_export_png_with_mmdc(in_mmd: Path, out_png: Path) -> bool:
    """
    If Mermaid CLI is available, export a PNG for convenience.
    Returns True on success, False otherwise.
    """
    if not CONFIG.get("EXPORT_SVG_WITH_MMDC", True):
        return False

    mmdc = CONFIG.get("MMDC_PATH")
    if not mmdc:
        mmdc = shutil.which("mmdc")
    if not mmdc:
        log("[INFO] Mermaid CLI (mmdc) not found in PATH — skipping PNG export.")
        return False

    try:
        log(f"[INFO] Running mmdc to export PNG: {mmdc}")
        
        # Handle Windows PowerShell script
        if mmdc.endswith('.ps1'):
            # Run PowerShell script
            cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", mmdc, "-i", str(in_mmd), "-o", str(out_png), "-e", "png"]
        else:
            # Run as regular executable
            cmd = [mmdc, "-i", str(in_mmd), "-o", str(out_png), "-e", "png"]
        
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        log(f"[OK] Mermaid PNG written: {out_png}")
        return True
    except subprocess.CalledProcessError as e:
        log("[WARN] mmdc failed to export PNG. stderr:")
        log(e.stderr.decode(errors="ignore"))
    except Exception as ex:
        log(f"[WARN] mmdc PNG export error: {ex}")
    return False

def convert_svg_to_png(svg_path: Path, png_path: Path) -> bool:
    """
    Convert SVG to PNG using various methods for better quality.
    Returns True on success, False otherwise.
    """
    if not svg_path.exists():
        log(f"[WARN] SVG file not found: {svg_path}")
        return False
    
    try:
        # Method 1: Try using Inkscape (if available)
        inkscape = shutil.which("inkscape")
        if inkscape:
            log(f"[INFO] Converting SVG to PNG using Inkscape: {svg_path} -> {png_path}")
            subprocess.run(
                [inkscape, "--export-type=png", "--export-filename", str(png_path), str(svg_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            log(f"[OK] PNG created with Inkscape: {png_path}")
            return True
        
        # Method 2: Try using ImageMagick (if available)
        magick = shutil.which("magick")
        if magick:
            log(f"[INFO] Converting SVG to PNG using ImageMagick: {svg_path} -> {png_path}")
            subprocess.run(
                [magick, str(svg_path), str(png_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            log(f"[OK] PNG created with ImageMagick: {png_path}")
            return True
        
        # Method 3: Try using rsvg-convert (if available)
        rsvg = shutil.which("rsvg-convert")
        if rsvg:
            log(f"[INFO] Converting SVG to PNG using rsvg-convert: {svg_path} -> {png_path}")
            subprocess.run(
                [rsvg, "-h", "800", "-o", str(png_path), str(svg_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            log(f"[OK] PNG created with rsvg-convert: {png_path}")
            return True
        
        log("[INFO] No SVG to PNG converter found (tried Inkscape, ImageMagick, rsvg-convert)")
        return False
        
    except subprocess.CalledProcessError as e:
        log(f"[WARN] SVG to PNG conversion failed. stderr: {e.stderr.decode(errors='ignore')}")
    except Exception as ex:
        log(f"[WARN] SVG to PNG conversion error: {ex}")
    return False

def try_export_svg_with_mmdc(in_mmd: Path, out_svg: Path) -> bool:
    """
    If Mermaid CLI is available, export an SVG for convenience.
    Returns True on success, False otherwise.
    """
    if not CONFIG.get("EXPORT_SVG_WITH_MMDC", True):
        return False

    mmdc = CONFIG.get("MMDC_PATH")
    if not mmdc:
        mmdc = shutil.which("mmdc")
    if not mmdc:
        log("[INFO] Mermaid CLI (mmdc) not found in PATH — skipping SVG export.")
        return False

    try:
        log(f"[INFO] Running mmdc to export SVG: {mmdc}")
        subprocess.run(
            [mmdc, "-i", str(in_mmd), "-o", str(out_svg)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        log(f"[OK] Mermaid SVG written: {out_svg}")
        return True
    except subprocess.CalledProcessError as e:
        log("[WARN] mmdc failed to export SVG. stderr:")
        log(e.stderr.decode(errors="ignore"))
    except Exception as ex:
        log(f"[WARN] mmdc export error: {ex}")
    return False

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
        # Skip rn_ files (root node files) from the tree diagram
        if node_id.startswith('rn_'):
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
        # Skip rn_ files (root node files) from the tree diagram
        if n['id'].startswith('rn_'):
            return
        add_node(n['id'])
        for ch in n.get('children', []):
            # Skip edges involving rn_ files
            if ch['source'].startswith('rn_') or ch['target'].startswith('rn_'):
                continue
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

def compute_tree_path_for_pair(repo_root: Path, root_product: str, root_process: str, target_product: str, target_process: str, save_tree: bool = True, output_dir: Optional[Path] = None) -> str:
    """
    Compute the original tree path from the root product/process to the target product/process.
    Returns a string like 'rn_pd_livebox_6_user_interface_ps_livebox_6_user_interface_production'.
    
    Args:
        repo_root: Path to the repository root
        root_product: Root product ID
        root_process: Root process ID  
        target_product: Target product ID
        target_process: Target process ID
        save_tree: Whether to save tree files (JSON, Mermaid, etc.)
        output_dir: Directory to save tree files (defaults to repo_root/out_tree)
    """
    index = scan_repository(repo_root)
    # Prefer root_product if present, else root_process
    root_id = root_product if root_product in index else root_process
    tree = build_tree(root_id, index, include_reverse_producers=False, max_depth=None)

    def find_path(node, target_ids, path=None):
        if path is None:
            path = []
        if node['id'] in target_ids:
            return path + [node['id']]
        for child in node.get('children', []):
            result = find_path(child['child'], target_ids, path + [node['id']])
            if result:
                return result
        return None

    target_ids = [target_product, target_process]
    path_list = find_path(tree, target_ids)
    if path_list:
        prod = next((nid for nid in path_list if nid.startswith('pd_')), None)
        proc = next((nid for nid in path_list if nid.startswith('ps_')), None)
        if prod and proc:
            tree_path_name = f"rn_{prod}_{proc}"
        else:
            tree_path_name = f"rn_{target_product}_{target_process}"
    else:
        tree_path_name = f"rn_{target_product}_{target_process}"
    
    # Save tree files if requested
    if save_tree:
        if output_dir is None:
            output_dir = repo_root / "out_tree"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save tree data as markdown file (JSON content with .md extension)
        tree_json = json.dumps(tree, indent=2, ensure_ascii=False)
        tree_md_path = output_dir / f'{tree_path_name}.md'
        tree_md_path.write_text(tree_json, encoding='utf-8')
        
        # Generate Mermaid diagram and convert to PNG
        mermaid = to_mermaid(tree, index)
        # Guard against any HTML entities (fixes '--&gt;' etc.)
        mermaid = (mermaid
                   .replace('&gt;', '>')
                   .replace('&lt;', '<')
                   .replace('&amp;', '&'))
        mmd_path = output_dir / f'{tree_path_name}.mmd'
        mmd_path.write_text(mermaid, encoding='utf-8')
        
        # Generate SVG first, then convert to PNG for better quality
        svg_path = output_dir / f'{tree_path_name}.svg'
        png_path = output_dir / f'{tree_path_name}.png'
        
        print(f"[DEBUG] Attempting SVG export: {mmd_path} -> {svg_path}")
        svg_success = try_export_svg_with_mmdc(mmd_path, svg_path)
        
        if svg_success:
            print(f"[OK] SVG file created: {svg_path}")
            # Convert SVG to PNG for better quality
            print(f"[DEBUG] Converting SVG to PNG: {svg_path} -> {png_path}")
            png_success = convert_svg_to_png(svg_path, png_path)
            if png_success:
                print(f"[OK] PNG file created from SVG: {png_path}")
            else:
                print(f"[INFO] SVG to PNG conversion failed")
        else:
            print(f"[INFO] SVG export failed, skipping PNG generation")
        
        print(f"[OK] Tree data saved to: {tree_md_path}")
        print(f"[OK] Mermaid diagram saved to: {mmd_path}")
        print(f"[OK] Tree path name: {tree_path_name}")
    
    return tree_path_name
