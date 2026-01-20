# Invisible Injection - Unicode Security Research Platform

An integrated Unicode security research toolkit featuring homoglyph generation, character encoding, and threat detection capabilities.

## Core Modules Overview

This project contains four core components:

### 1️⃣ generate_homoglyph - Homoglyph Generator

**Purpose:** Generate visually similar Unicode characters for security research and testing

**Basic Usage:**
```python
from generate_homoglyph.homoglyph import HomoglyphGenerator

# Initialize the generator
generator = HomoglyphGenerator()

# Generate homoglyphs for a character
homoglyphs = generator.homoglyphs['a']  # ['а', 'α', 'ɑ', 'ａ']

# Generate obfuscated text
obfuscated = generator.generate_homoglyph_string("password")
```

📖 Detailed documentation: [generate_homoglyph/README.md](generate_homoglyph/README.md)

---

### 2️⃣ generate_unicode_tag_characters - Tag Character Generator

**Purpose:** Encode text into invisible Unicode tag characters for steganography research

**Basic Usage:**
```bash
# Run interactive mode
python generate_unicode_tag_characters/unicode_tag_characters.py

# Input text to convert, system automatically converts and saves
```

**Python API Usage:**
```python
from generate_unicode_tag_characters.unicode_tag_characters import convert_to_tag_chars, save_to_file

# Convert text
result = convert_to_tag_chars("hello world")

# Save to file
save_to_file(result, "./output/encoded.txt")
```

📖 Detailed documentation: [generate_unicode_tag_characters/README.md](generate_unicode_tag_characters/README.md)

---

### 3️⃣ GPIGuard - Unicode Threat Detection System

**Purpose:** Detect and analyze Unicode-based security threats (homoglyphs, confusables, bidirectional attacks, etc.)

**Quick Start:**

```bash
# Enter GPIGuard directory
cd GPIGuard

# Install dependencies
pip install -r requirements.txt

# Run interactive analysis system
python data_parsing/parse_data.py

# Run complete threat analysis
python unicode_analysis/analysis_main.py
```

**Core Features:**
- 📊 **Data Collection** - Collect data from multiple sources (websites, APIs, social media)
- 📝 **Data Parsing** - Support for CSV, JSON, XML, HTML and other formats
- 🔍 **Threat Detection** - Detect homoglyphs, confusable characters, bidirectional text attacks
- 📈 **Report Generation** - Output detailed threat analysis reports

📖 Detailed documentation: [GPIGuard/README.md](GPIGuard/README.md)

---

### 4️⃣ unicode_data.json - Custom Training Dataset

**Purpose:** Contains Unicode character metadata and threat characteristics for model training

**Content includes:**
- ✅ Unicode character metadata (149,186 characters)
- ✅ Confusable character mappings (10,000+ mapping relationships)
- ✅ Threat profiles (homoglyphs, bidirectional attacks, etc.)
- ✅ Identifier status information
- ✅ Script and language information

**Usage:**
```python
import json

# Load the dataset
with open('unicode_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Access confusable mappings
confusables = data['confusables']['a']

# View threat profiles
threats = data['threat_profiles']
```

📖 Detailed documentation: [Unicode_data.json.md](Unicode_data.json.md)


---

## Quick Start Guide

### Scenario 1: I want to generate homoglyph characters for testing

```bash
cd generate_homoglyph
python -c "from homoglyph import HomoglyphGenerator; g = HomoglyphGenerator(); print(g.generate_homoglyph_string('admin'))"
```

### Scenario 2: I want to generate invisible encoded text

```bash
python generate_unicode_tag_characters/unicode_tag_characters.py
# Follow prompts to input text, system automatically converts and saves
```

### Scenario 3: I want to detect Unicode threats in text

```bash
cd GPIGuard
python unicode_analysis/analysis_main.py
# Follow system prompts to analyze data
```

### Scenario 4: I want to train models using the dataset

```python
import json

# Load training data
with open('unicode_data.json', 'r', encoding='utf-8') as f:
    training_data = json.load(f)

# Use training_data['confusables'] for model training
# Use training_data['threat_profiles'] to define threat categories
```

---

## Installation & Environment

### System Requirements
- Python 3.8+
- pip package manager

### Installation Steps

```bash
# 1. Clone or download the project
git clone <project-url>
cd Invisible\ Injection

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# 3. Install GPIGuard dependencies
cd GPIGuard
pip install -r requirements.txt
```

---

## File Description

| File/Folder | Description |
|------------|------------|
| `generate_homoglyph/` | Homoglyph character generation tool |
| `generate_unicode_tag_characters/` | Unicode tag character encoding tool |
| `GPIGuard/` | Main threat detection and analysis system |
| `unicode_data.json` | Custom Unicode threat dataset |
| `syntesis_data.json` | Synthesized data file |
| `README.md` | English version documentation |

---

## Frequently Asked Questions

### Q1: Where should I start?

**A:** If you're new, we recommend the following order:
1. Read this README to understand the overall structure
2. View each module's README.md for detailed information
3. Try the four core features one by one

### Q2: What is the purpose of these tools?

**A:** These are security research tools for:
- ✅ Educational purposes - Understanding Unicode security threats
- ✅ Defensive research - Developing detection and protection mechanisms
- ✅ Academic research - Analyzing character similarity and attack vectors

### Q3: Can these be used for malicious purposes?

**A:** ⚠️ **No**. These tools are designed specifically for defensive security research. Any malicious use will have legal consequences.

### Q4: How large is the dataset?

**A:** `unicode_data.json` contains:
- 149,186 Unicode character data entries
- 10,000+ confusable character mappings
- Complete threat feature library

---

## License and Disclaimer

⚠️ **Important Notice:**

- For **security research and educational use only**
- Prohibited from **malicious purposes** (fraud, social engineering, etc.)
- Users must understand relevant **legal regulations** before use
- Users bear **full responsibility** for all operations

---

## Need Help?

1. View detailed documentation for each module:
   - [generate_homoglyph/README.md](generate_homoglyph/README.md)
   - [generate_unicode_tag_characters/README.md](generate_unicode_tag_characters/README.md)
   - [GPIGuard/README.md](GPIGuard/README.md)
   - [Unicode_data.json.md](Unicode_data.json.md)

2. Check project log files for error information

3. Ensure Python version >= 3.8

---

**Project Version:** v1.0  
**Last Updated:** January 2026  
**Maintained By:** Invisible Injection Team
