#!/usr/bin/env python3
"""
Fetch the latest IAB Content Taxonomy datasets from the IAB GitHub repo and
normalize them into the formats expected by this tool:

- iab_mapper/data/iab_2x.json  → [{"code": str, "label": str}]
- iab_mapper/data/iab_3x.json  → [{"id": str, "label": str, "path": [str,...], "scd": bool}]

Notes
- Uses GitHub's contents API to locate the latest 2.x and 3.x files.
- Supports JSON or TSV/CSV inputs; attempts to infer columns.
- Set GITHUB_TOKEN to raise rate limits; otherwise unauthenticated.
"""
from __future__ import annotations

import os
import sys
import json
import re
import io
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple

import requests
import pandas as pd


IAB_REPO = "InteractiveAdvertisingBureau/Taxonomies"
CONTENT_DIR = "Content Taxonomies"
GITHUB_API = "https://api.github.com"

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.abspath(os.path.join(ROOT, "iab_mapper", "data"))
RAW_DIR = os.path.join(DATA_DIR, "raw")


@dataclass
class FileMeta:
    name: str
    download_url: str


def gh_headers() -> Dict[str, str]:
    token = os.getenv("GITHUB_TOKEN")
    if token:
        return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    return {"Accept": "application/vnd.github+json"}


def list_content_files() -> List[FileMeta]:
    url = f"{GITHUB_API}/repos/{IAB_REPO}/contents/{requests.utils.quote(CONTENT_DIR, safe='')}"
    resp = requests.get(url, headers=gh_headers(), timeout=20)
    resp.raise_for_status()
    files = []
    for item in resp.json():
        if item.get("type") == "file":
            files.append(FileMeta(name=item["name"], download_url=item["download_url"]))
    return files


_VER_RE = re.compile(r"Content\s*Taxonomy\s*(?P<major>\d+)\.(?P<minor>\d+)", re.I)


def parse_version_from_name(name: str) -> Optional[Tuple[int, int]]:
    m = _VER_RE.search(name)
    if not m:
        return None
    return int(m.group("major")), int(m.group("minor"))


def pick_latest(files: List[FileMeta], major: int) -> Optional[FileMeta]:
    candidates: List[Tuple[Tuple[int, int], FileMeta]] = []
    for f in files:
        ver = parse_version_from_name(f.name)
        if not ver:
            continue
        maj, minr = ver
        if maj == major:
            candidates.append(((maj, minr), f))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0][1], reverse=True)
    return candidates[0][1]


def download_text(url: str) -> str:
    r = requests.get(url, headers=gh_headers(), timeout=30)
    r.raise_for_status()
    return r.text


def save_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def to_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if val is None:
        return False
    s = str(val).strip().lower()
    return s in {"true", "1", "yes", "y"}


def normalize_2x(df: pd.DataFrame) -> List[Dict[str, Any]]:
    cols = {c.lower(): c for c in df.columns}
    id_col = next((cols[k] for k in cols if k in {"code", "id", "node id", "taxonomy id", "unique id"}), None)
    label_col = next((cols[k] for k in cols if k in {"label", "name", "node", "node name"}), None)
    if not id_col or not label_col:
        raise ValueError("Could not infer 2.x id/label columns")
    out: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        code = str(row.get(id_col) or "").strip()
        label = str(row.get(label_col) or "").strip()
        if not code or not label:
            continue
        out.append({"code": code, "label": label})
    return out


def normalize_3x(df: pd.DataFrame) -> List[Dict[str, Any]]:
    cols = {c.lower(): c for c in df.columns}
    id_col = next((cols[k] for k in cols if k in {"id", "node id", "taxonomy id", "unique id"}), None)
    label_col = next((cols[k] for k in cols if k in {"label", "name", "node", "node name"}), None)
    path_col = next((cols[k] for k in cols if k in {"path", "full path", "taxonomy path"}), None)
    scd_col = next((cols[k] for k in cols if k in {"scd", "sensitive", "is scd"}), None)

    tier_cols = [cols[c] for c in df.columns.str.lower() if c.startswith("tier ") or c.startswith("tier")]

    def row_path(r) -> List[str]:
        if path_col:
            raw = r.get(path_col)
            if isinstance(raw, str) and raw.strip():
                parts = [p.strip() for p in re.split(r">|/|\\|,", raw) if p.strip()]
                if parts:
                    return parts
        # Try tier columns
        parts = []
        for t in tier_cols:
            val = str(r.get(t) or "").strip()
            if val:
                parts.append(val)
        return parts

    if not id_col or not label_col:
        raise ValueError("Could not infer 3.x id/label columns")

    out: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        id_ = str(row.get(id_col) or "").strip()
        label = str(row.get(label_col) or "").strip()
        if not id_ or not label:
            continue
        path = row_path(row) or [label]
        scd = to_bool(row.get(scd_col)) if scd_col else False
        out.append({"id": id_, "label": label, "path": path, "scd": scd})
    return out


