<p align="center">
  <img src="assets/header.png" alt="IAB Taxonomy Mapper" width="900" />
</p>

# IAB Content Taxonomy Mapper (Local CLI)

<p align="center">
  <a href="https://pypi.org/project/iab-mapper/"><img alt="PyPI" src="https://img.shields.io/pypi/v/iab-mapper.svg"></a>
  <a href="https://img.shields.io/pypi/dm/iab-mapper"><img alt="Downloads" src="https://img.shields.io/pypi/dm/iab-mapper"></a>
  <a href="https://github.com/mixpeek/iab-mapper/actions"><img alt="CI" src="https://github.com/mixpeek/iab-mapper/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://github.com/mixpeek/iab-mapper/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
</p>

Map **IAB Content Taxonomy 2.x** labels/codes to **IAB 3.0** locally with a deterministic → fuzzy → (optional) semantic pipeline.
Outputs are **IAB‑3.0–compatible IDs** for OpenRTB/VAST, with optional **vector attributes** (Channel, Type, Format, Language, Source, Environment) and **SCD** awareness.

> Local-first by default. No external APIs are required; LLM re‑rank is optional.

---

## 📚 Table of Contents

- [✨ Features](#-features)
- [Why migrate to IAB 3.0?](#-why-migrate-to-iab-30)
- [How it works](#-how-it-works)
- [🔧 Install](#-install)
- [🚀 Quick Start](#-quick-start)
- [🐍 Python API](#-python-api-alternative-to-cli)
- [📥 Input Formats](#-input-formats)
- [📤 Output Formats](#-output-formats)
- [⚙️ Useful Flags](#️-useful-flags)
- [🧩 Vectors](#-vectors-orthogonal-attributes)
- [✅ IAB 3.0 Conformance Notes](#-iab-30-conformance-notes)
- [📎 Official IAB References](#-official-iab-references)
- [🧯 Troubleshooting](#-troubleshooting)
- [📦 Example Commands](#-example-commands)
- [📜 License](#-license)

---

### Versioning snapshot

| IAB 2.x supported | IAB 3.x supported | Updated       |
|-------------------|-------------------|---------------|
| 2.2               | 3.1               | 2025-09-12    |

---

### Update catalogs (fetch latest from IAB)

Use the bundled fetcher to sync to the latest Content Taxonomy files from the official IAB GitHub repository. It will locate the latest 2.x and 3.x datasets and normalize them into this tool’s schemas.

```bash
# via Python script (direct)
python scripts/update_catalogs.py

# or via CLI command
mixpeek-iab-mapper update-catalogs --exact3 "3.1" --exact2 "2.2"
# Optional: use a GitHub token to raise rate limits
# export GITHUB_TOKEN=ghp_...
```

Outputs:
- `iab_mapper/data/iab_2x.json` → `[{"code","label"}]`
- `iab_mapper/data/iab_3x.json` → `[{"id","label","path":[],"scd":bool}]`

Replace or extend `synonyms_*.json` and `vectors_*.json` as needed for your org.

---

## ✨ Features
- Deterministic alias/exact matching → fuzzy string matching → **optional local embeddings** (Sentence-Transformers) for near-misses
- Emits **IAB 3.0 IDs** (not just labels) and configurable **`cattax`** for OpenRTB conformance
- Multi-category output per input; **vector attributes** support
- **SCD (Sensitive Content) flag** visibility and optional exclusion (`--drop-scd`)
- Exports **CSV or JSON**; includes **OpenRTB** and **VAST CONTENTCAT** helpers
- Local-only, reproducible, versioned catalogs

---

## 🔎 Why migrate to IAB 3.0?

- 3.0 introduces clearer separation of primary topic “aboutness” vs. orthogonal vectors (e.g., news vs. opinion, formats, channels).
- Better support for CTV/video, podcasts, games, and app stores.
- Non‑backwards compatible in areas like News/Opinion and entertainment genres; careful migration is required.

This tool makes migration practical: it emits valid 3.0 IDs and helps curate edge cases with overrides, synonyms, thresholds, and audit outputs.

---

## 🧠 How it works

1) Normalize text and apply alias/exact matches via synonyms.
2) Fuzzy retrieval (rapidfuzz | TF‑IDF | BM25) with configurable thresholds.
3) Optional semantic augmentation with local embeddings (Sentence‑Transformers or TF‑IDF KNN).
4) Optional local LLM re‑ranking (Ollama) for ordering only.
5) Assemble outputs: topic IDs + vector IDs → OpenRTB `content.cat` with configurable `cattax`.
6) SCD flags are surfaced and can be excluded with `--drop-scd`.

---

## 🔧 Install

### From PyPI (recommended)
```bash
pip install iab-mapper
```

### 1) Clone / unpack
```bash
unzip iab-mapper.zip && cd iab-mapper
```

### 2) Python env & install
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
# Optional (enable local embeddings / KNN search)
pip install -e ".[emb]"
```

> If you need fully offline installs, pre-bundle the Sentence-Transformers model in your image/host and point to it via `--emb-model` (local path).

### 3) LLM Re-ranking (Ollama, optional)
If you intend to use the LLM re-ranking feature (available in the demo's "Advanced options"), you need to have [Ollama](https://ollama.com/) installed and the `llama3.1:8b` model pulled locally.

```bash
# Install Ollama (if you haven't already)
# Refer to https://ollama.com/download for installation instructions

# Pull the required LLM model
ollama pull llama3.1:8b
```

After installing Ollama and pulling the model, ensure your Ollama server is running (it usually starts automatically after installation).

---

## 📁 Project Layout
```
iab-mapper/
  pyproject.toml
  sample_2x_codes.csv
  iab_mapper/
    __init__.py
    cli.py
    pipeline.py
    matching.py
    normalize.py
    embeddings.py
    io_utils.py
    data/
      iab_2x.json
      iab_3x.json
      synonyms_2x.json
      synonyms_3x.json
      vectors_channel.json
      vectors_type.json
      vectors_format.json
      vectors_language.json
      vectors_source.json
      vectors_environment.json
```

Replace the stub `data/*.json` with your **full IAB catalogs** (include `id`, `label`, `path`, and `scd` on 3.0 nodes).

---

## 🚀 Quick Start

```bash
# simplest path: fuzzy only, CSV in → JSON out
iab-mapper sample_2x_codes.csv -o mapped.json

# enable local embeddings (improves recall on free‑text labels)
iab-mapper sample_2x_codes.csv -o mapped.json --use-embeddings
```

OpenRTB and VAST helpers (example output):

```json
{"content":{"cat":["3-5-2","1026","1068"],"cattax":"2"}}
```

```text
"3-5-2","1026","1068"
```

The output contains for each input row:
- `out_ids` → **IAB 3.0 IDs** (topics + any vector IDs)
- `openrtb` → `{"content":{"cat":[...],"cattax":"<enum>"}}` (configurable via `--cattax`)
- `vast_contentcat` → `"id1","id2",...`
- Topic confidences, sources (`"exact"/"fuzzy"/"embed"/"override"), SCD flags, and chosen vectors.

---

## 🐍 Python API (alternative to CLI)

Install:
```bash
pip install iab-mapper
```

Basic usage:
```python
from pathlib import Path
from iab_mapper.pipeline import Mapper, MapConfig
import iab_mapper as pkg

# Use packaged stub catalogs or point data_dir to your own
data_dir = Path(pkg.__file__).parent / "data"

cfg = MapConfig(
    fuzzy_method="bm25",   # rapidfuzz|tfidf|bm25
    fuzzy_cut=0.92,
    use_embeddings=False,   # set True and choose emb_model to enable
    max_topics=3,
    drop_scd=False,
    cattax="2",            # OpenRTB content.cattax enum
    overrides_path=None     # path to JSON overrides if desired
)

mapper = Mapper(cfg, str(data_dir))

# Single record with optional vectors
rec = {
    "code": "2-12",
    "label": "Food & Drink",
    "channel": "editorial",
    "type": "article",
    "format": "video",
    "language": "en",
    "source": "professional",
    "environment": "ctv",
}

out = mapper.map_record(rec)
print(out["out_ids"])         # topic + vector IDs
print(out["openrtb"])         # {"content": {"cat": [...], "cattax": "2"}}
print(out["vast_contentcat"]) # "id1","id2",...

# Or just map topics
topics = mapper.map_topics("Cooking how-to")

# Batch over a list of dicts
rows = [rec, {"label": "Sports"}]
mapped = [mapper.map_record(r) for r in rows]
```

Enable local embeddings (optional):
```python
cfg = MapConfig(fuzzy_method="rapidfuzz", use_embeddings=True, emb_model="tfidf", emb_cut=0.8)
mapper = Mapper(cfg, str(data_dir))
out = mapper.map_record({"label": "Cooking how-to"})
```

Use overrides (force mapping before matching):
```python
cfg = MapConfig(overrides_path="overrides.json")  # [{"code":"1-4","label":null,"ids":["2-3-18"]}]
mapper = Mapper(cfg, str(data_dir))
```

---

## 📥 Input Formats

### CSV
- Required columns: `label`
- Optional columns: `code` (2.x), `channel`, `type`, `format`, `language`, `source`, `environment`

Example:
```csv
code,label,channel,type,format,language,source,environment
1-4,Sports,editorial,article,video,en,professional,ctv
, Cooking how-to ,editorial,article,video,en,professional,web
```

### JSON
- List of objects with the same fields as CSV.

---

## 📤 Output Formats

### CSV
- Includes compact JSON strings for complex fields (e.g., `topic_ids`, `openrtb`).

### JSON
- List of records. Example snippet:
```json
{
  "in_code": "2-12",
  "in_label": "Food & Drink",
  "out_ids": ["3-5-2", "1026", "1068"],
  "out_labels": ["Food & Drink > Cooking"],
  "topic_ids": ["3-5-2"],
  "topic_confidence": [0.89],
  "topic_sources": ["fuzzy"],
  "topic_scd": [false],
  "vectors": {"channel":"editorial","type":"article","format":"video","language":"en","source":"professional","environment":"ctv"},
  "cattax": "2",
  "openrtb": {"content":{"cat":["3-5-2","1026","1068"],"cattax":"2"}},
  "vast_contentcat": ""3-5-2","1026","1068""
}
```

---

## ⚙️ Useful Flags

| Flag | Default | What it does |
|------|---------|--------------|
| `--fuzzy-cut` | `0.92` | Stricter = fewer, higher-confidence matches |
| `--use-embeddings` | off | Enable local embeddings for near-miss labels |
| `--emb-model` | `all-MiniLM-L6-v2` | Sentence-Transformers model or `tfidf` |
| `--emb-cut` | `0.80` | Cosine similarity threshold for embeddings |
| `--max-topics` | `3` | Cap topic IDs per row |
| `--drop-scd` | off | Exclude Sensitive Content nodes |
| `--cattax` | `2` | OpenRTB `content.cattax` enum |
| `--unmapped-out` | — | Write misses to file for audit |
| `--overrides` | — | Force mappings before match |

---

## 🧩 Vectors (Orthogonal Attributes)
Pass via columns or pre-fill in your CSV:
- **Channel** (`vectors_channel.json`): e.g., `editorial`, `ugc`
- **Type** (`vectors_type.json`): e.g., `article`, `podcast`, `livestream`
- **Format** (`vectors_format.json`): e.g., `video`, `text`, `audio`
- **Language** (`vectors_language.json`): e.g., `en`, `es`, `de`
- **Source** (`vectors_source.json`): e.g., `professional`, `brand`, `news`
- **Environment** (`vectors_environment.json`): e.g., `ctv`, `web`, `app`

Each value maps to a **stable IAB 3.0 ID** that is appended to the `cat` array.

---

## ✅ IAB 3.0 Conformance Notes
- Emits **IDs** for `content.cat` and sets **`"cattax":"<enum>"`**.  
- Supports **multiple categories per content** (topic IDs + vectors).  
- **Strict ID validation**: only IDs present in your 3.0 catalog are emitted.  
- **SCD-aware**: show SCD flags and optionally exclude (`--drop-scd`).

> This tool is **not affiliated with IAB**. It is an independent utility for compatibility with IAB Content Taxonomy.

---

## 📎 Official IAB References

- Content Taxonomy 3.0 Implementation Guide (PDF): https://iabtechlab.com/wp-content/uploads/2021/09/Implementation-Guide-Content-Taxonomy-3-0-pc-Sept2021.pdf
- IAB Tech Lab Content Taxonomy page: https://iabtechlab.com/standards/content-taxonomy/
- Implementation guidance (historic mappings and migration notes):
  - https://github.com/InteractiveAdvertisingBureau/Taxonomies/blob/develop/implementation.md#content-21-to-ad-product-20-taxonomy-mapping-implementation-guidance
  - https://github.com/InteractiveAdvertisingBureau/Taxonomies/blob/develop/Taxonomy%20Mappings/Ad%20Product%202.0%20to%20Content%202.1.tsv
  - https://github.com/katieshell/Taxonomies/blob/main/implementation.md#implementation-guidance-for-content-1--content-2-mapping
  - https://github.com/katieshell/Taxonomies/blob/main/implementation.md#migrating-from-content-taxonomy-10

---

## 🔬 Evaluation (recommended)
Create a small gold set for your domain and run periodic checks:
```bash
# (pseudo) compare mapped.json to gold.json for accuracy & unmapped rates
python scripts/eval.py mapped.json gold.json
```
Gate releases on accuracy deltas so behavior stays stable for audits.

Minimal starter:

```json
// scripts/gold.json
[{"in_label":"Sports","topic_ids":["483"]}]
```

```python
# scripts/eval.py (toy example)
import json, sys
pred = { (r.get('in_label')): set(r.get('topic_ids',[])) for r in json.load(open(sys.argv[1])) }
gold = { (r.get('in_label')): set(r.get('topic_ids',[])) for r in json.load(open(sys.argv[2])) }
tp=fp=fn=0
for k in gold:
    g=gold[k]; p=pred.get(k,set())
    tp += len(g & p); fp += len(p - g); fn += len(g - p)
print({'tp':tp,'fp':fp,'fn':fn})
```

---

## 🛠️ Updating Catalogs
Replace the stub JSONs in `iab_mapper/data/` with your official datasets:
- `iab_2x.json` → include `code`, `label`
- `iab_3x.json` → include `id`, `label`, `path[]`, `scd`
- `synonyms_*.json` → org-specific aliases
 - `vectors_*.json` → official vector catalogs mapping values to stable 3.0 IDs

Commit with a version bump and note `taxonomy_version` in your release notes.

---

## 🔐 Security & operations

- Local-first: processing happens on your machine; no external APIs needed.
- No PII required; CSV/JSON processed in-memory.
- Air‑gapped: prebundle ST model and run `iab-mapper` fully offline.

---

## 🤝 Using Mixpeek API (optional)

If you prefer managing catalogs, outputs, and audits centrally, you can run mapping locally and then persist results via Mixpeek for auditability.

```http
# 1) create collection
POST /collections { "name": "iab-taxonomy" }

# 2) create 'document' with 2.x codes
POST /collections/{id}/documents { "document_id":"iab-2x", "properties": { ... } }

# 3) run taxonomy feature extractor (2.x → 3.0)
POST /collections/{id}/documents/{doc}/features { "extractor":"taxonomy", "params":{"target_version":"3.0"} }

# 4) fetch enriched doc
GET /collections/{id}/documents/{doc}
```

See also: [Taxonomy Mapper tool](/tools/iab-taxonomy-mapper), [Taxonomy audit tool](/tools/taxonomy-audit), [Video guide](/education/videos/taxonomies-guide), and the landing page at [mxp.co/taxonomy](https://mxp.co/taxonomy).

## 🧯 Troubleshooting
- **No matches:** lower `--fuzzy-cut` or enable `--use-embeddings`.
- **Weird matches:** raise thresholds; add synonyms into `synonyms_*.json`.
- **Offline:** pre-bundle ST model; set `--emb-model` to a local folder path.
- **CSV issues:** ensure UTF-8 and header row (`label` required).
 - **Unmapped:** inspect `--unmapped-out` and add overrides/synonyms as needed.

---

## 📦 Example Commands
```bash
# Strict fuzzy only
iab-mapper sample_2x_codes.csv -o mapped.csv --fuzzy-cut 0.95

# Embeddings on, drop SCD, max 2 topics, custom cattax, collect unmapped
iab-mapper sample_2x_codes.csv -o mapped.json --use-embeddings --drop-scd --max-topics 2 --cattax 2 --unmapped-out misses.json
```

---

## 📜 License
MIT. See [LICENSE](LICENSE).

Include IAB attribution in your deployed UI/footer:
> “IAB is a registered trademark of the Interactive Advertising Bureau. This tool is an independent utility built by Mixpeek for interoperability with IAB Content Taxonomy standards.”
