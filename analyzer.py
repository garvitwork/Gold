"""
Analysis module for Gold/Silver Price Prediction
Implements all signal detection logic from PART 1, 2, and 3
"""

import pandas as pd
import numpy as np
from config import THRESHOLDS

class MarketAnalyzer:
    """Analyze market conditions and detect dip signals"""
    
    def __init__(self, indicators):
        self.indicators = indicators
        self.signals = {}
        
    def analyze_real_yield(self):
        """PART 1.1: Rise in US Real Interest Rates"""
        try:
            real_yield = self.indicators.get('real_yield')
            if real_yield.empty:
                return {
                    'status': 'Real yield data unavailable - FRED API key may be invalid', 
                    'signal': 'NEUTRAL', 
                    'value': None,
                    'change': 0,
                    'critical': False
                }
            
            current = real_yield['real_yield'].iloc[-1]
            prev_month = real_yield['real_yield'].iloc[-30] if len(real_yield) > 30 else real_yield['real_yield'].iloc[0]
            change = current - prev_month
            
            if change > 0.5:
                signal = 'BEARISH'
                status = f'Real yield rising ({change:.2f}% increase) - Negative for gold'
            elif change < -0.5:
                signal = 'BULLISH'
                status = f'Real yield falling ({change:.2f}% decrease) - Positive for gold'
            else:
                signal = 'NEUTRAL'
                status = f'Real yield stable ({change:.2f}% change)'
            
            return {
                'status': status,
                'signal': signal,
                'value': current,
                'change': change,
                'critical': current > THRESHOLDS['real_yield_critical']
            }
        except Exception as e:
            return {
                'status': 'Error calculating real yield - Check FRED API key', 
                'signal': 'NEUTRAL', 
                'value': None,
                'change': 0,
                'critical': False
            }
    
    def analyze_dxy(self):
        """PART 1.2: Strengthening US Dollar"""
        try:
            dxy = self.indicators.get('dxy')
            if dxy.empty:
                return {'status': 'No Data', 'signal': 'NEUTRAL', 'value': None}
            
            current = dxy['value'].iloc[-1]
            prev_month = dxy['value'].iloc[-30] if len(dxy) > 30 else dxy['value'].iloc[0]
            change_pct = ((current - prev_month) / prev_month) * 100
            
            if change_pct > 2:
                signal = 'BEARISH'
                status = f'DXY strengthening ({change_pct:.2f}%) - Negative for gold'
            elif change_pct < -2:
                signal = 'BULLISH'
                status = f'DXY weakening ({change_pct:.2f}%) - Positive for gold'
            else:
                signal = 'NEUTRAL'
                status = f'DXY stable ({change_pct:.2f}% change)'
            
            return {
                'status': status,
                'signal': signal,
                'value': current,
                'change_pct': change_pct
            }
        except Exception as e:
            return {'status': f'Error: {e}', 'signal': 'NEUTRAL', 'value': None}
    
    def analyze_risk_sentiment(self):
        """PART 1.3: Stock Market Risk-ON Phase"""
        try:
            vix = self.indicators.get('vix')
            sp500 = self.indicators.get('sp500')
            nifty = self.indicators.get('nifty')
            
            signals = []
            
            # VIX analysis
            if not vix.empty:
                current_vix = vix.iloc[-1, 0]
                if current_vix < THRESHOLDS['vix_low']:
                    signals.append(f'VIX low ({current_vix:.2f}) - Risk-ON, bearish for gold')
                    vix_signal = 'BEARISH'
                elif current_vix > 20:
                    signals.append(f'VIX high ({current_vix:.2f}) - Risk-OFF, bullish for gold')
                    vix_signal = 'BULLISH'
                else:
                    signals.append(f'VIX neutral ({current_vix:.2f})')
                    vix_signal = 'NEUTRAL'
            else:
                vix_signal = 'NEUTRAL'
            
            # Equity trend
            if not sp500.empty:
                sp_return = ((sp500.iloc[-1, 0] - sp500.iloc[-30, 0]) / sp500.iloc[-30, 0] * 100) if len(sp500) > 30 else 0
                if sp_return > 5:
                    signals.append(f'S&P rallying (+{sp_return:.2f}%) - Bearish for gold')
            
            if not nifty.empty:
                nifty_return = ((nifty.iloc[-1, 0] - nifty.iloc[-30, 0]) / nifty.iloc[-30, 0] * 100) if len(nifty) > 30 else 0
                if nifty_return > 5:
                    signals.append(f'NIFTY rallying (+{nifty_return:.2f}%) - Bearish for gold')
            
            return {
                'status': ' | '.join(signals) if signals else 'No clear risk sentiment',
                'signal': vix_signal,
                'vix': current_vix if not vix.empty else None
            }
        except Exception as e:
            return {'status': f'Error: {e}', 'signal': 'NEUTRAL'}
    
    def analyze_inr(self):
        """PART 1.5: INR vs USD Movement"""
        try:
            usdinr = self.indicators.get('usdinr')
            if usdinr.empty:
                return {'status': 'No Data', 'signal': 'NEUTRAL', 'value': None}
            
            current = usdinr.iloc[-1, 0]
            prev_month = usdinr.iloc[-30, 0] if len(usdinr) > 30 else usdinr.iloc[0, 0]
            change_pct = ((current - prev_month) / prev_month) * 100
            
            if change_pct < -1:
                signal = 'BEARISH'
                status = f'INR strengthening ({change_pct:.2f}%) - Indian gold cheaper'
            elif change_pct > 1:
                signal = 'BULLISH'
                status = f'INR weakening ({change_pct:.2f}%) - Indian gold expensive'
            else:
                signal = 'NEUTRAL'
                status = f'INR stable ({change_pct:.2f}% change)'
            
            return {
                'status': status,
                'signal': signal,
                'value': current,
                'change_pct': change_pct
            }
        except Exception as e:
            return {'status': f'Error: {e}', 'signal': 'NEUTRAL', 'value': None}
    
    def analyze_gold_silver_ratio(self):
        """PART 2.2: Gold-Silver Ratio"""
        try:
            ratio_data = self.indicators.get('gold_silver_ratio')
            if ratio_data.empty:
                return {'status': 'No Data', 'signal': 'NEUTRAL', 'value': None}
            
            current_ratio = ratio_data['ratio'].iloc[-1]
            
            if current_ratio > THRESHOLDS['gold_silver_high']:
                signal = 'BEARISH'
                status = f'Ratio high ({current_ratio:.2f}) - Gold overvalued vs Silver'
            elif current_ratio < THRESHOLDS['gold_silver_low']:
                signal = 'BULLISH'
                status = f'Ratio low ({current_ratio:.2f}) - Silver overheated'
            else:
                signal = 'NEUTRAL'
                status = f'Ratio normal ({current_ratio:.2f})'
            
            return {
                'status': status,
                'signal': signal,
                'value': current_ratio
            }
        except Exception as e:
            return {'status': f'Error: {e}', 'signal': 'NEUTRAL', 'value': None}
    
    def analyze_real_yield_divergence(self):
        """PART 2.1: Gold vs Real Yield Divergence"""
        try:
            gold = self.indicators.get('gold')
            real_yield = self.indicators.get('real_yield')
            
            if gold.empty or real_yield.empty:
                return {'status': 'No Data', 'signal': 'NEUTRAL'}
            
            # Resample both to daily frequency and forward fill
            gold_daily = gold.resample('D').ffill()
            real_yield_daily = real_yield.resample('D').ffill()
            
            # Merge data
            merged = gold_daily.merge(real_yield_daily, left_index=True, right_index=True, how='inner')
            
            if len(merged) < 30:
                return {'status': 'Insufficient data for correlation', 'signal': 'NEUTRAL'}
            
            # Calculate 30-day correlation
            correlation = merged.iloc[-30:].corr().iloc[0, 1]
            
            # Normally gold and real yield are negatively correlated
            if correlation > -0.3:
                signal = 'BULLISH'
                status = f'Divergence detected (corr: {correlation:.2f}) - Hidden demand signal'
            else:
                signal = 'NEUTRAL'
                status = f'Normal correlation (corr: {correlation:.2f})'
            
            return {
                'status': status,
                'signal': signal,
                'correlation': correlation
            }
        except Exception as e:
            return {'status': f'Data frequency mismatch', 'signal': 'NEUTRAL'}
    
    def get_dip_detection_score(self):
        """PART 3: Practical dip-detection checklist"""
        checklist = {
            'Real Yield': self.analyze_real_yield(),
            'USD Strength': self.analyze_dxy(),
            'Risk Sentiment': self.analyze_risk_sentiment(),
            'INR Movement': self.analyze_inr(),
            'Gold-Silver Ratio': self.analyze_gold_silver_ratio(),
            'Yield Divergence': self.analyze_real_yield_divergence(),
        }
        
        # Calculate score
        bullish_count = sum(1 for item in checklist.values() if item['signal'] == 'BULLISH')
        bearish_count = sum(1 for item in checklist.values() if item['signal'] == 'BEARISH')
        
        if bullish_count >= 3:
            recommendation = 'GOOD ENTRY POINT'
            color = 'green'
        elif bearish_count >= 3:
            recommendation = 'AVOID / WAIT'
            color = 'red'
        else:
            recommendation = 'NEUTRAL / WATCH'
            color = 'orange'
        
        return {
            'checklist': checklist,
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'recommendation': recommendation,
            'color': color
        }
    
    def run_full_analysis(self):
        """Run complete analysis"""
        return {
            'real_yield': self.analyze_real_yield(),
            'dxy': self.analyze_dxy(),
            'risk_sentiment': self.analyze_risk_sentiment(),
            'inr': self.analyze_inr(),
            'gold_silver_ratio': self.analyze_gold_silver_ratio(),
            'divergence': self.analyze_real_yield_divergence(),
            'dip_score': self.get_dip_detection_score()
        }
