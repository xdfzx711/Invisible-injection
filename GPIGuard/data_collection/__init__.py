#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Data Collection Module
统一的数据收集接口，支持HTML、API、Reddit、Twitter等多种数据源
"""

__version__ = "2.0.0"
__author__ = "Unicode Agent Team"

from .collect_data import DataCollectionManager

__all__ = ['DataCollectionManager']



