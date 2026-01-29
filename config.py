"""
Configuration file for Gold/Silver Price Prediction App
Contains all constants, API endpoints, and helper functions
"""

import datetime as dt

# API Endpoints
FRED_API_KEY = "5cf3188d580f74f1d25740119d36ac97"  # REQUIRED: Get free key from https://fred.stlouisfed.org/
ALPHA_VANTAGE_KEY = "HS0555JLJFI1VU25"  # Get free key from https://www.alphavantage.co/

# NOTE: If FRED_API_KEY is not set, those indicators will be unavailable
# Yahoo Finance data works without API key

# Data sources
ENDPOINTS = {
    'us_10y': 'DGS10',  # US 10-Year Treasury
    'us_cpi': 'CPIAUCSL',  # US CPI
    'fed_rate': 'FEDFUNDS',  # Federal Funds Rate
    'dxy': 'DTWEXBGS',  # Dollar Index
    'vix': '^VIX',  # Volatility Index
    'sp500': '^GSPC',  # S&P 500
    'nifty': '^NSEI',  # Nifty 50
    'gold': 'GC=F',  # Gold Futures
    'silver': 'SI=F',  # Silver Futures
    'usdinr': 'USDINR=X',  # USD to INR
}

# Thresholds for analysis
THRESHOLDS = {
    'vix_low': 13,
    'gold_silver_high': 85,
    'gold_silver_low': 65,
    'real_yield_critical': 2.0,
}

# Date range for data fetching
DEFAULT_PERIOD = '1y'
DEFAULT_START = (dt.datetime.now() - dt.timedelta(days=365)).strftime('%Y-%m-%d')
DEFAULT_END = dt.datetime.now().strftime('%Y-%m-%d')

# Chart colors
COLORS = {
    'primary': '#FFD700',  # Gold
    'secondary': '#C0C0C0',  # Silver
    'positive': '#00C853',
    'negative': '#FF1744',
    'neutral': '#2196F3',
}
