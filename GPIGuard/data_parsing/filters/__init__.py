#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据过滤器模块
提供各种文本过滤功能，包括干扰字符过滤
"""

from .interference_filter import InterferenceCharacterFilter
from .filter_config import INTERFERENCE_FILTER_CONFIG

__all__ = [
    'InterferenceCharacterFilter',
    'INTERFERENCE_FILTER_CONFIG'
]



