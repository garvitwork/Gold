"""
FastAPI Backend for Gold & Silver Price Prediction App
Production-ready API with real-time data fetching and analysis
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
from datetime import datetime

# Import our existing modules
from data_fetcher import DataFetcher
from analyzer import MarketAnalyzer

# Initialize FastAPI app
app = FastAPI(
    title="Gold & Silver Price Prediction API",
    description="Real-time gold and silver price analysis for Indian market with advanced signals",
    version="1.0.0"
)

# CORS configuration - adjust origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    message: str

class GoldPriceResponse(BaseModel):
    gold_inr_10g: float
    gold_usd_10g: float
    usdinr: float
    timestamp: str

class MarketIndicatorsResponse(BaseModel):
    real_yield: Optional[float]
    dxy: Optional[float]
    vix: Optional[float]
    gold_silver_ratio: Optional[float]
    timestamp: str

class SignalResponse(BaseModel):
    signal: str
    status: str
    value: Optional[float]

class DipDetectionResponse(BaseModel):
    recommendation: str
    bullish_count: int
    bearish_count: int
    neutral_count: int
    checklist: Dict[str, Any]

# Initialize data fetcher (singleton pattern)
data_fetcher = None

def get_data_fetcher():
    """Get or create data fetcher instance"""
    global data_fetcher
    if data_fetcher is None:
        data_fetcher = DataFetcher()
    return data_fetcher


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "Gold & Silver Price Prediction API is running"
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check with API status"""
    try:
        fetcher = get_data_fetcher()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "message": "All systems operational"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


