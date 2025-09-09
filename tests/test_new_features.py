from pathlib import Path
import json

from iab_mapper.pipeline import Mapper, MapConfig


def data_dir() -> Path:
    import iab_mapper as pkg
    return Path(pkg.__file__).parent / "data"


def test_vectors_and_cattax_in_outputs():
    cfg = MapConfig(fuzzy_method="bm25", fuzzy_cut=0.1, max_topics=3, cattax="2")
    m = Mapper(cfg, str(data_dir()))
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
    out = m.map_record(rec)
    assert out["cattax"] == "2"
    assert out["openrtb"]["content"]["cattax"] == "2"
    assert "out_ids" in out and isinstance(out["out_ids"], list)
    # vectors should be present and non-empty
    assert out["vectors"].get("channel") == "editorial"
    assert any(i for i in out["out_ids"] if i != out["topic_ids"][0])


def test_overrides_precedence(tmp_path: Path):
    overrides = [
        {"code": "1-4", "label": None, "ids": ["2-3-18"]},
    ]
    ov_path = tmp_path / "overrides.json"
    ov_path.write_text(json.dumps(overrides), encoding="utf-8")

    cfg = MapConfig(fuzzy_method="rapidfuzz", fuzzy_cut=0.95, max_topics=3, overrides_path=str(ov_path))
    m = Mapper(cfg, str(data_dir()))
    out = m.map_record({"code": "1-4", "label": "Sports"})
    assert out["topic_ids"] == ["2-3-18"]
    assert out["topics"][0]["source"] == "override"


def test_drop_scd_excludes_nodes():
    # In the stub data, "Food & Drink > Alcoholic Beverages" is scd=true
    cfg = MapConfig(fuzzy_method="bm25", fuzzy_cut=0.1, max_topics=3, drop_scd=True)
    m = Mapper(cfg, str(data_dir()))
    out = m.map_record({"code": "2-12", "label": "Food & Drink"})
    assert "3-5-8" not in out["topic_ids"]


def test_cli_unmapped_and_cattax(tmp_path: Path):
    from typer.testing import CliRunner
    from iab_mapper.cli import app
    runner = CliRunner()

    # Create an input with an unmapped label
    input_file = tmp_path / "input.csv"
    input_file.write_text("label\nUnknown Label That Wont Match\n", encoding="utf-8")
    out_path = tmp_path / "mapped.json"
    misses_path = tmp_path / "misses.json"

    res = runner.invoke(app, [str(input_file), "-o", str(out_path), "--cattax", "2", "--unmapped-out", str(misses_path)])
    assert res.exit_code == 0
    data = json.loads(out_path.read_text())
    assert isinstance(data, list)
    misses = json.loads(misses_path.read_text())
    assert len(misses) == 1

