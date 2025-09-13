from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from iab_mapper.pipeline import Mapper, MapConfig
import iab_mapper as pkg


class MapRow(BaseModel):
    code: Optional[str] = None
    label: Optional[str] = None
    channel: Optional[str] = None
    type: Optional[str] = None
    format: Optional[str] = None
    language: Optional[str] = None
    source: Optional[str] = None
    environment: Optional[str] = None


class MapOptions(BaseModel):
    confidence_min: float = Field(0.7, ge=0.0, le=1.0)
    fuzzy_method: str = "rapidfuzz"  # rapidfuzz|tfidf|bm25
    fuzzy_cut: float = Field(0.92, ge=0.0, le=1.0)
    methods: Optional[List[str]] = None  # for hybrid selection: ["exact","tfidf","bm25","rapidfuzz"]
    use_embeddings: bool = False
    emb_model: str = "all-MiniLM-L6-v2"
    emb_cut: float = Field(0.80, ge=0.0, le=1.0)
    max_topics: int = 3
    drop_scd: bool = False
    cattax: str = "2"
    overrides_path: Optional[str] = None
    # LLM re-rank
    use_llm: bool = False
    llm_model: Optional[str] = "llama3.1:8b"
    llm_host: Optional[str] = "http://localhost:11434"


class MapRequest(BaseModel):
    version_from: str = "2.x"
    version_to: str = "3.0"
    rows: List[MapRow]
    options: MapOptions = MapOptions()


class MapResponseRow(BaseModel):
    code_2x: Optional[str]
    label_2x: Optional[str]
    code_3x: Optional[str]
    label_3x: Optional[str]
    confidence: float
    method: Optional[str]
    notes: Optional[str] = None
    llm_reranked: bool = False # New field


class MapResponse(BaseModel):
    summary: Dict[str, Any]
    rows: List[MapResponseRow]


def create_app() -> FastAPI:
    api = FastAPI(title="IAB Mapper API")

    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Prepare mapper with packaged data dir
    data_dir = Path(pkg.__file__).parent / "data"

    @api.post("/api/map", response_model=MapResponse)
    def post_map(req: MapRequest):
        try:
            # Inject methods list into config for hybrid selection
            cfg = MapConfig(
                fuzzy_cut=req.options.fuzzy_cut,
                fuzzy_method=req.options.fuzzy_method,
                use_embeddings=req.options.use_embeddings,
                emb_model=req.options.emb_model,
                emb_cut=req.options.emb_cut,
                max_topics=req.options.max_topics,
                drop_scd=req.options.drop_scd,
                cattax=req.options.cattax,
                overrides_path=req.options.overrides_path,
                use_llm=req.options.use_llm,
                llm_model=req.options.llm_model or "llama3.1:8b",
                llm_host=req.options.llm_host or "http://localhost:11434",
            )
            # attach dynamic 'methods' attribute if provided
            if req.options.methods is not None:
                setattr(cfg, "methods", req.options.methods)
            mapper = Mapper(cfg, str(data_dir))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize mapper: {e}") from e

        out_rows: List[MapResponseRow] = []
        mapped = 0

        for r in req.rows:
            in_rec = {
                "code": r.code,
                "label": r.label or "",
                "channel": r.channel,
                "type": r.type,
                "format": r.format,
                "language": r.language,
                "source": r.source,
                "environment": r.environment,
            }
            res = mapper.map_record(in_rec)

            # Pick top topic above threshold if present
            top_id: Optional[str] = None
            top_label: Optional[str] = None
            top_conf: float = 0.0
            top_method: Optional[str] = None
            if res.get("topics"):
                cand = res["topics"][0]
                if float(cand.get("confidence", 0.0)) >= float(req.options.confidence_min):
                    top_id = str(cand.get("id"))
                    top_label = str(cand.get("label"))
                    top_conf = float(cand.get("confidence", 0.0))
                    top_method = str(cand.get("source")) if cand.get("source") else None

            if top_id:
                mapped += 1

            out_rows.append(
                MapResponseRow(
                    code_2x=r.code,
                    label_2x=r.label,
                    code_3x=top_id,
                    label_3x=top_label,
                    confidence=round(top_conf, 3),
                    method=top_method,
                    notes=None,
                    llm_reranked=res.get("llm_reranked", False), # Populate new field
                )
            )

        total = len(req.rows)
        summary = {
            "total": total,
            "mapped": mapped,
            "unmatched": total - mapped,
            "threshold": req.options.confidence_min,
        }

        return MapResponse(summary=summary, rows=out_rows)

    # Serve static demo at root path
    static_dir = Path(__file__).resolve().parent.parent / "demo"
    static_dir.mkdir(parents=True, exist_ok=True)
    # Legacy path redirect
    @api.get("/iab-mapper")
    def legacy_redirect():
        return RedirectResponse(url="/")

    api.mount("/", StaticFiles(directory=str(static_dir), html=True), name="root")

    return api


app = create_app()

# uvicorn entry:
# uvicorn scripts.web_server:app --reload --port 8000


