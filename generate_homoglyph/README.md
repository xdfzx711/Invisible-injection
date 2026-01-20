# Homoglyph Character Generator

A Python utility for generating homoglyph characters - visually similar Unicode characters from different writing systems that can be used for security research, testing, and demonstration purposes.

## Overview

The Homoglyph Character Generator provides a comprehensive mapping of Latin characters to their homoglyphic equivalents from various Unicode blocks including:

- **Cyrillic characters** - Latin characters that look similar to Cyrillic characters
- **Greek characters** - Greek alphabet characters that resemble Latin letters
- **Mathematical alphanumeric symbols** - Bold, italic, and other mathematical variants
- **Fullwidth characters** - East Asian fullwidth character equivalents
- **Special Unicode variations** - Roman numerals, lunate sigma, and other variants

## Features

- Extensive homoglyph mapping tables for both lowercase and uppercase letters
- Support for Unicode confusables from a mappings file
- Digit and number character homoglyph generation
- Symbol and punctuation character substitution
- Flexible character replacement with fallback options

## Usage

### Basic Usage

```python
from homoglyph import HomoglyphGenerator

# Initialize the generator
generator = HomoglyphGenerator()

# Get homoglyphs for a character
homoglyphs_for_a = generator.homoglyphs.get('a')
# Result: ['а', 'α', 'ɑ', 'ａ']

# Generate a homoglyph string
original = "example"
obfuscated = generator.generate_homoglyph_string(original)
# Result: String with characters replaced by homoglyphs
```

### Advanced Features

```python
# Initialize with custom Unicode confusables mapping
generator = HomoglyphGenerator(
    load_digit_mapping=True, 
    digit_mapping_file='unicode_confusables.json'
)

# Generate homoglyphs with specific selection methods
homoglyph_text = generator.generate_obfuscated_text(
    original_text="password",
    max_substitutions=0.5  # Replace up to 50% of characters
)
```

## Homoglyph Mapping Examples

### Latin Lowercase Letters

- `a` → `а` (Cyrillic), `α` (Greek), `ɑ` (Latin variant), `ａ` (Fullwidth)
- `o` → `о` (Cyrillic), `ο` (Greek), `ｏ` (Fullwidth)
- `p` → `р` (Cyrillic), `ρ` (Greek)
- `x` → `х` (Cyrillic), `χ` (Greek)

### Latin Uppercase Letters

- `A` → `А` (Cyrillic), `Α` (Greek), `Ａ` (Fullwidth)
- `H` → `Н` (Cyrillic), `Η` (Greek)
- `O` → `О` (Cyrillic), `Ο` (Greek), `Ｏ` (Fullwidth)

## Security Considerations

This tool is designed for:
- ✅ Security research and awareness
- ✅ Testing Unicode vulnerability detection systems
- ✅ Demonstrating homoglyph attack vectors
- ✅ Educational purposes about Unicode security threats

### Warning

⚠️ Homoglyph attacks can be used maliciously to:
- Spoof domain names and usernames
- Bypass security filters and content moderation
- Create visually deceptive content
- Deceive users into trusting fraudulent content

Use responsibly and only for authorized security testing.

## Key Classes and Methods

### HomoglyphGenerator

- `__init__(load_digit_mapping, digit_mapping_file)` - Initialize with optional Unicode confusables
- `homoglyphs` - Dictionary mapping characters to homoglyph lists
- `generate_homoglyph_string(text)` - Convert entire strings to homoglyphs
- `get_homoglyphs(char)` - Get all homoglyphs for a specific character
- `has_homoglyph(char)` - Check if a character has homoglyphs

## File Structure

```
generate_homoglyph/
├── README.md              # This file
└── homoglyph.py          # Main HomoglyphGenerator class
```

## Dependencies

- Python 3.6+
- Standard library only (no external dependencies for basic functionality)

## Related Projects

- **generate_unicode_tag_characters** - Generate Unicode tag characters for text encoding
- **GPIGuard** - Comprehensive Unicode threat detection system
- **Unicode_data.json** - Unicode character metadata and confusables database

## License

This project is intended for security research and educational purposes.

## Contributing

To extend the homoglyph mappings:

1. Add new character mappings to the `self.homoglyphs` dictionary
2. Include comments identifying the source Unicode block
3. Limit to 4 most effective homoglyphs per character
4. Test with the GPIGuard detection system

## References

- Unicode Standard - Confusable Characters
- International Domain Names (IDN) Security
- Homoglyph Attack Vectors
- Zero-width and invisible character exploits
