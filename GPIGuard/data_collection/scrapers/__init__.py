#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTML爬取模块
"""

from .web_scraper import WebScraper
from .html_extractor import HTMLExtractor
from .scraping_config import ScrapingConfig

__all__ = ['WebScraper', 'HTMLExtractor', 'ScrapingConfig']
