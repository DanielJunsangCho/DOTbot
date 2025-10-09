# DOTbot - Unified Web Scraping and AI Behavior Analysis

DOTbot is a comprehensive web scraping and analysis system that combines general-purpose data extraction with specialized AI behavior detection capabilities. It integrates two previously separate systems into a unified, powerful platform.

## 🌟 Features

### Core Capabilities
- **Unified Web Scraping**: Extract structured data from any website
- **AI Behavior Analysis**: Detect and analyze concerning AI behaviors in content
- **Adaptive Scraping**: Automatically selects optimal scraping strategy (HTTP or browser-based)
- **Multiple Export Formats**: CSV, JSON, database storage
- **Quality Evaluation**: Built-in evaluation and metrics for data quality
- **Batch Processing**: Handle multiple URLs efficiently

### Advanced Features
- **LangGraph Workflows**: Sophisticated processing pipelines
- **Browser Automation**: Handle JavaScript-heavy and dynamic sites
- **Intelligent Routing**: Auto-select scraping method based on URL characteristics
- **Comprehensive Evaluation**: Multiple evaluation metrics and quality assessment
- **Session Management**: Track operations and maintain state

## 🏗️ Architecture

```
DOTbot/
├── core/                    # Shared infrastructure
│   ├── schemas.py          # Unified data models
│   ├── config.py           # Configuration management
│   └── storage.py          # Storage interfaces
│
├── scraping/               # Scraping capabilities
│   ├── basic_scraper.py    # HTTP-based scraping
│   ├── browser_scraper.py  # Browser automation
│   ├── scraper_factory.py  # Scraper selection
│   └── tools/              # Extraction utilities
│
├── processing/             # Data processing
│   ├── pipeline.py         # Processing workflows
│   ├── classifiers.py      # Content classification
│   └── exporters.py        # Export utilities
│
├── workflows/              # LangGraph workflows
│   ├── unified_workflow.py # Main orchestration
│   ├── general_scrape.py   # General purpose workflow
│   └── ai_behavior_workflow.py # AI analysis workflow
│
├── evaluation/             # Quality assessment
│   ├── evaluators.py       # Evaluation logic
│   ├── metrics.py          # Metrics calculation
│   └── dataset_utils.py    # Dataset management
│
├── prompts/                # LLM prompts
│   ├── agent_prompts.py    # Agent system prompts
│   ├── classifier_prompts.py # Classification prompts
│   └── tool_prompts.py     # Tool descriptions
│
└── api/                    # User interfaces
    ├── main.py             # Main API
    └── cli.py              # Command line interface
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd DOTbot

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Environment Variables

Create a `.env` file with:

```env
OPENAI_API_KEY=your_openai_key_here
LANGSMITH_API_KEY=your_langsmith_key_here
LANGSMITH_PROJECT=DOTbot-Observatory
```

### Basic Usage

#### Command Line Interface

```bash
# General web scraping
python main.py scrape https://example.com/data --format csv

# AI behavior analysis
python main.py analyze https://lesswrong.com/posts/example "Find deceptive behaviors"

# Batch processing
python main.py batch --urls url1.com url2.com url3.com

# Show system information
python main.py info
```

#### Programmatic Usage

```python
import asyncio
from api.main import create_dotbot_instance

async def main():
    # Create DOTbot instance
    dotbot = create_dotbot_instance()
    
    # General web scraping
    result = await dotbot.extract_structured_data(
        url="https://example.com/data",
        scrape_mode="auto",
        export_format="csv"
    )
    
    # AI behavior analysis  
    analysis = await dotbot.analyze_ai_behavior(
        url="https://lesswrong.com/posts/example",
        question="Find examples of reward gaming",
        categories=["Reward Gaming", "Deceptive Behaviour"]
    )
    
    print(f"Analysis complete: {analysis['success']}")

