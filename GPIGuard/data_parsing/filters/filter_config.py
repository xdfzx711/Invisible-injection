#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
过滤器配置File - 干扰字符过滤策略
只移除真正的干扰字符（emoji、数学符号、kaomoji等），保留正常字符和攻击字符
"""

import json
import os
import re

# 干扰字符过滤器配置 - 默认全部启用
INTERFERENCE_FILTER_CONFIG = {
    "enabled": True,                   # 启用过滤器
    "mode": "interference_removal",    # 干扰字符移除模式
    "preserve_unicode_attacks": True,  # 保留Unicode攻击字符
    "preserve_normal_text": True,      # 保留正常文本字符
    "output_report": False,            # 不生成过滤报告
    "log_filtered_chars": True         # 记录被过滤的字符
}

# 需要移除的干扰字符范围
INTERFERENCE_RANGES = [
    # Emoji表情符号
    (0x1F600, 0x1F64F),  # Emoticons
    (0x1F300, 0x1F5FF),  # Misc Symbols and Pictographs
    (0x1F680, 0x1F6FF),  # Transport and Map Symbols
    (0x1F1E6, 0x1F1FF),  # Regional Indicator Symbols
    (0x2600, 0x26FF),    # Miscellaneous Symbols
    (0x2700, 0x27BF),    # Dingbats
    
    # 数学符号（非攻击性的）
    (0x2200, 0x22FF),    # Mathematical Operators
    (0x2A00, 0x2AFF),    # Supplemental Mathematical Operators
    (0x27C0, 0x27EF),    # Miscellaneous Mathematical Symbols-A
    (0x2980, 0x29FF),    # Miscellaneous Mathematical Symbols-B
    (0x2B00, 0x2BFF),    # Miscellaneous Symbols and Arrows
    
    # 其他装饰性符号
    (0x2500, 0x257F),    # Box Drawing
    (0x2580, 0x259F),    # Block Elements
    (0x25A0, 0x25FF),    # Geometric Shapes
    
    # 泰语字符（用于kaomoji）
    (0x0E00, 0x0E7F),    # Thai
    
    # 阿拉伯语字符形式（装饰性）
    (0xFE70, 0xFEFF),    # Arabic Presentation Forms-B
    
    # 通用标点符号
    (0x2000, 0x206F),    # General Punctuation (包含 • 等)
]

# 需要移除的具体干扰字符（单个字符）
INTERFERENCE_CHARS = {
    'ฅ',    # U+0E05 THAI CHARACTER KHO KHON (kaomoji装饰)
    '^',    # U+005E CIRCUMFLEX ACCENT (kaomoji装饰)
    '•',    # U+2022 BULLET (装饰性符号)
    'ﻌ',    # U+FECC ARABIC LETTER AIN MEDIAL FORM (装饰性)
    'ü',    # U+00FC LATIN SMALL LETTER U WITH DIAERESIS (装饰性)
    '©',    # U+00A9 COPYRIGHT SIGN (装饰性符号)
    'µ',    # U+00B5 MICRO SIGN (装饰性符号)
}

# 需要保留的Unicode攻击字符范围（即使看起来像干扰字符也要保留）
PROTECTED_ATTACK_RANGES = [
    (0xE0000, 0xE007F),  # 标签字符（Tag Characters）
    (0x1D400, 0x1D7FF),  # 数学字母数字符号 (Homoglyph Character)
    (0x200B, 0x200F),    # 零宽字符
    (0x2060, 0x2064),    # 词连接符
    (0xFEFF, 0xFEFF),    # 零宽非断空格
    (0xE0100, 0xE01EF),  # 变体选择符补充
    (0x0300, 0x036F),    # 组合变音符号
    (0x1AB0, 0x1AFF),    # 组合变音符号扩展
    (0x1DC0, 0x1DFF),    # 组合变音符号补充
    (0x034F, 0x034F),    # 组合石墨连接符
    (0x061C, 0x061C),    # 阿拉伯字母标记
    (0x180E, 0x180E),    # 蒙古语元音分隔符
    (0xFFF9, 0xFFFB),    # 互操作性字符
    # BIDI双向文本控制字符（保留用于Unicode攻击检测）
    (0x202A, 0x202E),    # BIDI嵌入和覆盖字符 (LRE, RLE, PDF, LRO, RLO)
    (0x2066, 0x2069),    # BIDI隔离字符 (LRI, RLI, FSI, PDI)
]

# Kaomoji 颜文字模式（简化版，避免复杂的Unicode转义）
KAOMOJI_PATTERNS = [
    r'[（(][^)）]*[）)]',  # 基本括号表情
    r'[╯°□°）╯]',         # 翻桌表情相关字符
    r'[¯\\_(ツ)_/¯]',      # 耸肩表情相关字符
    r'[ಠ_ಠ]',             # 瞪眼表情
    r'[◕_◕]',             # 圆眼表情
]

# 需要保留的格式控制字符
PRESERVED_FORMAT_CHARS = {
    '\n',    # 换行符 (U+000A)
    '\r',    # 回车符 (U+000D)  
    '\t',    # 制表符 (U+0009)
    ' ',     # 空格 (U+0020)
}