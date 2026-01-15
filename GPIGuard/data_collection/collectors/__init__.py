#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据收集器模块
所有数据收集器的实现
"""

from .html_collector import HTMLCollector
from .reddit_collector import RedditCollector
from .twitter_collector import TwitterCollector
from .github_collector import GithubCollector
from .godofprompt_collector import GodOfPromptCollector

__all__ = [
    'HTMLCollector',
    'RedditCollector',
    'TwitterCollector',
    'GithubCollector',
    'GodOfPromptCollector'
]