asyncio.run(main())
```

## 🔧 Configuration

### Scraping Modes

- **`basic`**: HTTP requests with BeautifulSoup (fast, reliable)
- **`browser`**: Browser automation with Browser-Use (handles JS)
- **`auto`**: Automatically selects optimal mode based on URL

### AI Behavior Categories

DOTbot analyzes content for these concerning behaviors:

1. **Deceptive Behaviour**: Misleading or false information
2. **Reward Gaming**: Exploiting evaluation metrics
3. **Sycophancy**: Telling users what they want to hear
4. **Goal Misgeneralization**: Pursuing unintended objectives
5. **Unauthorized Access**: Attempting to bypass restrictions

### Export Formats

- **CSV**: Structured tabular data
- **JSON**: Hierarchical data with metadata
- **Database**: SQLite storage for large datasets

## 📊 Evaluation and Quality

DOTbot includes comprehensive evaluation capabilities:

### General Scraping Metrics
- **Extraction Accuracy**: Completeness of data extraction
- **Structure Quality**: Consistency of extracted schema
- **Content Quality**: Meaningfulness of extracted content
- **Performance**: Speed and success rates

### AI Behavior Analysis Metrics
- **Detection Recall**: Coverage of concerning behaviors
- **Classification Precision**: Accuracy of behavior categorization
- **Semantic Fidelity**: Preservation of original meaning
- **Coverage**: Breadth of content analyzed

## 🔄 Workflows

DOTbot uses LangGraph for sophisticated processing workflows:

### Unified Workflow
1. **Route Scraper**: Select optimal scraping method
2. **Perform Scraping**: Extract raw content
3. **Process Content**: Analyze and structure data
4. **Export Data**: Save in requested format
5. **Finalize**: Complete workflow and report results

### AI Behavior Workflow
1. **Initialize Analysis**: Set up behavior detection
2. **Scrape Content**: Extract relevant content
3. **Analyze Behavior**: Classify concerning behaviors
4. **Generate Reports**: Create detailed analysis reports
5. **Finalize Analysis**: Summarize findings

## 🧪 Testing and Development

### Running Tests

```bash
# Install development dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest

# Run specific test categories
pytest tests/test_scraping.py
pytest tests/test_processing.py
```

### Example Test

```python
import pytest
from api.main import create_dotbot_instance

@pytest.mark.asyncio
async def test_basic_scraping():
    dotbot = create_dotbot_instance()
    
    result = await dotbot.extract_structured_data(
        url="https://httpbin.org/json",
        scrape_mode="basic"
    )
    
    assert result["success"] == True
    assert result["export_path"] is not None
```

## 📚 Advanced Usage

### Custom Scrapers

```python
from scraping.base_scraper import BaseScraper

class CustomScraper(BaseScraper):
    async def scrape_url(self, url: str, **kwargs):
        # Custom scraping logic
        pass
    
    def is_suitable_for_url(self, url: str) -> bool:
        return "custom-site.com" in url
```

### Custom Evaluation

```python
from evaluation.evaluators import BaseEvaluator

class CustomEvaluator(BaseEvaluator):
    async def evaluate(self, result, **kwargs):
        # Custom evaluation logic
        return EvaluationMetrics(custom_metric=0.95)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Run tests: `pytest`
6. Commit changes: `git commit -am 'Add feature'`
7. Push to branch: `git push origin feature-name`
8. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🛠️ Migration Notes

This unified system combines:
- **agent_workflow/**: General web scraping with LangGraph
- **src/**: AI behavior analysis with Browser-Use
- **evals/**: Evaluation framework with LangSmith

### Backward Compatibility

Legacy imports are supported through compatibility layers:

```python
# Old agent_workflow usage still works
from agent_workflow.src.basic_scraper import url_handler

# New unified usage
from scraping.tools.url_handler import url_handler
```

## 🔍 Troubleshooting

### Common Issues

1. **Browser automation fails**: Install browser dependencies
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **LangSmith connection issues**: Check API key and project settings

3. **Import errors**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

### Debug Mode

Enable verbose logging:

```bash
python main.py scrape <url> --verbose
```

Or programmatically:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📞 Support

- **Issues**: Create an issue on GitHub
- **Questions**: Check the documentation or create a discussion
- **Feature Requests**: Submit an enhancement issue

---

**DOTbot** - Unified Web Scraping and AI Behavior Analysis Tool