def parse_table(text: str, name: str) -> pd.DataFrame:
    # Decide delimiter by filename extension, and detect header row
    lower = name.lower()
    lines = text.splitlines()
    header_idx = 0
    for i, line in enumerate(lines[:10]):
        if ("unique id" in line.lower()) and ("name" in line.lower()):
            header_idx = i
            break
    sio = io.StringIO(text)
    if lower.endswith(".tsv"):
        return pd.read_csv(sio, sep="\t", header=header_idx)
    if lower.endswith(".csv"):
        return pd.read_csv(sio, header=header_idx)
    # Try to parse JSON as table-like
    try:
        data = json.loads(text)
    except Exception:
        raise ValueError(f"Unsupported file format for {name}")
    # If it's already a flat list, return as DataFrame
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return pd.DataFrame(data)
    # Otherwise, attempt to flatten a hierarchical JSON under common keys
    rows: List[Dict[str, Any]] = []

    def walk(node: Dict[str, Any], ancestors: List[str]):
        nid = node.get("id") or node.get("code")
        label = node.get("label") or node.get("name")
        scd = node.get("scd") or node.get("is_scd") or node.get("sensitive")
        children = node.get("children") or node.get("nodes") or []
        if nid and label:
            rows.append({
                "id": nid,
                "label": label,
                "path": ancestors + [label],
                "scd": scd,
            })
        for c in children:
            if isinstance(c, dict):
                walk(c, ancestors + [label] if label else ancestors)

    if isinstance(data, dict):
        walk(data, [])
    elif isinstance(data, list):
        for n in data:
            if isinstance(n, dict):
                walk(n, [])
    return pd.DataFrame(rows)


def main() -> int:
    print("[update_catalogs] Listing IAB content taxonomy files…")
    files = list_content_files()
    f3 = pick_latest(files, major=3)
    f2 = pick_latest(files, major=2)
    if not f3:
        print("ERROR: Could not locate a Content Taxonomy 3.x file in the IAB repo.")
        return 1
    if not f2:
        print("WARNING: Could not locate a Content Taxonomy 2.x file; continuing with 3.x only.")

    os.makedirs(RAW_DIR, exist_ok=True)

    # 3.x
    print(f"[update_catalogs] Downloading 3.x → {f3.name}")
    txt3 = download_text(f3.download_url)
    open(os.path.join(RAW_DIR, f3.name), "w", encoding="utf-8").write(txt3)
    df3 = parse_table(txt3, f3.name)
    try:
        norm3 = normalize_3x(df3)
        save_json(os.path.join(DATA_DIR, "iab_3x.json"), norm3)
        print(f"[update_catalogs] Wrote {len(norm3)} rows → iab_mapper/data/iab_3x.json")
    except Exception as e:
        print(f"ERROR: Failed to normalize 3.x: {e}")

    # 2.x
    if f2:
        print(f"[update_catalogs] Downloading 2.x → {f2.name}")
        txt2 = download_text(f2.download_url)
        open(os.path.join(RAW_DIR, f2.name), "w", encoding="utf-8").write(txt2)
        df2 = parse_table(txt2, f2.name)
        try:
            norm2 = normalize_2x(df2)
            save_json(os.path.join(DATA_DIR, "iab_2x.json"), norm2)
            print(f"[update_catalogs] Wrote {len(norm2)} rows → iab_mapper/data/iab_2x.json")
        except Exception as e:
            print(f"ERROR: Failed to normalize 2.x: {e}")

    print("[update_catalogs] Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())


