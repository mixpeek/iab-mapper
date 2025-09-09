import orjson, pandas as pd
from pathlib import Path

def load_json(path): return orjson.loads(Path(path).read_bytes())
def save_csv(df, path): df.to_csv(path, index=False)
def save_json(df, path): Path(path).write_bytes(orjson.dumps(df.to_dict(orient="records")))
