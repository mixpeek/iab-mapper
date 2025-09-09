import re, unicodedata
PUNCT_RE = re.compile(r"[^\w\s&/+-]")
WS_RE = re.compile(r"\s+")
def normalize(text: str) -> str:
    t = unicodedata.normalize("NFKC", text or "")
    t = t.lower().strip()
    t = t.replace("&"," and ")
    t = t.replace("-", " ")
    t = PUNCT_RE.sub(" ", t)
    t = WS_RE.sub(" ", t)
    return t.strip()
