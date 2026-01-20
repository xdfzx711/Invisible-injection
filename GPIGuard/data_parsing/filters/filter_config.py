#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filter Config File - Interference Character Filter Strategy
Only remove true interference characters (emoji, math symbols, kaomoji, etc.), preserve normal and attack characters
"""

import json
import os
import re

# Interference character filter config - enabled by default
INTERFERENCE_FILTER_CONFIG = {
    "enabled": True,                   # Enable filter
    "mode": "interference_removal",    # Interference character removal mode
    "preserve_unicode_attacks": True,  # Preserve Unicode attack characters
    "preserve_normal_text": True,      # Preserve normal text characters
    "output_report": False,            # Do not generate filter report
    "log_filtered_chars": True         # Log filtered characters
}

# Interference character ranges to remove
INTERFERENCE_RANGES = [
    # Emoji symbols
    (0x1F600, 0x1F64F),  # Emoticons
    (0x1F300, 0x1F5FF),  # Misc Symbols and Pictographs
    (0x1F680, 0x1F6FF),  # Transport and Map Symbols
    (0x1F1E6, 0x1F1FF),  # Regional Indicator Symbols
    (0x2600, 0x26FF),    # Miscellaneous Symbols
    (0x2700, 0x27BF),    # Dingbats
    
    # Math symbols (non-attack)
    (0x2200, 0x22FF),    # Mathematical Operators
    (0x2A00, 0x2AFF),    # Supplemental Mathematical Operators
    (0x27C0, 0x27EF),    # Miscellaneous Mathematical Symbols-A
    (0x2980, 0x29FF),    # Miscellaneous Mathematical Symbols-B
    (0x2B00, 0x2BFF),    # Miscellaneous Symbols and Arrows
    
    # Other decorative symbols
    (0x2500, 0x257F),    # Box Drawing
    (0x2580, 0x259F),    # Block Elements
    (0x25A0, 0x25FF),    # Geometric Shapes
    
    # Thai characters (used for kaomoji)
    (0x0E00, 0x0E7F),    # Thai
    
    # Arabic character forms (decorative)
    (0xFE70, 0xFEFF),    # Arabic Presentation Forms-B
    
    # General Punctuation
    (0x2000, 0x206F),    # General Punctuation (includes • etc)
]

# Specific interference characters to remove (individual characters)
INTERFERENCE_CHARS = {
    'ฅ',    # U+0E05 THAI CHARACTER KHO KHON (kaomoji decoration)
    '^',    # U+005E CIRCUMFLEX ACCENT (kaomoji decoration)
    '•',    # U+2022 BULLET (decorative symbol)
    'ﻌ',    # U+FECC ARABIC LETTER AIN MEDIAL FORM (decorative)
    'ü',    # U+00FC LATIN SMALL LETTER U WITH DIAERESIS (decorative)
    '©',    # U+00A9 COPYRIGHT SIGN (decorative symbol)
    'µ',    # U+00B5 MICRO SIGN (decorative symbol)
}

# Protected Unicode attack character ranges (preserve even if look like interference)
PROTECTED_ATTACK_RANGES = [
    (0xE0000, 0xE007F),  # Tag Characters
    (0x1D400, 0x1D7FF),  # Mathematical Alphanumeric Symbols (Homoglyph Character)
    (0x200B, 0x200F),    # Zero-width characters
    (0x2060, 0x2064),    # Word Joiner
    (0xFEFF, 0xFEFF),    # Zero-width non-breaking space
    (0xE0100, 0xE01EF),  # Variation Selector Supplement
    (0x0300, 0x036F),    # Combining Diacritical Marks
    (0x1AB0, 0x1AFF),    # Combining Diacritical Marks Extended
    (0x1DC0, 0x1DFF),    # Combining Diacritical Marks Supplement
    (0x034F, 0x034F),    # Combining Grapheme Joiner
    (0x061C, 0x061C),    # Arabic Letter Mark
    (0x180E, 0x180E),    # Mongolian Vowel Separator
    (0xFFF9, 0xFFFB),    # Interoperability characters
    # BIDI bidirectional text control characters (preserve for Unicode attack detection)
    (0x202A, 0x202E),    # BIDI Embedding and Override Characters (LRE, RLE, PDF, LRO, RLO)
    (0x2066, 0x2069),    # BIDI Isolate Characters (LRI, RLI, FSI, PDI)
]

# Kaomoji emoticon patterns (simplified version, avoid complex Unicode escapes)
KAOMOJI_PATTERNS = [
    r'[（(][^)）]*[）)]',  # Basic parenthesis emoticons
    r'[╯°□°）╯]',         # Flip table emoticon related characters
    r'[¯\\_(ツ)_/¯]',      # Shrug emoticon related characters
    r'[ಠ_ಠ]',             # Stare emoticon
    r'[◕_◕]',             # Round eyes emoticon
]

# Format control characters to preserve
PRESERVED_FORMAT_CHARS = {
    '\n',    # Newline (U+000A)
    '\r',    # Carriage return (U+000D)  
    '\t',    # Tab (U+0009)
    ' ',     # Space (U+0020)
}