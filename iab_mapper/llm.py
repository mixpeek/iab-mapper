import json
from typing import List, Dict

try:
    import requests
except Exception:  # pragma: no cover - optional
    requests = None


SYSTEM_PROMPT = (
    "You are a taxonomy assistant. Given a content label and a list of candidate taxonomy nodes, "
    "rank the candidates by semantic fit to the label. Return a JSON array of candidate IDs in best-to-worst order."
)


def _build_prompt(query: str, candidates: List[Dict]) -> str:
    lines = [
        "Content label:",
        query.strip(),
        "",
        "Candidates (id | label):",
    ]
    for c in candidates:
        lines.append(f"{c['id']} | {c['label']}")
    lines.append("")
    lines.append(
        "Return only a JSON array of candidate ids in descending quality, e.g.: [\"3-5-2\",\"2-3-18\"]."
    )
    return "\n".join(lines)


def rerank_candidates(query: str, candidates: List[Dict], host: str, model: str) -> List[Dict]:
    """Reorder candidates using a local Ollama model. Fail-soft if unavailable."""
    if requests is None or not candidates:
        return candidates

    url = host.rstrip("/") + "/api/chat"
    prompt = _build_prompt(query, candidates)
    try:
        resp = requests.post(
            url,
            timeout=20,
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content = data.get("message", {}).get("content") or ""
        # best-effort JSON extraction
        start = content.find("[")
        end = content.find("]", start)
        order = []
        if start != -1 and end != -1:
            try:
                order = json.loads(content[start : end + 1])
            except Exception:
                order = []
        if not order:
            return candidates
        # Map to a dict for ordering
        id_to_item = {c["id"]: c for c in candidates}
        ranked = [id_to_item[i] for i in order if i in id_to_item]
        # append any missing
        seen = set(order)
        for c in candidates:
            if c["id"] not in seen:
                ranked.append(c)
        return ranked
    except Exception:
        return candidates


