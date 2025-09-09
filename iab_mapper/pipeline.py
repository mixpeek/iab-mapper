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
    fuzzy_method: str = "rapidfuzz"  # rapidfuzz|tfidf|bm25
    use_embeddings: bool = False
    emb_model: str = "all-MiniLM-L6-v2"
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
        if self.cfg.fuzzy_method == "rapidfuzz":
            fuzz_hits = matching.fuzzy_multi(q, self.labels3, top_k=self.cfg.max_topics, cut=self.cfg.fuzzy_cut)
        else:
            fuzz_hits = self.retriever.search(q, top_k=self.cfg.max_topics, cut=self.cfg.fuzzy_cut)
        for lbl, s in fuzz_hits:
            id_ = self.label_to_id.get(lbl)
            if not id_:
                continue
            if any(x["id"] == id_ for x in out):
                continue
            if not self.cfg.drop_scd or not self.id_to_row[id_].get("scd"):
                out.append({"id": id_, "label": self.id_to_row[id_]["label"], "confidence": round(float(s),3), "source": self.cfg.fuzzy_method})
        if self.emb and len(out) < self.cfg.max_topics:
            hits = self.emb.search(q, top_k=10)
            for idx, sim in hits:
                if sim < self.cfg.emb_cut: continue
                label = self.labels3[idx]
                id_ = self.label_to_id.get(label)
                if not id_ or any(x["id"]==id_ for x in out): continue
                if not self.cfg.drop_scd or not self.id_to_row[id_].get("scd"):
                    out.append({"id": id_, "label": self.id_to_row[id_]["label"], "confidence": round(float(sim),3), "source":"embed"})
                if len(out) >= self.cfg.max_topics: break
        # Optional LLM re-ranking (keeps same candidates, reorders by semantic fit)
        if self.cfg.use_llm and llm_mod is not None and len(out) > 1:
            try:
                out = llm_mod.rerank_candidates(q, out, host=self.cfg.llm_host, model=self.cfg.llm_model)
            except Exception:
                # Fail soft if LLM not available
                pass
        return out[:self.cfg.max_topics]

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
        topics = self._apply_overrides(in_code, in_label)
        if topics is None:
            topics = self.map_topics(in_label)

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
        }
