from sklearn.neighbors import NearestNeighbors
try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
except Exception:
    TfidfVectorizer = None

class EmbIndex:
    def __init__(self, texts, model_name="all-MiniLM-L6-v2"):
        self.texts = texts
        self.nn = NearestNeighbors(metric="cosine", n_neighbors=10)
        self.mode = "st"
        if model_name == "tfidf":
            if TfidfVectorizer is None:
                raise RuntimeError("scikit-learn is required for TF-IDF index")
            self.mode = "tfidf"
            self.vectorizer = TfidfVectorizer(lowercase=True)
            self.emb = self.vectorizer.fit_transform(texts)
            self.nn.fit(self.emb)
        else:
            if SentenceTransformer is None:
                raise RuntimeError("Install extras for embeddings or use --emb-model tfidf")
            self.model = SentenceTransformer(model_name)
            self.emb = self.model.encode(texts, batch_size=64, normalize_embeddings=True, show_progress_bar=False)
            self.nn.fit(self.emb)

    def search(self, query: str, top_k=5):
        top_k = max(1, min(top_k, len(self.texts)))
        if self.mode == "tfidf":
            q = self.vectorizer.transform([query])
        else:
            q = self.model.encode([query], normalize_embeddings=True)
        dists, idxs = self.nn.kneighbors(q, n_neighbors=top_k)
        sims = 1 - dists[0]
        return list(zip(idxs[0].tolist(), sims.tolist()))
