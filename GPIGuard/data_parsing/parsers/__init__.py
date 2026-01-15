#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据解析器集合
"""

from .json_parser import JSONParser
from .csv_parser import CSVParser
from .xml_parser import XMLParser
from .html_parser import HTMLParser
from .reddit_parser import RedditParser
from .twitter_parser import TwitterParser
from .github_parser import GithubParser
from .godofprompt_parser import GodOfPromptParser

__all__ = [
    'JSONParser',
    'CSVParser',
    'XMLParser',
    'HTMLParser',
    'RedditParser',
    'TwitterParser',
    'GithubParser',
    'GodOfPromptParser'
]
