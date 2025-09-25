# Official IAB Sample Datasets

This directory contains sample datasets based on the official IAB Content Taxonomy from the [IAB Tech Lab Taxonomies repository](https://github.com/InteractiveAdvertisingBureau/Taxonomies).

## Sample Files

### `sample_2x_codes_official.csv` & `sample_2x_codes_official.json`
- **Size:** 60+ records
- **Content:** Mix of official IAB 2.x codes and free-text labels
- **Purpose:** Comprehensive testing of the mapper with realistic data
- **Features:** Includes vector attributes (channel, type, format, language, source, environment)

### Key Features of Official Samples

1. **Official IAB 2.x Codes:** Uses actual category codes from IAB Content Taxonomy 2.2
2. **Realistic Categories:** Covers all major IAB categories (Arts & Entertainment, Automotive, Business, etc.)
3. **Subcategories:** Includes detailed subcategories (e.g., Auto Parts, Electric Vehicle, Luxury)
4. **Free-text Examples:** Contains challenging free-text labels that require semantic matching
5. **Vector Attributes:** Demonstrates the full range of orthogonal attributes supported

## Usage

### Command Line
```bash
# Test with official sample data
iab-mapper demo/official_samples/sample_2x_codes_official.csv -o mapped_official.json

# Test with embeddings enabled
iab-mapper demo/official_samples/sample_2x_codes_official.csv -o mapped_official.json --use-embeddings

# Test with different fuzzy methods
iab-mapper demo/official_samples/sample_2x_codes_official.csv -o mapped_bm25.json --fuzzy-method bm25
```

### Python API
```python
import json
from iab_mapper.pipeline import Mapper, MapConfig
import iab_mapper as pkg

# Load official sample data
with open('demo/official_samples/sample_2x_codes_official.json', 'r') as f:
    sample_data = json.load(f)

# Configure mapper
cfg = MapConfig(
    fuzzy_method="bm25",
    fuzzy_cut=0.92,
    use_embeddings=True,
    max_topics=3
)

data_dir = Path(pkg.__file__).parent / "data"
mapper = Mapper(cfg, str(data_dir))

# Map all samples
results = [mapper.map_record(record) for record in sample_data]
```

## Expected Results

The official sample data should demonstrate:

1. **High Accuracy:** Most official IAB codes should map with high confidence
2. **Semantic Matching:** Free-text labels should be matched using embeddings
3. **Vector Attributes:** All vector attributes should be preserved and mapped
4. **SCD Awareness:** Any sensitive content should be flagged appropriately
5. **OpenRTB Compliance:** Output should be ready for OpenRTB/VAST integration

## Data Source

These samples are based on the official IAB Content Taxonomy files:
- **Content Taxonomy 2.2:** [IAB Tech Lab Repository](https://github.com/InteractiveAdvertisingBureau/Taxonomies/tree/main/Content%20Taxonomies)
- **Content Taxonomy 3.1:** [IAB Tech Lab Repository](https://github.com/InteractiveAdvertisingBureau/Taxonomies/tree/main/Content%20Taxonomies)

## Contributing

To update these samples with the latest IAB taxonomy data:

1. Check the [IAB Tech Lab Taxonomies repository](https://github.com/InteractiveAdvertisingBureau/Taxonomies) for updates
2. Run the fetch script: `python scripts/fetch_official_taxonomies.py`
3. Test the updated samples with the mapper
4. Update this README if needed

## License

These sample datasets are derived from IAB Tech Lab taxonomies and are subject to the same licensing terms as the original IAB materials.
