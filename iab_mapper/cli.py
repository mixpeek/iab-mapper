import typer, pandas as pd, json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from iab_mapper.pipeline import Mapper, MapConfig
from iab_mapper.updater import update_catalogs

app = typer.Typer(add_completion=False)
con = Console()

@app.command()
def run(
    input_path: Path = typer.Argument(..., help="CSV/JSON with 'label' and optional 'code' + vector cols"),
    out: Path = typer.Option(..., "--out","-o", help="Output file (.csv or .json)"),
    data_dir: Path = typer.Option(Path(__file__).parent / "data", help="Data dir"),
    fuzzy_cut: float = typer.Option(0.92),
    fuzzy_method: str = typer.Option("rapidfuzz", help="rapidfuzz|tfidf|bm25"),
    use_embeddings: bool = typer.Option(False),
    emb_model: str = typer.Option("all-MiniLM-L6-v2"),
    emb_cut: float = typer.Option(0.80),
    max_topics: int = typer.Option(3),
    drop_scd: bool = typer.Option(False),
    # OpenRTB cattax and overrides
    cattax: str = typer.Option("2", help="OpenRTB content.cattax enumeration value for Content Taxonomy"),
    overrides: Path = typer.Option(None, help="JSON file with overrides [{code?,label?,ids[]}]") ,
    # Optional LLM rerank
    use_llm: bool = typer.Option(False, help="Use local LLM (Ollama) for re-ranking"),
    llm_model: str = typer.Option("llama3.1:8b"),
    llm_host: str = typer.Option("http://localhost:11434"),
    # Unmapped report
    unmapped_out: Path = typer.Option(None, help="Optional JSON file to write unmapped/empty-topic rows"),
):
    cfg = MapConfig(
        fuzzy_cut=fuzzy_cut,
        fuzzy_method=fuzzy_method,
        use_embeddings=use_embeddings,
        emb_model=emb_model,
        emb_cut=emb_cut,
        max_topics=max_topics,
        drop_scd=drop_scd,
        cattax=cattax,
        overrides_path=str(overrides) if overrides else None,
        use_llm=use_llm,
        llm_model=llm_model,
        llm_host=llm_host,
    )
    mapper = Mapper(cfg, str(data_dir))

    if input_path.suffix.lower()==".csv": df = pd.read_csv(input_path)
    elif input_path.suffix.lower()==".json": df = pd.read_json(input_path)
    else: raise typer.BadParameter("Input must be .csv or .json")

    if "label" not in df.columns: raise typer.BadParameter("Need 'label' col")
    if "code" not in df.columns: df["code"]=None

    rows = []
    unmapped = []
    for rec in df.to_dict(orient="records"):
        out_rec = mapper.map_record(rec)
        rows.append(out_rec)
        if len(out_rec.get("topic_ids", [])) == 0:
            unmapped.append({"in_code": out_rec.get("in_code"), "in_label": out_rec.get("in_label")})

    out_df = pd.DataFrame(rows)
    table = Table()
    for col in ["in_code","in_label","out_ids","cattax"]: table.add_column(col)
    for _, r in out_df.iterrows():
        table.add_row(str(r["in_code"]), r["in_label"], json.dumps(r.get("out_ids", [])), str(r.get("cattax")))
    con.print(table)

    if out.suffix.lower()==".csv":
        out_df.to_csv(out,index=False)
    elif out.suffix.lower()==".json":
        out_df.to_json(out,orient="records")
    else:
        raise typer.BadParameter("Output must be .csv or .json")
    con.print(f"Saved → {out}")
    if unmapped_out and unmapped:
        Path(unmapped_out).write_text(json.dumps(unmapped, ensure_ascii=False), encoding="utf-8")
        con.print(f"Unmapped → {unmapped_out} ({len(unmapped)})")
if __name__=="__main__": app()


@app.command(name="update-catalogs")
def update_catalogs_cmd(
    data_dir: Path = typer.Option(Path(__file__).parent / "data", help="Data dir to write catalogs"),
    major3: int = typer.Option(3, help="Major version to pick for Content Taxonomy 3.x (e.g., 3)"),
    major2: int = typer.Option(2, help="Major version to pick for Content Taxonomy 2.x (e.g., 2)"),
    exact3: str = typer.Option(None, help="Exact filename substring for 3.x (e.g., '3.1')"),
    exact2: str = typer.Option(None, help="Exact filename substring for 2.x (e.g., '2.2')"),
    token: str = typer.Option(None, help="GitHub token (overrides env GITHUB_TOKEN)"),
):
    """Fetch latest IAB catalogs from IAB GitHub and normalize into JSON."""
    update_catalogs(str(data_dir), major3=major3, major2=major2, exact3=exact3, exact2=exact2, token=token)
    con.print(f"Updated catalogs in {data_dir}")
