# GPIGuard - Unicode Threat Detection System

A comprehensive Python-based system for detecting and analyzing Unicode-based security threats, including homoglyphs, confusables, bidirectional text attacks, and identifier spoofing.

## Overview

GPIGuard is designed to:
- **Collect data** from multiple sources (Web APIs, CSV, JSON, XML, HTML, Reddit, Twitter, GitHub)
- **Parse and analyze** Unicode characters for security threats
- **Detect threats** such as:
  - Homoglyph attacks (visually similar characters from different scripts)
  - Confusable characters (easily confused characters)
  - Bidirectional (BIDI) text attacks
  - Identifier spoofing attempts
  - Zero-width character injections
- **Generate reports** in multiple formats for security analysis

## Project Structure

```
GPIGuard/
├── data_collection/          # Data collection from various sources
│   ├── collectors/           # Source-specific collectors (HTML, Reddit, Twitter, GitHub, etc.)
│   ├── scrapers/             # Web scraping utilities
│   ├── config/               # Configuration files
│   └── utils/                # Utility functions
│
├── data_parsing/             # Data parsing and preprocessing
│   ├── parsers/              # Format-specific parsers (CSV, JSON, XML, etc.)
│   ├── filters/              # Data filtering and interference detection
│   └── utils/                # Parsing utilities
│
├── unicode_analysis/         # Unicode threat detection engine
│   ├── homograph_detector.py # Homoglyph detection
│   ├── identifier_status_detector.py # Identifier spoofing detection
│   ├── threat_formatter.py   # Threat formatting and reporting
│   └── analysis_main.py      # Main analysis entry point
│
└── requirements.txt          # Python dependencies
```

## Quick Start

### 1. Installation

```bash
# Clone or download the project
cd GPIGuard

# Install dependencies
pip install -r requirements.txt
```

For detailed installation instructions, see [INSTALLATION.md](INSTALLATION.md).

### 2. Configuration

Before running the system, configure your settings:

```bash
# Copy configuration template
cp config/config_template.json config/config.json

# Edit configuration as needed
# See CONFIGURATION.md for detailed options
```

### 3. Basic Usage

#### Run Unicode Analysis

```bash
cd unicode_analysis
python analysis_main.py --source-dir ../testscan_data/parsed_data --output-dir ../testscan_data/threat_detection
```

#### Run Data Collection

```bash
cd data_collection
python collect_data.py
```

#### Run Data Parsing

```bash
cd data_parsing
python parse_data.py
```

## Key Features

### Data Collection Module
- **Multi-source Support**: HTML, CSV, JSON, XML, Reddit, Twitter, GitHub APIs
- **Configurable Collection**: Settings-based data source configuration
- **Error Handling**: Robust error management with detailed logging
- **Data Validation**: Input validation and preprocessing

### Data Parsing Module
- **Format Support**: Parse CSV, JSON, XML, HTML, and more
- **Data Filtering**: Remove interference and duplicate content
- **Structured Output**: Convert to standardized data formats
- **Encoding Detection**: Automatic character encoding detection

### Unicode Analysis Module
- **Threat Detection**: Multiple threat detection algorithms
- **Report Generation**: Generate threats in JSON, CSV, and text formats
- **Performance Optimization**: Efficient Unicode processing
- **Comprehensive Analysis**: Detailed character analysis and classification

## Threat Detection Types

### 1. Homograph Detection
Identifies characters that look similar but come from different Unicode blocks:
- Latin-Greek confusion (e.g., Greek Alpha vs Latin A)
- Cyrillic-Latin confusion
- Extended Latin variants

### 2. Confusable Detection
Uses Unicode Confusables database to detect easily confused characters:
- Visually similar characters across different scripts
- Similar diacritic marks

### 3. BIDI (Bidirectional) Detection
Detects bidirectional override attacks:
- BIDI override characters (U+202E, U+202D, etc.)
- Isolation characters
- BIDI contextual detection

### 4. Identifier Status Detection
Identifies potential identifier spoofing:
- Checks character identifier status in Unicode
- Detects mixing of scripts in identifiers
- Flags potentially confusing identifier patterns

### 5. Unicode Type Classification
Categorizes Unicode characters:
- Script classification
- Category classification
- Bidirectional properties

## Configuration

See [CONFIGURATION.md](CONFIGURATION.md) for detailed configuration options including:
- Data collection source settings
- Parser behavior customization
- Threat detection thresholds
- Output format preferences
- Logging configuration

## Output Format

Threat detection results are available in multiple formats:
- **JSON**: Structured threat data with complete details
- **CSV**: Tabular format for spreadsheet analysis
- **Text**: Human-readable threat reports

Sample output structure:
```json
{
  "character": "α",
  "unicode_point": "U+03B1",
  "threat_type": "homograph",
  "threat_severity": "high",
  "description": "Greek Alpha - looks similar to Latin A",
  "source": "test_data.txt",
  "location": "line 5, column 12"
}
```

## Logging

The system provides detailed logging across all modules:
- Logs stored in `log/` directory
- Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- Separate logs for each module

## Requirements

- Python 3.8 or higher
- See [requirements.txt](requirements.txt) for full dependency list
- Dependencies include:
  - `requests` for HTTP requests
  - `beautifulsoup4` for HTML parsing
  - `lxml` for XML processing
  - `pandas` for data analysis
  - `regex` for advanced pattern matching

## API Integration

The system supports integration with:
- **Reddit API**: Requires `praw` configuration
- **Twitter API v2**: Requires `tweepy` configuration
- **GitHub API**: For code threat analysis
- **Custom APIs**: Extensible collector architecture

## Performance Considerations

- Large file processing: Use streaming when possible
- Unicode analysis: Optimized for character-level operations
- Memory usage: Configurable batch processing
- Parallel processing: Supported for multi-source collection

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure project root is in Python path
2. **Configuration Not Found**: Check `config/` directory and file paths
3. **API Failures**: Verify API credentials in configuration
4. **Encoding Issues**: Ensure UTF-8 file encoding

See logs in `log/` directory for detailed error information.

## Contributing

To extend the system:
1. Add new collectors in `data_collection/collectors/`
2. Add new parsers in `data_parsing/parsers/`
3. Extend threat detection in `unicode_analysis/`
4. Maintain consistent English documentation

## License

[Add your license information here]

## Contact & Support

[Add support contact information here]

## Version History

- **v1.0** (January 2026): Initial release with homoglyph, confusable, and BIDI threat detection

## Changelog

### v1.0 Initial Release
- Comprehensive Unicode threat detection engine
- Multi-source data collection system
- Flexible data parsing framework
- Support for JSON, CSV, XML output formats
- Complete English documentation