@app.get("/api/gold-price", response_model=GoldPriceResponse)
async def get_gold_price():
    """
    Get current Indian gold price per 10 grams
    Includes import duty, GST, and retail markup
    """
    try:
        fetcher = get_data_fetcher()
        indian_gold = fetcher.calculate_indian_gold_price()
        
        if indian_gold.empty:
            raise HTTPException(status_code=503, detail="Unable to fetch gold price data")
        
        latest = indian_gold.iloc[-1]
        
        return {
            "gold_inr_10g": round(latest['gold_inr'], 2),
            "gold_usd_10g": round(latest['gold_usd_10g'], 2),
            "usdinr": round(latest['usdinr'], 2),
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching gold price: {str(e)}")


@app.get("/api/market-indicators", response_model=MarketIndicatorsResponse)
async def get_market_indicators():
    """
    Get all market indicators (Real Yield, DXY, VIX, Gold-Silver Ratio)
    """
    try:
        fetcher = get_data_fetcher()
        indicators = fetcher.get_market_indicators()
        
        # Extract latest values
        real_yield_val = None
        if not indicators['real_yield'].empty:
            real_yield_val = float(indicators['real_yield']['real_yield'].iloc[-1])
        
        dxy_val = None
        if not indicators['dxy'].empty:
            dxy_val = float(indicators['dxy']['value'].iloc[-1])
        
        vix_val = None
        if not indicators['vix'].empty:
            vix_val = float(indicators['vix'].iloc[-1, 0])
        
        ratio_val = None
        if not indicators['gold_silver_ratio'].empty:
            ratio_val = float(indicators['gold_silver_ratio']['ratio'].iloc[-1])
        
        return {
            "real_yield": real_yield_val,
            "dxy": dxy_val,
            "vix": vix_val,
            "gold_silver_ratio": ratio_val,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching indicators: {str(e)}")


@app.get("/api/analysis/real-yield", response_model=SignalResponse)
async def analyze_real_yield():
    """Analyze US Real Interest Rates signal"""
    try:
        fetcher = get_data_fetcher()
        indicators = fetcher.get_market_indicators()
        analyzer = MarketAnalyzer(indicators)
        result = analyzer.analyze_real_yield()
        
        return {
            "signal": result['signal'],
            "status": result['status'],
            "value": result.get('value')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing real yield: {str(e)}")


@app.get("/api/analysis/dxy", response_model=SignalResponse)
async def analyze_dxy():
    """Analyze US Dollar strength (DXY) signal"""
    try:
        fetcher = get_data_fetcher()
        indicators = fetcher.get_market_indicators()
        analyzer = MarketAnalyzer(indicators)
        result = analyzer.analyze_dxy()
        
        return {
            "signal": result['signal'],
            "status": result['status'],
            "value": result.get('value')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing DXY: {str(e)}")


@app.get("/api/analysis/risk-sentiment", response_model=SignalResponse)
async def analyze_risk_sentiment():
    """Analyze stock market risk sentiment (VIX)"""
    try:
        fetcher = get_data_fetcher()
        indicators = fetcher.get_market_indicators()
        analyzer = MarketAnalyzer(indicators)
        result = analyzer.analyze_risk_sentiment()
        
        return {
            "signal": result['signal'],
            "status": result['status'],
            "value": result.get('vix')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing risk sentiment: {str(e)}")


@app.get("/api/analysis/inr", response_model=SignalResponse)
async def analyze_inr():
    """Analyze INR vs USD movement"""
    try:
        fetcher = get_data_fetcher()
        indicators = fetcher.get_market_indicators()
        analyzer = MarketAnalyzer(indicators)
        result = analyzer.analyze_inr()
        
        return {
            "signal": result['signal'],
            "status": result['status'],
            "value": result.get('value')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing INR: {str(e)}")


@app.get("/api/analysis/gold-silver-ratio", response_model=SignalResponse)
async def analyze_gold_silver_ratio():
    """Analyze Gold-Silver ratio"""
    try:
        fetcher = get_data_fetcher()
        indicators = fetcher.get_market_indicators()
        analyzer = MarketAnalyzer(indicators)
        result = analyzer.analyze_gold_silver_ratio()
        
        return {
            "signal": result['signal'],
            "status": result['status'],
            "value": result.get('value')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing gold-silver ratio: {str(e)}")


@app.get("/api/analysis/full", response_model=Dict[str, Any])
async def get_full_analysis():
    """
    Get complete market analysis with all signals
    This is the main endpoint for comprehensive analysis
    """
    try:
        fetcher = get_data_fetcher()
        indicators = fetcher.get_market_indicators()
        analyzer = MarketAnalyzer(indicators)
        analysis = analyzer.run_full_analysis()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "real_yield": analysis['real_yield'],
            "dxy": analysis['dxy'],
            "risk_sentiment": analysis['risk_sentiment'],
            "inr": analysis['inr'],
            "gold_silver_ratio": analysis['gold_silver_ratio'],
            "divergence": analysis['divergence'],
            "dip_score": analysis['dip_score']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in full analysis: {str(e)}")


@app.get("/api/dip-detection", response_model=DipDetectionResponse)
async def get_dip_detection():
    """
    Get dip detection score and recommendation
    Returns GOOD ENTRY POINT / NEUTRAL / AVOID based on signals
    """
    try:
        fetcher = get_data_fetcher()
        indicators = fetcher.get_market_indicators()
        analyzer = MarketAnalyzer(indicators)
        dip_score = analyzer.get_dip_detection_score()
        
        neutral_count = 6 - dip_score['bullish_count'] - dip_score['bearish_count']
        
        return {
            "recommendation": dip_score['recommendation'],
            "bullish_count": dip_score['bullish_count'],
            "bearish_count": dip_score['bearish_count'],
            "neutral_count": neutral_count,
            "checklist": dip_score['checklist']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in dip detection: {str(e)}")


@app.get("/api/historical/gold-price")
async def get_historical_gold_price(days: int = 30):
    """
    Get historical gold price data
    Query param: days (default: 30, max: 365)
    """
    try:
        if days > 365:
            raise HTTPException(status_code=400, detail="Maximum 365 days of historical data")
        
        fetcher = get_data_fetcher()
        indian_gold = fetcher.calculate_indian_gold_price()
        
        if indian_gold.empty:
            raise HTTPException(status_code=503, detail="Unable to fetch historical data")
        
        # Get last N days
        recent_data = indian_gold.tail(days)
        
        return {
            "data": [
                {
                    "date": idx.strftime("%Y-%m-%d"),
                    "gold_inr_10g": round(row['gold_inr'], 2),
                    "gold_usd_10g": round(row['gold_usd_10g'], 2),
                    "usdinr": round(row['usdinr'], 2)
                }
                for idx, row in recent_data.iterrows()
            ],
            "count": len(recent_data),
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching historical data: {str(e)}")


# Run with: uvicorn api:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
