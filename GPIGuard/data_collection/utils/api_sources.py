#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API Data Source Configuration
Centrally manage all API data source URLs and configurations
"""

# ==================== JSON Data Sources ====================

# GitHub API Data Source
GITHUB_SOURCES = {
    'users': [
        {'username': 'torvalds', 'description': 'Linus Torvalds'},
        {'username': 'gvanrossum', 'description': 'Python Creator'},
        {'username': 'octocat', 'description': 'GitHub Mascot'},
        {'username': 'defunkt', 'description': 'GitHub Co-founder'},
        {'username': 'mojombo', 'description': 'GitHub Co-founder'},
        {'username': 'pjhyett', 'description': 'GitHub Early Employee'},
        {'username': 'wycats', 'description': 'Ember.js Creator'},
        {'username': 'dhh', 'description': 'Ruby on Rails Creator'},
    ]
}

# Public API Data Sources
PUBLIC_API_SOURCES = [
    {
        'name': 'worldbank_population',
        'urls': [
            'https://api.worldbank.org/v2/country/US/indicator/SP.POP.TOTL?format=json&date=2020:2023',
            'https://api.worldbank.org/v2/country/CN/indicator/SP.POP.TOTL?format=json&date=2020:2023',
            'https://api.worldbank.org/v2/country/GB/indicator/SP.POP.TOTL?format=json&date=2020:2023'
        ],
        'description': 'World Bank Population Data',
        'type': 'worldbank'
    },
    {
        'name': 'wikipedia_articles',
        'urls': [
            'https://en.wikipedia.org/w/api.php?action=query&titles=Python_(programming_language)&format=json&prop=extracts&exintro=true',
            'https://en.wikipedia.org/w/api.php?action=query&titles=Artificial_intelligence&format=json&prop=extracts&exintro=true',
            'https://en.wikipedia.org/w/api.php?action=query&titles=Machine_learning&format=json&prop=extracts&exintro=true'
        ],
        'description': 'Wikipedia Article Data',
        'type': 'wikipedia'
    },
    {
        'name': 'wikidata_entities',
        'urls': [
            'https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q42&format=json',
            'https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q5&format=json',
            'https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q1860&format=json'
        ],
        'description': 'Wikidata Entity Data',
        'type': 'wikidata'
    },
    {
        'name': 'nasa_apod',
        'urls': [
            'https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY&count=3'
        ],
        'description': 'NASA Astronomy Picture of the Day',
        'type': 'nasa'
    }
]

# Financial API Data Sources
FINANCIAL_API_SOURCES = [
    {
        'name': 'crypto_prices',
        'urls': [
            'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,cardano&vs_currencies=usd,eur',
            'https://api.coingecko.com/api/v3/coins/bitcoin',
            'https://api.coingecko.com/api/v3/coins/ethereum'
        ],
        'description': 'Cryptocurrency Price Data',
        'type': 'crypto'
    },
    {
        'name': 'crypto_markets',
        'urls': [
            'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1',
            'https://api.coingecko.com/api/v3/global'
        ],
        'description': 'Cryptocurrency Market Data',
        'type': 'crypto'
    },
    {
        'name': 'exchange_rates',
        'urls': [
            'https://api.exchangerate-api.com/v4/latest/USD',
            'https://api.exchangerate-api.com/v4/latest/EUR',
            'https://api.exchangerate-api.com/v4/latest/GBP'
        ],
        'description': 'Exchange Rate Data',
        'type': 'forex'
    }
]

# Weather API Data Sources
WEATHER_API_SOURCES = [
    {
        'name': 'weather_free',
        'urls': [
            'https://wttr.in/London?format=j1',
            'https://wttr.in/NewYork?format=j1',
            'https://wttr.in/Tokyo?format=j1'
        ],
        'description': 'Free Weather Data',
        'type': 'weather'
    }
]

# ==================== CSV Data Sources ====================

GOVERNMENT_CSV_SOURCES = [
    {
        'name': 'us_federal_holidays',
        'url': 'https://raw.githubusercontent.com/datasets/us-federal-holidays/master/data/us-federal-holidays.csv',
        'description': 'US Federal Holidays Data',
        'country': 'US',
        'format': 'csv'
    },
    {
        'name': 'us_state_codes',
        'url': 'https://raw.githubusercontent.com/datasets/us-state-names/master/data/us-state-names.csv',
        'description': 'US State Codes Data',
        'country': 'US',
        'format': 'csv'
    },
    {
        'name': 'uk_postcode_sample',
        'url': 'https://raw.githubusercontent.com/datasets/uk-postcodes/master/data/sample.csv',
        'description': 'UK Postcode Sample Data',
        'country': 'UK',
        'format': 'csv'
    },
    {
        'name': 'canada_provinces',
        'url': 'https://raw.githubusercontent.com/datasets/country-codes/master/data/country-codes.csv',
        'description': 'Country Codes Data',
        'country': 'CA',
        'format': 'csv'
    },
    {
        'name': 'world_cities',
        'url': 'https://raw.githubusercontent.com/datasets/world-cities/master/data/world-cities.csv',
        'description': 'World Cities Data',
        'country': 'WORLD',
        'format': 'csv'
    },
    {
        'name': 'currency_codes',
        'url': 'https://raw.githubusercontent.com/datasets/currency-codes/master/data/codes-all.csv',
        'description': 'World Currency Codes',
        'country': 'WORLD',
        'format': 'csv'
    }
]

# ==================== XML Data Sources ====================

XML_SOURCES = [
    {
        'name': 'rss_bbc_news',
        'url': 'http://feeds.bbci.co.uk/news/rss.xml',
        'description': 'BBC News RSS Feed',
        'type': 'rss'
    },
    {
        'name': 'rss_cnn_world',
        'url': 'http://rss.cnn.com/rss/edition.rss',
        'description': 'CNN World News RSS Feed',
        'type': 'rss'
    },
    {
        'name': 'nasa_rss_breaking',
        'url': 'https://www.nasa.gov/rss/dyn/breaking_news.rss',
        'description': 'NASA Breaking News RSS Feed',
        'type': 'rss'
    },
    {
        'name': 'nasa_rss_image',
        'url': 'https://www.nasa.gov/rss/dyn/lg_image_of_the_day.rss',
        'description': 'NASA Daily Image RSS Feed',
        'type': 'rss'
    },
    {
        'name': 'worldbank_countries',
        'url': 'https://api.worldbank.org/v2/country?format=xml&per_page=50',
        'description': 'World Bank Country List XML',
        'type': 'worldbank'
    },
    {
        'name': 'worldbank_indicators',
        'url': 'https://api.worldbank.org/v2/indicator?format=xml&per_page=20',
        'description': 'World Bank Indicators List XML',
        'type': 'worldbank'
    },
    {
        'name': 'ecb_exchange_rates',
        'url': 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml',
        'description': 'ECB Daily Exchange Rates XML',
        'type': 'ecb'
    }
]

# ==================== Data Source Groups (for submenus) ====================

JSON_SOURCE_GROUPS = {
    'github': {
        'name': 'GitHub API',
        'description': 'Collect GitHub users and repository data',
        'sources': ['github']
    },
    'public': {
        'name': 'Public API',
        'description': 'Wikipedia, NASA, Wikidata and other public data',
        'sources': PUBLIC_API_SOURCES
    },
    'financial': {
        'name': 'Financial API',
        'description': 'Cryptocurrency prices, exchange rate data',
        'sources': FINANCIAL_API_SOURCES
    },
    'weather': {
        'name': 'Weather API',
        'description': 'City weather data',
        'sources': WEATHER_API_SOURCES
    }
}

XML_SOURCE_GROUPS = {
    'rss': {
        'name': 'RSS News Sources',
        'description': 'BBC, CNN, NASA and other news subscriptions',
        'sources': [s for s in XML_SOURCES if s['type'] == 'rss']
    },
    'worldbank': {
        'name': 'World Bank XML',
        'description': 'Country list, economic indicators, etc.',
        'sources': [s for s in XML_SOURCES if s['type'] == 'worldbank']
    },
    'financial_xml': {
        'name': 'Financial XML',
        'description': 'ECB exchange rates, etc.',
        'sources': [s for s in XML_SOURCES if s['type'] == 'ecb']
    }
}






















