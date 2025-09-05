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

def try_export_svg_with_mmdc(in_mmd: Path, out_svg: Path) -> bool:
    """
    If Mermaid CLI is available, export an SVG for convenience.
    Returns True on success, False otherwise.
    """
    if not CONFIG.get("EXPORT_SVG_WITH_MMDC", False):
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
