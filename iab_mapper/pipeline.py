from dataclasses import dataclass
from .io_utils import load_json
from .normalize import normalize
from . import matching
from .embeddings import EmbIndex
from typing import Optional, Dict, List, Any
try:
    from . import llm as llm_mod
except Exception:
    llm_mod = None

@dataclass
class MapConfig:
    fuzzy_cut: float = 0.92
    fuzzy_method: str = "rapidfuzz"  # rapidfuzz|tfidf|bm25|hybrid
    use_embeddings: bool = False
    emb_model: str = "tfidf"  # default lightweight for demo; switch to all-MiniLM-L6-v2 if installed
    emb_cut: float = 0.80
    max_topics: int = 3
    drop_scd: bool = False
    # OpenRTB cattax value (string per spec enumeration)
    cattax: str = "2"
    # Optional overrides file (JSON). Each item: {"code": str|null, "label": str|null, "ids": [str]}
    overrides_path: Optional[str] = None
    # LLM re-ranking (optional, local via Ollama)
    use_llm: bool = False
    llm_model: str = "llama3.1:8b"
    llm_host: str = "http://localhost:11434"

class Mapper:
    def __init__(self, cfg: MapConfig, data_dir: str):
        self.cfg = cfg
        self.iab2 = load_json(f"{data_dir}/iab_2x.json")
        self.iab3 = load_json(f"{data_dir}/iab_3x.json")
        # Synonyms are optional
        try:
            self.syn2 = load_json(f"{data_dir}/synonyms_2x.json")
        except Exception:
            self.syn2 = {}
        try:
            self.syn3 = load_json(f"{data_dir}/synonyms_3x.json")
        except Exception:
            self.syn3 = {}
        self.alias_idx = matching.build_alias_index(self.iab2, self.syn2)
        self.labels3, self.label_to_id = matching.build_label_maps(self.iab3, self.syn3)
        self.id_to_row = {r["id"]: r for r in self.iab3}
        self.emb: Optional[EmbIndex] = EmbIndex(self.labels3, self.cfg.emb_model) if self.cfg.use_embeddings else None
        # Build optional alternative retrievers
        self.retriever = None
        if self.cfg.fuzzy_method == "tfidf":
            self.retriever = matching.TFIDFIndex(self.labels3)
        elif self.cfg.fuzzy_method == "bm25":
            self.retriever = matching.BM25Index(self.labels3)

        # Load vector catalogs if present
        self.vectors: Dict[str, Dict[str, str]] = {
            "channel": self._try_load(f"{data_dir}/vectors_channel.json"),
            "type": self._try_load(f"{data_dir}/vectors_type.json"),
            "format": self._try_load(f"{data_dir}/vectors_format.json"),
            "language": self._try_load(f"{data_dir}/vectors_language.json"),
            "source": self._try_load(f"{data_dir}/vectors_source.json"),
            "environment": self._try_load(f"{data_dir}/vectors_environment.json"),
        }

        # Load optional overrides
        self.overrides = []  # type: List[Dict[str, Any]]
        if self.cfg.overrides_path:
            try:
                self.overrides = load_json(self.cfg.overrides_path)
            except Exception:
                self.overrides = []

    def map_topics(self, in_label: str):
        out = []
        q = self.alias_idx.get(normalize(in_label)) or in_label

        def add_hits(hits: List[tuple], source: str):
            for lbl, s in hits:
                id_ = self.label_to_id.get(lbl)
                if not id_:
                    continue
                if self.cfg.drop_scd and self.id_to_row[id_].get("scd"):
                    continue
                existing = next((x for x in out if x["id"] == id_), None)
                if existing:
                    if float(s) > float(existing.get("confidence", 0.0)):
                        existing["confidence"] = round(float(s), 3)
                        existing["source"] = source
                    continue
                out.append({
                    "id": id_,
                    "label": self.id_to_row[id_]["label"],
                    "confidence": round(float(s), 3),
                    "source": source,
                })

        # Embedding (semantic KNN) candidates first, if enabled
        if self.emb and self.cfg.use_embeddings:
            hits = self.emb.search(q, top_k=10) # Get more candidates to ensure good coverage
            emb_candidates = []
            for idx, sim in hits:
                if sim < self.cfg.emb_cut:
                    continue
                label = self.labels3[idx]
                id_ = self.label_to_id.get(label)
                if not id_:
                    continue
                if self.cfg.drop_scd and self.id_to_row[id_].get("scd"):
                    continue
                emb_candidates.append({
                    "id": id_,
                    "label": self.id_to_row[id_]["label"],
                    "confidence": round(float(sim), 3),
                    "source": "embed",
                })
            # Sort embedding candidates by confidence to prioritize strong semantic matches
            emb_candidates.sort(key=lambda x: float(x.get("confidence", 0.0)), reverse=True)
            for cand in emb_candidates:
                # Add embedding hits. If an ID already exists, only update if the embedding confidence is higher.
                existing = next((x for x in out if x["id"] == cand["id"]), None)
                if existing:
                    if cand["confidence"] > existing["confidence"]:
                        existing.update(cand) # Update with higher confidence embedding match
                else:
                    out.append(cand)


        if self.cfg.fuzzy_method == "rapidfuzz":
            fuzz_hits = matching.fuzzy_multi(q, self.labels3, top_k=max(5, self.cfg.max_topics), cut=self.cfg.fuzzy_cut)
            add_hits(fuzz_hits, "rapidfuzz")
        elif self.cfg.fuzzy_method in ("tfidf", "bm25"):
            fuzz_hits = self.retriever.search(q, top_k=max(5, self.cfg.max_topics), cut=self.cfg.fuzzy_cut)
            add_hits(fuzz_hits, self.cfg.fuzzy_method)
        elif self.cfg.fuzzy_method == "hybrid":
            selected = {"rapidfuzz", "tfidf", "bm25", "exact"}
            # Allow server to pass a subset via options.methods
            try:
                # Access dynamic methods list if present on cfg (injected by API layer)
                methods_list = getattr(self.cfg, "methods", None)
                if isinstance(methods_list, list) and methods_list:
                    selected = set([str(m) for m in methods_list])
            except Exception:
                pass
            # Exact label/path match approximation: use alias/normalized equality to labels
            if "exact" in selected:
                norm_q = normalize(q)
                for lbl in self.labels3:
                    if normalize(lbl) == norm_q:
                        # Explicitly set confidence to 1.0 for exact matches
                        add_hits([(lbl, 1.0)], "label_match")
            try:
                if "rapidfuzz" in selected:
                    rf_hits = matching.fuzzy_multi(q, self.labels3, top_k=max(5, self.cfg.max_topics), cut=self.cfg.fuzzy_cut)
                    add_hits(rf_hits, "rapidfuzz")
            except Exception:
                pass
            try:
                if "tfidf" in selected:
                    tf_idx = matching.TFIDFIndex(self.labels3)
                    tf_hits = tf_idx.search(q, top_k=max(5, self.cfg.max_topics), cut=self.cfg.fuzzy_cut)
                    add_hits(tf_hits, "tfidf")
            except Exception:
                pass
            try:
                if "bm25" in selected:
                    bm_idx = matching.BM25Index(self.labels3)
                    bm_hits = bm_idx.search(q, top_k=max(5, self.cfg.max_topics), cut=self.cfg.fuzzy_cut)
                    add_hits(bm_hits, "bm25")
            except Exception:
                pass


        # Optional LLM re-ranking (keeps same candidates, reorders by semantic fit)
        used_llm = False
        if self.cfg.use_llm and llm_mod is not None and len(out) > 1:
            try:
                initial_order_ids = [x["id"] for x in out] # Capture order before LLM
                out = llm_mod.rerank_candidates(q, out, host=self.cfg.llm_host, model=self.cfg.llm_model)
                final_order_ids = [x["id"] for x in out] # Capture order after LLM
                if initial_order_ids != final_order_ids: # Check if LLM actually re-ordered
                    used_llm = True
            except Exception:
                # Fail soft if LLM not available
                pass

        # Final trim to top-K
        if not used_llm:
            out.sort(key=lambda x: float(x.get("confidence", 0.0)), reverse=True)
        return out[: self.cfg.max_topics], used_llm # Return used_llm flag

    def _try_load(self, path: str) -> Dict[str, str]:
        try:
            data = load_json(path)
            # Expect a simple mapping of value -> id
            return {str(k): str(v) for k, v in data.items()}
        except Exception:
            return {}

    def _apply_overrides(self, in_code: Optional[str], in_label: str) -> Optional[List[Dict[str, Any]]]:
        if not self.overrides:
            return None
        norm_label = normalize(in_label)
        for rule in self.overrides:
            code_ok = (rule.get("code") is None) or (in_code and str(rule.get("code")) == str(in_code))
            label_ok = (rule.get("label") is None) or (normalize(str(rule.get("label"))) == norm_label)
            ids = rule.get("ids") or []
            if code_ok and label_ok and ids:
                out = []
                for id_ in ids:
                    if id_ in self.id_to_row:
                        out.append({
                            "id": id_,
                            "label": self.id_to_row[id_]["label"],
                            "confidence": 1.0,
                            "source": "override",
                        })
                return out or None
        return None

    def _map_vectors(self, rec: Dict[str, Any]) -> (Dict[str, str], List[str]):
        values: Dict[str, str] = {}
        ids: List[str] = []
        for dim, catalog in self.vectors.items():
            raw_val = rec.get(dim)
            if raw_val is None:
                continue
            val = str(raw_val).strip()
            if not val:
                continue
            id_ = catalog.get(val)
            if id_:
                values[dim] = val
                ids.append(id_)
        return values, ids

    def map_record(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        in_code = rec.get("code")
        in_label = rec.get("label") or ""

        # 1) Overrides first
        overrides_applied = self._apply_overrides(in_code, in_label)
        topics = overrides_applied
        used_llm_rerank = False
        if topics is None:
            topics, used_llm_rerank = self.map_topics(in_label) # Capture used_llm_rerank from map_topics
        else:
            # If overrides applied, LLM re-rank is not applicable for this record's top picks
            topics, _ = self.map_topics(in_label) # still run map_topics to get other candidates, but ignore its used_llm_rerank

        # Add SCD flag on topics
        for t in topics:
            t["scd"] = bool(self.id_to_row.get(t["id"], {}).get("scd"))

        topic_ids = [t["id"] for t in topics]
        topic_labels = [t["label"] for t in topics]
        topic_conf = [float(t.get("confidence", 0.0)) for t in topics]
        topic_srcs = [str(t.get("source", "")) for t in topics]
        topic_scd = [bool(t.get("scd", False)) for t in topics]

        # 2) Map vectors from record optional fields
        vectors_vals, vector_ids = self._map_vectors(rec)

        # 3) Compose outputs
        out_ids = []  # maintain order: topics then vectors, unique
        seen = set()
        for id_ in topic_ids + vector_ids:
            if id_ not in seen:
                out_ids.append(id_)
                seen.add(id_)

        vast = ",".join([f'"{i}"' for i in out_ids])
        openrtb = {"content": {"cat": out_ids, "cattax": str(self.cfg.cattax)}}

        return {
            "in_code": in_code,
            "in_label": in_label,
            "out_ids": out_ids,
            "out_labels": topic_labels,
            "topic_ids": topic_ids,
            "topic_confidence": topic_conf,
            "topic_sources": topic_srcs,
            "topic_scd": topic_scd,
            "vectors": vectors_vals,
            "cattax": str(self.cfg.cattax),
            "openrtb": openrtb,
            "vast_contentcat": vast,
            "topics": topics,
            "llm_reranked": used_llm_rerank, # Add LLM reranked flag to final output
        }
