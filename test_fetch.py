"""
Quick test script to verify data fetching
Run: python test_fetch.py
"""

import yfinance as yf
import time

print("Testing Yahoo Finance data fetching...\n")

tickers_to_test = {
    'Gold': 'GC=F',
    'Silver': 'SI=F', 
    'USD/INR': 'USDINR=X',
    'NIFTY': '^NSEI',
    'VIX': '^VIX',
}

for name, ticker in tickers_to_test.items():
    print(f"Fetching {name} ({ticker})...")
    try:
        time.sleep(1)
        stock = yf.Ticker(ticker)
        data = stock.history(period='5d', interval='1d')
        
        if not data.empty:
            print(f"✅ {name}: Success - {len(data)} days of data")
            print(f"   Latest close: {data['Close'].iloc[-1]:.2f}\n")
        else:
            print(f"❌ {name}: No data returned\n")
    except Exception as e:
        print(f"❌ {name}: Error - {e}\n")

print("\nIf all failed, Yahoo Finance may be blocking. Wait 5 minutes and try again.")
print("Alternative: Use different ticker symbols or set up FRED API key.")
