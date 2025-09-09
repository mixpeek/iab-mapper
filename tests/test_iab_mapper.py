from pathlib import Path
import json
import os

import pytest

from iab_mapper.normalize import normalize
from iab_mapper import matching
from iab_mapper.embeddings import EmbIndex
from iab_mapper.pipeline import Mapper, MapConfig


def data_dir() -> Path:
    # Resolve installed package data directory
    import iab_mapper as pkg
    return Path(pkg.__file__).parent / "data"


def test_normalize_basic():
    assert normalize(" Food & Drink !! ") == "food and drink"
    assert normalize("Cooking-how/to") == "cooking how/to"


def test_matching_fuzzy():
    iab3 = json.loads((data_dir() / "iab_3x.json").read_text())
    labels, label_to_id = matching.build_label_maps(iab3, {})
    hits = matching.fuzzy_multi("Sports", labels, top_k=3, cut=0.1)
    assert any(lbl.startswith("Sports") for lbl, _ in hits)


def test_tfidf_and_bm25_indices():
    iab3 = json.loads((data_dir() / "iab_3x.json").read_text())
    labels = [r["label"] for r in iab3]
    tfidf = matching.TFIDFIndex(labels)
    bm25 = matching.BM25Index(labels)
    hits_tfidf = tfidf.search("Food & Drink", top_k=3, cut=0.1)
    hits_bm25 = bm25.search("Food & Drink", top_k=3, cut=0.1)
    assert hits_tfidf and hits_bm25
    assert any("Food & Drink" in lbl for lbl, _ in hits_tfidf + hits_bm25)


def test_embeddings_tfidf_backend():
    iab3 = json.loads((data_dir() / "iab_3x.json").read_text())
    labels = [r["label"] for r in iab3]
    emb = EmbIndex(labels, model_name="tfidf")
    hits = emb.search("Cooking how-to", top_k=5)
    assert hits and hits[0][1] > 0


def test_pipeline_rapidfuzz():
    cfg = MapConfig(fuzzy_method="rapidfuzz", fuzzy_cut=0.1, max_topics=3)
    m = Mapper(cfg, str(data_dir()))
    out = m.map_topics("Sports")
    assert isinstance(out, list)


def test_pipeline_tfidf():
    cfg = MapConfig(fuzzy_method="tfidf", fuzzy_cut=0.1, max_topics=3)
    m = Mapper(cfg, str(data_dir()))
    out = m.map_topics("Food & Drink")
    assert out and any("Food & Drink" in x["label"] for x in out)


def test_pipeline_bm25():
    cfg = MapConfig(fuzzy_method="bm25", fuzzy_cut=0.1, max_topics=3)
    m = Mapper(cfg, str(data_dir()))
    out = m.map_topics("Cooking how-to")
    assert out and any("Cooking" in x["label"] for x in out)


def test_pipeline_embeddings_tfidf_augments():
    # Make fuzzy strict to force embed augmentation
    cfg = MapConfig(fuzzy_method="rapidfuzz", fuzzy_cut=0.95, use_embeddings=True, emb_model="tfidf", emb_cut=0.1)
    m = Mapper(cfg, str(data_dir()))
    out = m.map_topics("Cooking how-to")
    assert out and any(x["source"] == "embed" for x in out)


def test_cli_invocation(tmp_path: Path):
    from typer.testing import CliRunner
    from iab_mapper.cli import app

    input_csv = Path(__file__).parents[1] / "sample_2x_codes.csv"
    out_path = tmp_path / "mapped.json"
    runner = CliRunner()
    result = runner.invoke(app, [str(input_csv), "-o", str(out_path), "--fuzzy-method", "bm25", "--fuzzy-cut", "0.1"])
    assert result.exit_code == 0
    assert out_path.exists()
    data = json.loads(out_path.read_text())
    assert isinstance(data, list)


@pytest.mark.integration
def test_llm_rerank_with_ollama_if_available():
    # Skip if Ollama not running or model not present
    import requests
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        r.raise_for_status()
        models = [m.get("name") for m in r.json().get("models", [])]
    except Exception:
        pytest.skip("Ollama not available")
    if "llama2:latest" not in models:
        pytest.skip("llama2:latest not present")

    # Use rerank to reorder two candidates
    from iab_mapper import llm
    cands = [
        {"id": "3-5-8", "label": "Food & Drink > Alcoholic Beverages", "confidence": 0.5, "source": "bm25"},
        {"id": "3-5-2", "label": "Food & Drink > Cooking", "confidence": 0.4, "source": "bm25"},
    ]
    ranked = llm.rerank_candidates("Cooking how-to", cands, host="http://localhost:11434", model="llama2:latest")
    assert {c["id"] for c in ranked} == {c["id"] for c in cands}

