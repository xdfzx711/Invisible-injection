#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API数据源配置
集中管理所有API数据源的URL和配置
"""

# ==================== JSON数据源 ====================

# GitHub API数据源
GITHUB_SOURCES = {
    'users': [
        {'username': 'torvalds', 'description': 'Linus Torvalds'},
        {'username': 'gvanrossum', 'description': 'Python创始人'},
        {'username': 'octocat', 'description': 'GitHub吉祥物'},
        {'username': 'defunkt', 'description': 'GitHub联合创始人'},
        {'username': 'mojombo', 'description': 'GitHub联合创始人'},
        {'username': 'pjhyett', 'description': 'GitHub早期员工'},
        {'username': 'wycats', 'description': 'Ember.js创始人'},
        {'username': 'dhh', 'description': 'Ruby on Rails创始人'},
    ]
}

# 公共API数据源
PUBLIC_API_SOURCES = [
    {
        'name': 'worldbank_population',
        'urls': [
            'https://api.worldbank.org/v2/country/US/indicator/SP.POP.TOTL?format=json&date=2020:2023',
            'https://api.worldbank.org/v2/country/CN/indicator/SP.POP.TOTL?format=json&date=2020:2023',
            'https://api.worldbank.org/v2/country/GB/indicator/SP.POP.TOTL?format=json&date=2020:2023'
        ],
        'description': '世界银行人口数据',
        'type': 'worldbank'
    },
    {
        'name': 'wikipedia_articles',
        'urls': [
            'https://en.wikipedia.org/w/api.php?action=query&titles=Python_(programming_language)&format=json&prop=extracts&exintro=true',
            'https://en.wikipedia.org/w/api.php?action=query&titles=Artificial_intelligence&format=json&prop=extracts&exintro=true',
            'https://en.wikipedia.org/w/api.php?action=query&titles=Machine_learning&format=json&prop=extracts&exintro=true'
        ],
        'description': 'Wikipedia文章数据',
        'type': 'wikipedia'
    },
    {
        'name': 'wikidata_entities',
        'urls': [
            'https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q42&format=json',
            'https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q5&format=json',
            'https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q1860&format=json'
        ],
        'description': 'Wikidata实体数据',
        'type': 'wikidata'
    },
    {
        'name': 'nasa_apod',
        'urls': [
            'https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY&count=3'
        ],
        'description': 'NASA每日天文图片',
        'type': 'nasa'
    }
]

# 金融API数据源
FINANCIAL_API_SOURCES = [
    {
        'name': 'crypto_prices',
        'urls': [
            'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,cardano&vs_currencies=usd,eur',
            'https://api.coingecko.com/api/v3/coins/bitcoin',
            'https://api.coingecko.com/api/v3/coins/ethereum'
        ],
        'description': '加密货币价格数据',
        'type': 'crypto'
    },
    {
        'name': 'crypto_markets',
        'urls': [
            'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1',
            'https://api.coingecko.com/api/v3/global'
        ],
        'description': '加密货币市场数据',
        'type': 'crypto'
    },
    {
        'name': 'exchange_rates',
        'urls': [
            'https://api.exchangerate-api.com/v4/latest/USD',
            'https://api.exchangerate-api.com/v4/latest/EUR',
            'https://api.exchangerate-api.com/v4/latest/GBP'
        ],
        'description': '汇率数据',
        'type': 'forex'
    }
]

# 天气API数据源
WEATHER_API_SOURCES = [
    {
        'name': 'weather_free',
        'urls': [
            'https://wttr.in/London?format=j1',
            'https://wttr.in/NewYork?format=j1',
            'https://wttr.in/Tokyo?format=j1'
        ],
        'description': '免费天气数据',
        'type': 'weather'
    }
]

# ==================== CSV数据源 ====================

GOVERNMENT_CSV_SOURCES = [
    {
        'name': 'us_federal_holidays',
        'url': 'https://raw.githubusercontent.com/datasets/us-federal-holidays/master/data/us-federal-holidays.csv',
        'description': '美国联邦假日数据',
        'country': 'US',
        'format': 'csv'
    },
    {
        'name': 'us_state_codes',
        'url': 'https://raw.githubusercontent.com/datasets/us-state-names/master/data/us-state-names.csv',
        'description': '美国州代码数据',
        'country': 'US',
        'format': 'csv'
    },
    {
        'name': 'uk_postcode_sample',
        'url': 'https://raw.githubusercontent.com/datasets/uk-postcodes/master/data/sample.csv',
        'description': '英国邮编样本数据',
        'country': 'UK',
        'format': 'csv'
    },
    {
        'name': 'canada_provinces',
        'url': 'https://raw.githubusercontent.com/datasets/country-codes/master/data/country-codes.csv',
        'description': '国家代码数据',
        'country': 'CA',
        'format': 'csv'
    },
    {
        'name': 'world_cities',
        'url': 'https://raw.githubusercontent.com/datasets/world-cities/master/data/world-cities.csv',
        'description': '世界城市数据',
        'country': 'WORLD',
        'format': 'csv'
    },
    {
        'name': 'currency_codes',
        'url': 'https://raw.githubusercontent.com/datasets/currency-codes/master/data/codes-all.csv',
        'description': '世界货币代码',
        'country': 'WORLD',
        'format': 'csv'
    }
]

# ==================== XML数据源 ====================

XML_SOURCES = [
    {
        'name': 'rss_bbc_news',
        'url': 'http://feeds.bbci.co.uk/news/rss.xml',
        'description': 'BBC新闻RSS Feed',
        'type': 'rss'
    },
    {
        'name': 'rss_cnn_world',
        'url': 'http://rss.cnn.com/rss/edition.rss',
        'description': 'CNN世界新闻RSS Feed',
        'type': 'rss'
    },
    {
        'name': 'nasa_rss_breaking',
        'url': 'https://www.nasa.gov/rss/dyn/breaking_news.rss',
        'description': 'NASA突发新闻RSS Feed',
        'type': 'rss'
    },
    {
        'name': 'nasa_rss_image',
        'url': 'https://www.nasa.gov/rss/dyn/lg_image_of_the_day.rss',
        'description': 'NASA每日图片RSS Feed',
        'type': 'rss'
    },
    {
        'name': 'worldbank_countries',
        'url': 'https://api.worldbank.org/v2/country?format=xml&per_page=50',
        'description': '世界银行国家列表XML',
        'type': 'worldbank'
    },
    {
        'name': 'worldbank_indicators',
        'url': 'https://api.worldbank.org/v2/indicator?format=xml&per_page=20',
        'description': '世界银行指标列表XML',
        'type': 'worldbank'
    },
    {
        'name': 'ecb_exchange_rates',
        'url': 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml',
        'description': '欧洲央行每日汇率XML',
        'type': 'ecb'
    }
]

# ==================== 数据源分组（用于子菜单）====================

JSON_SOURCE_GROUPS = {
    'github': {
        'name': 'GitHub API',
        'description': '收集GitHub用户和仓库数据',
        'sources': ['github']
    },
    'public': {
        'name': '公共API',
        'description': 'Wikipedia, NASA, Wikidata等公共数据',
        'sources': PUBLIC_API_SOURCES
    },
    'financial': {
        'name': '金融API',
        'description': '加密货币价格, 汇率数据',
        'sources': FINANCIAL_API_SOURCES
    },
    'weather': {
        'name': '天气API',
        'description': '城市天气数据',
        'sources': WEATHER_API_SOURCES
    }
}

XML_SOURCE_GROUPS = {
    'rss': {
        'name': 'RSS新闻源',
        'description': 'BBC, CNN, NASA等新闻订阅',
        'sources': [s for s in XML_SOURCES if s['type'] == 'rss']
    },
    'worldbank': {
        'name': '世界银行XML',
        'description': '国家列表, 经济指标等',
        'sources': [s for s in XML_SOURCES if s['type'] == 'worldbank']
    },
    'financial_xml': {
        'name': '金融XML',
        'description': '欧洲央行汇率等',
        'sources': [s for s in XML_SOURCES if s['type'] == 'ecb']
    }
}






















