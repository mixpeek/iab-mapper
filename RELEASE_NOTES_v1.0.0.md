# IAB Mapper v1.0.0 Release Notes

## 🎉 Major Release: IAB Mapper v1.0.0

This is the first major release of the IAB Mapper, marking its readiness for production use and contribution to the IAB Tech Lab community.

## 🚀 What's New

### Official IAB Tech Lab Contribution
- **Formal donation** to IAB Tech Lab under BSD 2-Clause license
- **RF RAND mode** compliance for royalty-free usage
- **Industry-ready** for IAB member adoption

### Enhanced Sample Datasets
- **Official IAB samples** based on Content Taxonomy 2.2
- **60+ realistic categories** including subcategories
- **Vector attributes** examples (channel, type, format, language, source, environment)
- **Free-text challenges** for semantic matching testing

### Improved Documentation
- **Enablement-ready README** with 5-minute quickstart
- **Comprehensive CONTRIBUTING.md** with development guidelines
- **Enhanced issue templates** for better bug reports and feature requests
- **Official samples documentation** with usage examples

### License Update
- **BSD 2-Clause License** (previously MIT) for IAB Tech Lab compatibility
- **Open source compliance** with industry standards

## 🔧 Technical Features

### Core Functionality
- **Deterministic matching** → fuzzy matching → optional semantic enhancement
- **Local-first processing** with no external API dependencies
- **OpenRTB/VAST compatibility** with proper IAB 3.0 ID output
- **SCD awareness** for sensitive content handling
- **Vector attributes support** for orthogonal taxonomy dimensions

### Matching Methods
- **RapidFuzz** (default) for fast fuzzy string matching
- **BM25** and **TF-IDF** alternatives for different use cases
- **Sentence-Transformers** embeddings for semantic matching
- **Configurable thresholds** for precision/recall tuning

### Output Formats
- **CSV and JSON** export options
- **OpenRTB content.cat** format with configurable cattax
- **VAST CONTENTCAT** string format
- **Confidence scores** and source attribution
- **Audit trails** for unmapped items

## 📊 Performance & Reliability

### Tested Scenarios
- **Official IAB categories** with high accuracy mapping
- **Free-text labels** with semantic matching
- **Large datasets** (100+ items) with consistent performance
- **Edge cases** and error handling

### Quality Assurance
- **Comprehensive test suite** with pytest
- **Sample data validation** against official taxonomies
- **Cross-platform compatibility** (macOS, Linux, Windows)
- **Python 3.9+ support** with modern dependencies

## 🎯 Use Cases

### Ad Tech Industry
- **Contextual targeting** migration from 2.x to 3.0
- **Brand safety** with SCD-aware mapping
- **OpenRTB integration** for programmatic advertising
- **CTV and video** content classification

### Content Platforms
- **Content categorization** for recommendation systems
- **Search and discovery** with semantic matching
- **Analytics and reporting** with standardized taxonomies
- **Multi-format support** (text, video, audio, image)

## 📦 Installation & Usage

### Quick Start
```bash
# Install from PyPI
pip install iab-mapper

# Basic usage
iab-mapper sample_data.csv -o mapped_output.json

# With embeddings
iab-mapper sample_data.csv -o mapped_output.json --use-embeddings
```

### Python API
```python
from iab_mapper.pipeline import Mapper, MapConfig
import iab_mapper as pkg

cfg = MapConfig(fuzzy_method="bm25", use_embeddings=True)
data_dir = Path(pkg.__file__).parent / "data"
mapper = Mapper(cfg, str(data_dir))

result = mapper.map_record({"label": "Sports highlights"})
```

## 🔗 Resources

- **Repository:** https://github.com/mixpeek/iab-mapper
- **Documentation:** https://mixpeek.com/tools/iab-taxonomy-mapper
- **IAB Tech Lab:** https://github.com/InteractiveAdvertisingBureau/Taxonomies
- **Issues:** https://github.com/mixpeek/iab-mapper/issues

## 🤝 Contributing

We welcome contributions from the IAB community! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
git clone https://github.com/mixpeek/iab-mapper.git
cd iab-mapper
python -m venv .venv && source .venv/bin/activate
pip install -e ".[emb]" && pip install -r requirements-dev.txt
pytest -q
```

## 📞 Support

- **GitHub Issues:** For bug reports and feature requests
- **Documentation:** Comprehensive guides and examples
- **Community:** IAB Tech Lab member discussions
- **Enterprise:** Contact Mixpeek for custom integrations

## 🎯 Future Roadmap

### Multimodal Classification
- **Video content** analysis and classification
- **Audio/podcast** taxonomy mapping
- **Image recognition** for visual content
- **Cross-modal** content understanding

### Industry Integration
- **IAB member enablement** sessions
- **Migration tooling** for large-scale deployments
- **Performance optimization** for enterprise use
- **API integrations** with major ad tech platforms

---

**Ready for IAB Tech Lab contribution and industry adoption!** 🚀

*This release represents a significant milestone in making IAB 3.0 migration accessible to the entire ad tech ecosystem.*
