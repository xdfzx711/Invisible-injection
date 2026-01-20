# Unicode Tag Character Generator

A Python utility for converting regular text to Unicode tag characters - a special encoding mechanism using the Unicode tag block (U+E0000–U+E007F) for text obfuscation and security research.

## Overview

The Unicode Tag Character Generator converts standard text into Unicode tag characters, which are invisible or barely visible Unicode characters that can be used for:

- Security research and vulnerability testing
- Understanding Unicode encoding mechanisms
- Demonstrating text obfuscation techniques
- Educational exploration of Unicode features

## What are Unicode Tag Characters?

Unicode tag characters are characters in the **Tag block** (U+E0000 to U+E007F) originally intended for language and character variant specification in certain protocols. They can be used to encode regular ASCII characters invisibly within text streams.

### Mapping

Each standard ASCII character (U+0000 to U+007F) is mapped to a tag character by adding 0xE0000:
- `A` (U+0041) → Tag A (U+E0041)
- `1` (U+0031) → Tag 1 (U+E0031)
- `@` (U+0040) → Tag @ (U+E0040)

## Features

- **Text to Tag Character Conversion** - Convert any string to invisible tag characters
- **Clipboard Integration** - Copy converted text directly to clipboard
- **File Output** - Save converted text to files
- **Interactive CLI** - User-friendly command-line interface
- **Error Handling** - Robust error management for conversion failures

## Usage

### Command Line Interface

```bash
python unicode_tag_characters.py
```

The program will start an interactive session:

```
 Unicode Tag Character Converter
========================================

Enter the text to convert (or type 'exit' to quit): hello world
 Conversion successful!
 Converted text: <invisible tag characters>
 Save to file? (y/n): y
  Saved to file: D:\output\basic_tag_characters.txt
```

### Python API

```python
from unicode_tag_characters import convert_to_tag_chars, save_to_file, copy_to_clipboard

# Convert text to tag characters
original_text = "Hello World"
tag_chars = convert_to_tag_chars(original_text)

# Save to file
save_to_file(tag_chars, "./output/encoded.txt")

# Copy to clipboard
copy_to_clipboard(tag_chars)
```

## API Reference

### convert_to_tag_chars(input_string)

Converts input string to Unicode tag characters.

**Parameters:**
- `input_string` (str) - Text to convert

**Returns:**
- `str` - Converted text with tag characters
- `None` - If conversion fails

**Example:**
```python
result = convert_to_tag_chars("test")
# Result: String with characters converted to tag block equivalents
```

### save_to_file(text, filename)

Saves converted text to a file.

**Parameters:**
- `text` (str) - Text to save (usually converted tag characters)
- `filename` (str) - Output file path (default: "output.txt")

**Returns:**
- `bool` - True if successful, False otherwise

**Example:**
```python
save_to_file(tag_chars, "./output/basic_tag_characters.txt")
```

### copy_to_clipboard(string)

Copies text to system clipboard using tkinter.

**Parameters:**
- `string` (str) - Text to copy to clipboard

**Returns:**
- None

**Example:**
```python
copy_to_clipboard(converted_text)
print("Text copied to clipboard!")
```

## Interactive Commands

The interactive mode supports:

- **Text Entry** - Enter any text to convert
- **File Saving** - Save converted text with automatic directory creation
- **Clipboard** - Copy converted text for use in other applications
- **Exit** - Type 'exit' to quit the program

## Output Structure

```
output/
└── basic_tag_characters.txt  # Converted tag characters output file
```

## Technical Details

### Character Encoding Formula

```
Tag Character Code Point = 0xE0000 + Original Character Code Point

Examples:
- A (0x41) → 0xE0041 (Tag A)
- 5 (0x35) → 0xE0035 (Tag 5)
- @ (0x40) → 0xE0040 (Tag @)
```

### Supported Characters

- ASCII letters (A-Z, a-z)
- Digits (0-9)
- Punctuation and symbols
- Whitespace characters

### Limitations

- **ASCII Only** - Only supports standard ASCII characters (U+0000 to U+007F)
- **Invisibility** - Tag characters may not display visibly in all applications
- **Compatibility** - Some text editors may not support or display tag characters properly

## Dependencies

- Python 3.6+
- `tkinter` - For clipboard integration (usually included with Python)
- Standard library modules: `os`

## Use Cases

### 1. Security Testing

Test how systems handle invisible Unicode characters:

```python
payload = convert_to_tag_chars("admin")
# Test if system accepts this as valid input
```

### 2. Unicode Awareness

Demonstrate how text can be encoded invisibly:

```python
visible = "normal text"
invisible = convert_to_tag_chars("hidden")
combined = visible + invisible  # Appears as normal, contains hidden data
```

### 3. Educational Research

Learn about Unicode blocks and encoding:

```python
# Compare original and tag character versions
print(f"Original: {repr('test')}")
print(f"Tag chars: {repr(convert_to_tag_chars('test'))}")
```

## File Structure

```
generate_unicode_tag_characters/
├── README.md                      # This file
└── unicode_tag_characters.py      # Main converter utility
```

## Related Projects

- **generate_homoglyph** - Generate homoglyph characters from different scripts
- **GPIGuard** - Comprehensive Unicode threat detection system
- **Unicode_data.json** - Unicode character metadata database

## Security Considerations

⚠️ **Warning**: Unicode tag characters can be used for malicious purposes:

- **Invisible Injection** - Embed hidden commands in visible text
- **Payload Obfuscation** - Hide malicious code from detection systems
- **Social Engineering** - Craft deceptive messages containing hidden data
- **Data Exfiltration** - Encode sensitive data invisibly

Use only for:
- ✅ Authorized security research
- ✅ Vulnerability testing with permission
- ✅ Educational purposes
- ✅ Defensive system testing

## Troubleshooting

### Clipboard Operations Fail

**Problem:** tkinter clipboard operations fail on Linux/WSL

**Solution:** Ensure tkinter is installed or use the file-based output method

```bash
# Install tkinter on Ubuntu/Debian
sudo apt-get install python3-tk
```

### Characters Not Displaying

**Problem:** Converted tag characters don't display in text editor

**Solution:** Tag characters are often invisible by design. This is expected behavior. Verify with `repr()` in Python to see the actual characters.

### File Encoding Issues

**Problem:** UTF-8 encoding errors when reading files

**Solution:** Always open files with UTF-8 encoding:

```python
with open(filename, 'r', encoding='utf-8') as f:
    content = f.read()
```

## Contributing

To extend the Unicode tag character tool:

1. Add support for additional Unicode blocks
2. Implement alternative encoding methods
3. Add detection mechanisms for tag characters
4. Improve clipboard handling for different platforms

## License

This project is intended for security research and educational purposes.

## References

- Unicode Standard - Tags Block (U+E0000 to U+E007F)
- Unicode Text Encoding Techniques
- Invisible Character Exploitation Methods
- Zero-Width Character Injection Attacks
