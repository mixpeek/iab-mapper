from rapidfuzz import fuzz, process
from .normalize import normalize
import numpy as np
from typing import List, Tuple
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except Exception:
    TfidfVectorizer = None

def build_alias_index(catalog, synonyms):
    idx = {}
    for row in catalog:
        for cand in {row["label"], *synonyms.get(row["label"], [])}:
            idx[normalize(cand)] = row["label"]
    return idx

def build_label_maps(iab3, synonyms_3x):
    label_to_id = {}
    labels = []
    for row in iab3:
        label_to_id[row["label"]] = row["id"]
        labels.append(row["label"])
        for syn in synonyms_3x.get(row["label"], []):
            # Map synonyms to the same ID and include them in the search space
            label_to_id[syn] = row["id"]
            labels.append(syn)
    return labels, label_to_id

def fuzzy_multi(query, choices, top_k=3, cut=0.90):
    if not query: return []
    hits = process.extract(query, choices, scorer=fuzz.WRatio, limit=top_k)
    out = []
    for lbl, score, _ in hits:
        s = score/100.0
        if s >= cut:
            out.append((lbl, s))
    return out


class TFIDFIndex:
    def __init__(self, texts: List[str]):
        if TfidfVectorizer is None:
            raise RuntimeError("scikit-learn is required for TF-IDF retrieval")
        self.texts = texts
        self.vectorizer = TfidfVectorizer(lowercase=True)
        self.mat = self.vectorizer.fit_transform(texts)

    def search(self, query: str, top_k: int = 3, cut: float = 0.90) -> List[Tuple[str, float]]:
        if not query:
            return []
        qv = self.vectorizer.transform([query])
        sims = cosine_similarity(qv, self.mat)[0]
        idxs = np.argsort(-sims)[:top_k]
        out: List[Tuple[str, float]] = []
        for idx in idxs:
            score = float(sims[idx])
            if score >= cut:
                out.append((self.texts[idx], score))
        return out


class BM25Index:
    def __init__(self, texts: List[str], k1: float = 1.5, b: float = 0.75):
        self.texts = texts
        self.k1 = k1
        self.b = b
        # Tokenize with same normalization pipeline
        self.docs = [normalize(t).split() for t in texts]
        self.N = len(self.docs)
        self.df = {}
        self.doc_len = np.array([len(d) for d in self.docs], dtype=np.float32)
        for d in self.docs:
            seen = set(d)
            for tok in seen:
                self.df[tok] = self.df.get(tok, 0) + 1
        self.avgdl = float(self.doc_len.mean()) if self.N else 0.0
        # Precompute IDF
        # Using BM25+ variant to avoid negative idf when df ~ N
        self.idf = {t: np.log(1 + (self.N - df + 0.5) / (df + 0.5)) for t, df in self.df.items()}

    def _score_doc(self, q_tokens: List[str], doc_idx: int) -> float:
        doc = self.docs[doc_idx]
        dl = self.doc_len[doc_idx]
        if dl == 0:
            return 0.0
        score = 0.0
        # term frequencies in doc
        tf = {}
        for tok in doc:
            tf[tok] = tf.get(tok, 0) + 1
        for tok in q_tokens:
            if tok not in tf or tok not in self.idf:
                continue
            f = tf[tok]
            idf = self.idf[tok]
            denom = f + self.k1 * (1 - self.b + self.b * (dl / (self.avgdl or 1.0)))
            score += idf * (f * (self.k1 + 1)) / (denom or 1.0)
        return score

    def search(self, query: str, top_k: int = 3, cut: float = 0.90) -> List[Tuple[str, float]]:
        if not query:
            return []
        q_tokens = normalize(query).split()
        if not q_tokens:
            return []
        scores = np.array([self._score_doc(q_tokens, i) for i in range(self.N)], dtype=np.float32)
        if scores.size == 0:
            return []
        max_score = float(scores.max()) or 1.0
        # Normalize to 0..1 for a comparable threshold behavior
        norm_scores = scores / max_score
        idxs = np.argsort(-scores)[:top_k]
        out: List[Tuple[str, float]] = []
        for idx in idxs:
            s = float(norm_scores[idx])
            if s >= cut:
                out.append((self.texts[idx], s))
        return out
