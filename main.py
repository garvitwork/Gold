"""
Gold & Silver Price Prediction App for Indian Market
Main Streamlit Application
Run with: streamlit run main.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data_fetcher import DataFetcher
from analyzer import MarketAnalyzer
from config import COLORS, THRESHOLDS
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Gold & Silver Price Prediction",
    page_icon="💰",
    layout="wide"
)

# Title
st.title("💰 Gold & Silver Price Prediction - Indian Market Context")
st.markdown("Real-time analysis of factors affecting gold prices in India")

# Helper function to check data availability
def check_data_available(data, data_name):
    """Check if data is available and return appropriate message"""
    if data is None or (isinstance(data, pd.DataFrame) and data.empty):
        st.warning(f"⚠️ {data_name} data temporarily unavailable. This may affect analysis accuracy.")
        return False
    return True

# Initialize data fetcher
@st.cache_data(ttl=3600)
def fetch_all_data():
    """Fetch all market data with caching"""
    fetcher = DataFetcher()
    return fetcher.get_market_indicators()

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    st.info("📊 Data updates every hour")
    
    show_part1 = st.checkbox("Part 1: Basic Factors", value=True)
    show_part2 = st.checkbox("Part 2: Advanced Signals", value=True)
    show_part3 = st.checkbox("Part 3: Dip Detection", value=True)
    
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# Load data
with st.spinner("Fetching real-time market data..."):
    indicators = fetch_all_data()
    
    # Check if critical data is missing
    critical_data_missing = []
    if indicators.get('gold', pd.DataFrame()).empty:
        critical_data_missing.append("Gold Prices")
    if indicators.get('usdinr', pd.DataFrame()).empty:
        critical_data_missing.append("USD/INR Exchange Rate")
    
    if critical_data_missing:
        st.error(f"""
        ⚠️ **Unable to fetch critical data:** {', '.join(critical_data_missing)}
        
        **Possible reasons:**
        - Yahoo Finance API rate limiting (try again in a few minutes)
        - Network connectivity issues
        - Invalid FRED API key (if using FRED data)
        
        **Solutions:**
        1. Wait 2-3 minutes and click "🔄 Refresh Data" in the sidebar
        2. Check your internet connection
        3. Verify FRED API key in config.py
        4. Try restarting the app
        """)
        st.stop()
    
    analyzer = MarketAnalyzer(indicators)
    analysis = analyzer.run_full_analysis()

# ============================================================================
# PART 1: BASIC FACTORS
# ============================================================================
if show_part1:
    st.header("📊 PART 1: Factors Causing Gold Price Dip in India")
    
    # Indian Gold Price Overview
    st.subheader("🇮🇳 Indian Gold Price Breakdown")
    indian_gold = indicators.get('indian_gold')
    
    if not indian_gold.empty and check_data_available(indian_gold, "Indian Gold Price"):
        col1, col2, col3 = st.columns(3)
        
        current_gold_inr = indian_gold['gold_inr'].iloc[-1]
        current_gold_usd = indian_gold['gold_usd_10g'].iloc[-1]
        current_usdinr = indian_gold['usdinr'].iloc[-1]
        
        with col1:
            st.metric("Gold Price (INR/10g)", f"₹{current_gold_inr:,.0f}")
            st.caption("Includes import duty & GST")
        with col2:
            st.metric("Global Gold (USD/10g)", f"${current_gold_usd:,.2f}")
            st.caption("International spot price")
        with col3:
            st.metric("USD/INR", f"₹{current_usdinr:.2f}")
        
        # Plot Indian gold price trend
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=indian_gold.index,
            y=indian_gold['gold_inr'],
            mode='lines',
            name='Gold Price (INR)',
            line=dict(color=COLORS['primary'], width=2)
        ))
        fig.update_layout(
            title="Indian Gold Price Trend - Per 10 Grams (Last 1 Year)",
            xaxis_title="Date",
            yaxis_title="Price (INR/10g)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Indian gold price data unavailable. Please refresh in a few minutes.")
    
    # Factor Analysis Grid
    col1, col2 = st.columns(2)
    
    with col1:
        # 1. Real Yield Analysis
        st.subheader("1️⃣ US Real Interest Rates")
        real_yield_analysis = analysis['real_yield']
        
        signal_color = COLORS['negative'] if real_yield_analysis['signal'] == 'BEARISH' else \
                      COLORS['positive'] if real_yield_analysis['signal'] == 'BULLISH' else COLORS['neutral']
        
        st.markdown(f"**Signal:** :{signal_color}[{real_yield_analysis['signal']}]")
        st.write(real_yield_analysis['status'])
        
        if real_yield_analysis['value'] is not None:
            st.metric(
                "Current Real Yield",
                f"{real_yield_analysis['value']:.2f}%",
                f"{real_yield_analysis['change']:.2f}%"
            )
        else:
            st.warning("⚠️ FRED API: Get a new API key from https://fred.stlouisfed.org/")
        
        # Plot real yield
        real_yield_data = indicators.get('real_yield')
        if not real_yield_data.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=real_yield_data.index,
                y=real_yield_data['real_yield'],
                mode='lines',
                name='Real Yield',
                line=dict(color=signal_color, width=2)
            ))
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            fig.update_layout(
                title="US Real Yield Trend",
                xaxis_title="Date",
                yaxis_title="Real Yield (%)",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 2. DXY Analysis
        st.subheader("2️⃣ US Dollar Strength (DXY)")
        dxy_analysis = analysis['dxy']
        
        signal_color = COLORS['negative'] if dxy_analysis['signal'] == 'BEARISH' else \
                      COLORS['positive'] if dxy_analysis['signal'] == 'BULLISH' else COLORS['neutral']
        
        st.markdown(f"**Signal:** :{signal_color}[{dxy_analysis['signal']}]")
        st.write(dxy_analysis['status'])
        
        if dxy_analysis['value'] is not None:
            st.metric(
                "Current DXY",
                f"{dxy_analysis['value']:.2f}",
                f"{dxy_analysis['change_pct']:.2f}%"
            )
        
        # Plot DXY
        dxy_data = indicators.get('dxy')
        if not dxy_data.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dxy_data.index,
                y=dxy_data['value'],
                mode='lines',
                name='DXY Index',
                line=dict(color=signal_color, width=2)
            ))
            fig.update_layout(
                title="Dollar Index (DXY) Trend",
                xaxis_title="Date",
                yaxis_title="DXY",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 3. Risk Sentiment
        st.subheader("3️⃣ Stock Market Risk Sentiment")
        risk_analysis = analysis['risk_sentiment']
        
        signal_color = COLORS['negative'] if risk_analysis['signal'] == 'BEARISH' else \
                      COLORS['positive'] if risk_analysis['signal'] == 'BULLISH' else COLORS['neutral']
        
        st.markdown(f"**Signal:** :{signal_color}[{risk_analysis['signal']}]")
        st.write(risk_analysis['status'])
        
        # VIX Chart
        vix_data = indicators.get('vix')
        if not vix_data.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=vix_data.index,
                y=vix_data.iloc[:, 0],
                mode='lines',
                name='VIX',
                line=dict(color=signal_color, width=2)
            ))
            fig.add_hline(y=THRESHOLDS['vix_low'], line_dash="dash", line_color="red", annotation_text="Risk-ON threshold")
            fig.add_hline(y=20, line_dash="dash", line_color="green", annotation_text="Fear threshold")
            fig.update_layout(
                title="VIX (Fear Index)",
                xaxis_title="Date",
                yaxis_title="VIX",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 5. INR Movement
        st.subheader("5️⃣ INR vs USD Movement")
        inr_analysis = analysis['inr']
        
        signal_color = COLORS['negative'] if inr_analysis['signal'] == 'BEARISH' else \
                      COLORS['positive'] if inr_analysis['signal'] == 'BULLISH' else COLORS['neutral']
        
        st.markdown(f"**Signal:** :{signal_color}[{inr_analysis['signal']}]")
        st.write(inr_analysis['status'])
        
        if inr_analysis['value'] is not None:
            st.metric(
                "Current USD/INR",
                f"₹{inr_analysis['value']:.2f}",
                f"{inr_analysis['change_pct']:.2f}%"
            )
        
        # USD/INR Chart
        usdinr_data = indicators.get('usdinr')
        if not usdinr_data.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=usdinr_data.index,
                y=usdinr_data.iloc[:, 0],
                mode='lines',
                name='USD/INR',
                line=dict(color=signal_color, width=2)
            ))
            fig.update_layout(
                title="USD/INR Exchange Rate",
                xaxis_title="Date",
                yaxis_title="INR per USD",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PART 2: ADVANCED SIGNALS
# ============================================================================
if show_part2:
    st.header("🔥 PART 2: Advanced Professional Signals")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gold vs Real Yield Divergence
        st.subheader("1️⃣ Gold vs Real Yield Divergence")
        divergence = analysis['divergence']
        
        signal_color = COLORS['positive'] if divergence['signal'] == 'BULLISH' else COLORS['neutral']
        st.markdown(f"**Signal:** :{signal_color}[{divergence['signal']}]")
        st.write(divergence['status'])
        
        # Overlay plot
        gold_data = indicators.get('gold')
        real_yield_data = indicators.get('real_yield')
        
        if not gold_data.empty and not real_yield_data.empty:
            try:
                # Resample to daily and align
                gold_daily = gold_data.resample('D').ffill()
                real_yield_daily = real_yield_data.resample('D').ffill()
                
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                
                fig.add_trace(
                    go.Scatter(x=gold_daily.index, y=gold_daily.iloc[:, 0], name="Gold Price", line=dict(color=COLORS['primary'])),
                    secondary_y=False
                )
                fig.add_trace(
                    go.Scatter(x=real_yield_daily.index, y=real_yield_daily['real_yield'], name="Real Yield", line=dict(color='red')),
                    secondary_y=True
                )
                
                fig.update_xaxes(title_text="Date")
                fig.update_yaxes(title_text="Gold Price (USD)", secondary_y=False)
                fig.update_yaxes(title_text="Real Yield (%)", secondary_y=True)
                fig.update_layout(title="Gold vs Real Yield Correlation", height=350)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Unable to plot divergence: {str(e)}")
    
    with col2:
        # Gold-Silver Ratio
        st.subheader("2️⃣ Gold-Silver Ratio")
        gs_ratio = analysis['gold_silver_ratio']
        
        signal_color = COLORS['negative'] if gs_ratio['signal'] == 'BEARISH' else \
                      COLORS['positive'] if gs_ratio['signal'] == 'BULLISH' else COLORS['neutral']
        
        st.markdown(f"**Signal:** :{signal_color}[{gs_ratio['signal']}]")
        st.write(gs_ratio['status'])
        
        if gs_ratio['value'] is not None:
            st.metric("Current Ratio", f"{gs_ratio['value']:.2f}")
        
        # Ratio Chart
        ratio_data = indicators.get('gold_silver_ratio')
        if not ratio_data.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=ratio_data.index,
                y=ratio_data['ratio'],
                mode='lines',
                name='Gold/Silver Ratio',
                line=dict(color=signal_color, width=2)
            ))
            fig.add_hline(y=THRESHOLDS['gold_silver_high'], line_dash="dash", line_color="red", annotation_text="Overvalued")
            fig.add_hline(y=THRESHOLDS['gold_silver_low'], line_dash="dash", line_color="green", annotation_text="Undervalued")
            fig.update_layout(
                title="Gold/Silver Ratio Trend",
                xaxis_title="Date",
                yaxis_title="Ratio",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PART 3: DIP DETECTION CHECKLIST
# ============================================================================
if show_part3:
    st.header("✅ PART 3: Dip Detection Score & Recommendation")
    
    dip_score = analysis['dip_score']
    
    # Display recommendation with color
    rec_color = dip_score['color']
    st.markdown(f"### Recommendation: :{rec_color}[**{dip_score['recommendation']}**]")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Bullish Signals", dip_score['bullish_count'])
    with col2:
        st.metric("Bearish Signals", dip_score['bearish_count'])
    with col3:
        st.metric("Neutral Signals", 6 - dip_score['bullish_count'] - dip_score['bearish_count'])
    
    # Detailed checklist
    st.subheader("📋 Detailed Checklist")
    
    checklist_df = []
    for factor, data in dip_score['checklist'].items():
        checklist_df.append({
            'Factor': factor,
            'Signal': data['signal'],
            'Status': data['status']
        })
    
    df = pd.DataFrame(checklist_df)
    
    # Color code the signals
    def color_signal(val):
        if val == 'BULLISH':
            return f'background-color: {COLORS["positive"]}; color: white'
        elif val == 'BEARISH':
            return f'background-color: {COLORS["negative"]}; color: white'
        else:
            return f'background-color: {COLORS["neutral"]}; color: white'
    
    styled_df = df.style.map(color_signal, subset=['Signal'])
    st.dataframe(styled_df, use_container_width=True, height=300)
    
    # Entry guidance
    st.info("""
    **Entry Guidance:**
    - ✅ **Good Entry**: 3+ bullish signals (Real yield falling, USD weak, VIX high, INR stable)
    - ⚠️ **Neutral**: Mixed signals, wait for clearer direction
    - ❌ **Avoid**: 3+ bearish signals (Real yield rising, USD strong, Risk-ON market)
    """)

# Footer
st.markdown("---")
st.caption("Data sources: Yahoo Finance, FRED API | Updates hourly | For educational purposes only")
