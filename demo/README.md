# IAB Mapper Demo

This folder contains a small web demo (HTML/CSS/JS) and a FastAPI server that exposes the mapping endpoint.

## What it does
- Upload a CSV or JSON of IAB 2.x labels (optional `code`).
- Click “Map Now” to call `POST /api/map`.
- View results with filters (unmatched only, confidence threshold, search).
- Export results to CSV or JSON.
- Banner shows a quick summary.
- File picker shows the selected filename and row count after upload.

## Run locally
1. Create and activate a virtual environment:
```
python3 -m venv .venv
source .venv/bin/activate
```
2. Install the package and dev requirements:
```
pip install -e .
pip install -r requirements-dev.txt
```
3. Start the server:
```
uvicorn scripts.web_server:app --port 8002 --reload
```
4. Open the demo:
```
http://localhost:8002/
```

## API
- `POST /api/map`
- Request body:
```json
{
  "version_from": "2.x",
  "version_to": "3.0",
  "rows": [{"code":"1-4","label":"Sports"}],
  "options": {
    "confidence_min": 0.7
  }
}
```

## Samples

### Basic Samples
- Small:
  - `sample_2x_codes.csv`
  - `sample_2x_codes.json`
- Large (~100+ rows):
  - `sample_2x_codes_large.csv`
  - `sample_2x_codes_large.json`

### Official IAB Samples
- **Official samples** (recommended for testing):
  - `official_samples/sample_2x_codes_official.csv`
  - `official_samples/sample_2x_codes_official.json`
  - Based on actual IAB Content Taxonomy 2.2 data
  - Includes 60+ realistic categories and subcategories
  - See [official_samples/README.md](official_samples/README.md) for details

### Input Format
CSV must include a header and a `label` column. Optional: `code`, `channel`, `type`, `format`, `language`, `source`, `environment`.
