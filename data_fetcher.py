"""
Data fetching module for Gold/Silver Price Prediction App
Uses yfinance API with improved rate limiting and retry logic
"""

import yfinance as yf
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
from config import FRED_API_KEY, ENDPOINTS, DEFAULT_START, DEFAULT_END
import warnings
warnings.filterwarnings('ignore')

class DataFetcher:
    """Fetch real-world financial data using yfinance"""
    
    def __init__(self):
        self.fred_base = "https://api.stlouisfed.org/fred/series/observations"
        self.cache = {}  # Simple in-memory cache
        self.cache_timeout = 300  # 5 minutes cache
        
    def get_yahoo_data(self, ticker, period='1y', interval='1d', retries=3):
        """Fetch data from Yahoo Finance with proper error handling and retry logic"""
        # Check cache first
        cache_key = f"{ticker}_{period}_{interval}"
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if time.time() - cached_time < self.cache_timeout:
                print(f"🔄 Using cached data for {ticker}")
                return cached_data
        
        for attempt in range(retries):
            try:
                # Increase delay between requests to avoid rate limiting
                time.sleep(1.5 + (attempt * 1))  # Progressive backoff: 1.5s, 2.5s, 3.5s
                
                # Try Ticker method first (more reliable)
                stock = yf.Ticker(ticker)
                hist = stock.history(period=period, interval=interval)
                
                if not hist.empty and 'Close' in hist.columns:
                    if hist.index.tz is not None:
                        hist.index = hist.index.tz_localize(None)
                    result = hist[['Close']].rename(columns={'Close': ticker})
                    print(f"✅ {ticker}: Fetched {len(hist)} data points")
                    
                    # Cache the result
                    self.cache[cache_key] = (result, time.time())
                    return result
                
                # If Ticker method failed, try download method
                time.sleep(1)
                data = yf.download(
                    ticker, 
                    period=period, 
                    interval=interval,
                    progress=False,
                    show_errors=False
                )
                
                if not data.empty and 'Close' in data.columns:
                    data.index = pd.to_datetime(data.index)
                    if data.index.tz is not None:
                        data.index = data.index.tz_localize(None)
                    result = data[['Close']].rename(columns={'Close': ticker})
                    print(f"✅ {ticker}: Fetched {len(data)} data points")
                    
                    # Cache the result
                    self.cache[cache_key] = (result, time.time())
                    return result
                
                # If no data on this attempt, try again
                if attempt < retries - 1:
                    print(f"⚠️ Retry {attempt + 1}/{retries} for {ticker}...")
                    time.sleep(3)  # Wait before retry
                    continue
                    
            except Exception as e:
                if attempt < retries - 1:
                    print(f"⚠️ Error fetching {ticker} (attempt {attempt + 1}/{retries}): {str(e)[:50]}")
                    time.sleep(3)  # Wait before retry
                    continue
                else:
                    print(f"❌ Failed to fetch {ticker} after {retries} attempts: {str(e)[:50]}")
        
        print(f"⚠️ No data available for {ticker} after {retries} attempts")
        return pd.DataFrame()
    
    def get_fred_data(self, series_id, start_date=DEFAULT_START, end_date=DEFAULT_END):
        """Fetch data from FRED API"""
        if FRED_API_KEY == "YOUR_FRED_API_KEY" or not FRED_API_KEY:
            print(f"⚠️ FRED API key not configured for {series_id}")
            return pd.DataFrame()
        
        try:
            params = {
                'series_id': series_id,
                'api_key': FRED_API_KEY,
                'file_type': 'json',
                'observation_start': start_date,
                'observation_end': end_date,
            }
            response = requests.get(self.fred_base, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'observations' in data and len(data['observations']) > 0:
                    df = pd.DataFrame(data['observations'])
                    df['date'] = pd.to_datetime(df['date'])
                    df['value'] = pd.to_numeric(df['value'], errors='coerce')
                    df = df[['date', 'value']].set_index('date')
                    df = df.dropna()
                    if not df.empty:
                        print(f"✅ {series_id}: Fetched {len(df)} data points")
                        return df
                    else:
                        print(f"⚠️ {series_id}: No valid data after cleaning")
                else:
                    print(f"⚠️ {series_id}: API returned empty observations")
            elif response.status_code == 400:
                print(f"❌ {series_id}: Invalid API key or parameters")
            elif response.status_code == 429:
                print(f"⚠️ {series_id}: Rate limit exceeded")
            else:
                print(f"❌ FRED API error for {series_id}: Status {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Error fetching {series_id}: {e}")
        
        return pd.DataFrame()
    
    def get_us_treasury_10y(self):
        """US 10-Year Treasury Yield"""
        return self.get_fred_data(ENDPOINTS['us_10y'])
    
    def get_us_cpi(self):
        """US Consumer Price Index"""
        return self.get_fred_data(ENDPOINTS['us_cpi'])
    
    def get_fed_rate(self):
        """Federal Funds Rate"""
        return self.get_fred_data(ENDPOINTS['fed_rate'])
    
    def get_dxy(self):
        """Dollar Index (DXY)"""
        return self.get_fred_data(ENDPOINTS['dxy'])
    
    def get_vix(self):
        """Volatility Index"""
        return self.get_yahoo_data(ENDPOINTS['vix'])
    
    def get_sp500(self):
        """S&P 500 Index"""
        return self.get_yahoo_data(ENDPOINTS['sp500'])
    
    def get_nifty(self):
        """Nifty 50 Index"""
        return self.get_yahoo_data(ENDPOINTS['nifty'])
    
    def get_gold_price(self):
        """Gold Futures Price"""
        return self.get_yahoo_data(ENDPOINTS['gold'])
    
    def get_silver_price(self):
        """Silver Futures Price"""
        return self.get_yahoo_data(ENDPOINTS['silver'])
    
    def get_usdinr(self):
        """USD to INR Exchange Rate"""
        return self.get_yahoo_data(ENDPOINTS['usdinr'])
    
    def calculate_real_yield(self):
        """Calculate Real Yield = 10Y Treasury - Inflation Rate"""
        try:
            treasury = self.get_us_treasury_10y()
            cpi = self.get_us_cpi()
            
            if treasury.empty or cpi.empty:
                print("⚠️ Treasury or CPI data is empty")
                return pd.DataFrame()
            
            print(f"   CPI data points: {len(cpi)}, Treasury data points: {len(treasury)}")
            
            # CPI is monthly - forward fill to daily
            cpi_daily = cpi.resample('D').ffill()
            
            # Calculate inflation rate
            # If we have enough data (12+ months), use YoY
            if len(cpi) >= 12:
                cpi_yoy = cpi_daily.pct_change(periods=365) * 100
            else:
                # Use month-over-month annualized
                cpi_mom = cpi_daily.pct_change(periods=30) * 12 * 100  # Annualized
                cpi_yoy = cpi_mom
            
            # Merge treasury with inflation
            merged = treasury.merge(cpi_yoy, left_index=True, right_index=True, how='inner')
            
            if merged.empty:
                print("⚠️ Merge failed - no overlapping dates")
                return pd.DataFrame()
            
            merged.columns = ['treasury', 'inflation']
            
            # Filter out NaN values before calculation
            merged = merged.dropna()
            
            if merged.empty:
                print("⚠️ No valid data after removing NaN")
                return pd.DataFrame()
            
            merged['real_yield'] = merged['treasury'] - merged['inflation']
            
            result = merged[['real_yield']]
            
            if not result.empty:
                print(f"✅ Real Yield: Calculated {len(result)} data points")
                print(f"   Latest Real Yield: {result['real_yield'].iloc[-1]:.2f}%")
                print(f"   Latest Treasury: {merged['treasury'].iloc[-1]:.2f}%")
                print(f"   Latest Inflation: {merged['inflation'].iloc[-1]:.2f}%")
            else:
                print("⚠️ Real Yield calculation resulted in empty data")
            
            return result
            
        except Exception as e:
            print(f"❌ Error calculating real yield: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def calculate_gold_silver_ratio(self):
        """Calculate Gold/Silver Ratio"""
        try:
            gold = self.get_gold_price()
            silver = self.get_silver_price()
            
            if gold.empty or silver.empty:
                return pd.DataFrame()
            
            merged = gold.merge(silver, left_index=True, right_index=True, how='inner')
            merged.columns = ['gold', 'silver']
            merged['ratio'] = merged['gold'] / merged['silver']
            
            return merged[['ratio']]
        except Exception as e:
            print(f"Error calculating gold/silver ratio: {e}")
            return pd.DataFrame()
    
    def calculate_indian_gold_price(self):
        """Calculate Indian Gold Price = Global Gold * USD/INR (per 10 grams) + Indian factors"""
        try:
            gold = self.get_gold_price()
            usdinr = self.get_usdinr()
            
            if gold.empty or usdinr.empty:
                return pd.DataFrame()
            
            merged = gold.merge(usdinr, left_index=True, right_index=True, how='inner')
            merged.columns = ['gold_usd', 'usdinr']
            
            # Convert from per oz to per 10 grams
            # 1 troy oz = 31.1035 grams, so 10 grams = 10/31.1035 oz
            OZ_TO_10G = 10 / 31.1035
            
            # Indian gold retail price factors:
            # 1. Import duty: ~15% (varies, but average)
            # 2. GST: 3%
            # 3. Making charges & retail markup: ~5-8%
            # Total markup: approximately 1.23 to 1.26
            INDIAN_MARKUP = 1.13  # 13% total (duty + GST + small markup)
            
            # Base gold price in INR per 10g
            base_price = merged['gold_usd'] * merged['usdinr'] * OZ_TO_10G
            
            # Apply Indian factors for retail price
            merged['gold_inr'] = base_price * INDIAN_MARKUP
            merged['gold_usd_10g'] = merged['gold_usd'] * OZ_TO_10G
            
            print(f"   Gold calculation: ${merged['gold_usd'].iloc[-1]:.2f}/oz → ₹{merged['gold_inr'].iloc[-1]:.0f}/10g")
            
            return merged[['gold_inr', 'gold_usd_10g', 'usdinr']]
        except Exception as e:
            print(f"Error calculating Indian gold price: {e}")
            return pd.DataFrame()
    
    def get_market_indicators(self):
        """Get all market indicators in one call with sequential fetching to avoid rate limits"""
        print("📡 Fetching data from APIs...")
        
        indicators = {}
        
        # Fetch sequentially with delays to avoid rate limiting
        print("📊 Fetching FRED data (US Treasury, CPI, DXY)...")
        indicators['real_yield'] = self.calculate_real_yield()
        time.sleep(1)
        indicators['dxy'] = self.get_dxy()
        
        print("💰 Fetching Yahoo Finance data (Gold, Silver, Currencies)...")
        time.sleep(2)
        indicators['gold'] = self.get_gold_price()
        time.sleep(2)
        indicators['silver'] = self.get_silver_price()
        time.sleep(2)
        indicators['usdinr'] = self.get_usdinr()
        
        print("📈 Fetching market indices (VIX, S&P500, NIFTY)...")
        time.sleep(2)
        indicators['vix'] = self.get_vix()
        time.sleep(2)
        indicators['sp500'] = self.get_sp500()
        time.sleep(2)
        indicators['nifty'] = self.get_nifty()
        
        print("🔢 Calculating ratios...")
        indicators['gold_silver_ratio'] = self.calculate_gold_silver_ratio()
        indicators['indian_gold'] = self.calculate_indian_gold_price()
        
        print("✅ Data fetch complete!")
        return indicators
