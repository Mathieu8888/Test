import streamlit as st
import sys, os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

sys.path.insert(0, os.path.dirname(__file__))
from Algorithmev1 import StockScorer
from smart_search import smart_search, extract_ticker

# Importer streamlit-searchbox pour l'autocompletion
try:
    from streamlit_searchbox import st_searchbox
    SEARCHBOX_AVAILABLE = True
except ImportError:
    SEARCHBOX_AVAILABLE = False

st.set_page_config(page_title="Analyseur Actions Boursières", page_icon="📈", layout="wide")

st.title("📈 Analyseur d'Actions Boursières")

# ============================
# ONGLETS PRINCIPAUX
# ============================
tab_analyse, tab_top100, tab_perf_pos, tab_perf_neg = st.tabs([
    "🔍 Analyse Individuelle",
    "🏆 Top 100 Capitalisation", 
    "📈 Meilleures Perfs 1Y",
    "📉 Pires Perfs 1Y"
])

# ============================
# FONCTIONS POUR LES CLASSEMENTS
# ============================

MAJOR_STOCKS = {
    "🇺🇸 Tech": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "NFLX", "AMD", "INTC",
                  "ADBE", "CRM", "ORCL", "CSCO", "AVGO", "QCOM", "TXN", "INTU", "NOW", "SNOW",
                  "PLTR", "UBER", "ABNB", "CRWD", "PANW", "ZS", "NET", "DDOG", "MDB", "SHOP"],
    
    "🇺🇸 Finance": ["JPM", "BAC", "WFC", "GS", "MS", "V", "MA", "AXP", "C", "BLK",
                     "SCHW", "USB", "PNC", "TFC", "COF", "BK", "STT", "TROW", "AIG", "MET"],
    
    "🇺🇸 Healthcare": ["UNH", "JNJ", "LLY", "ABBV", "MRK", "TMO", "ABT", "DHR", "PFE", "BMY",
                        "AMGN", "GILD", "CVS", "CI", "HUM", "ISRG", "REGN", "VRTX", "ZTS", "BIIB"],
    
    "🇺🇸 Consommation": ["WMT", "HD", "MCD", "NKE", "SBUX", "DIS", "COST", "TGT", "LOW", "TJX",
                          "PG", "KO", "PEP", "PM", "CL", "KMB", "EL", "MDLZ", "GIS", "KHC"],
    
    "🇺🇸 Energie & Industrie": ["XOM", "CVX", "COP", "SLB", "MPC", "PSX", "VLO", "OXY", "HAL", "EOG",
                                 "BA", "CAT", "GE", "HON", "UPS", "RTX", "LMT", "DE", "MMM", "EMR"],
    
    "🇺🇸 Telecom": ["T", "VZ", "TMUS", "CMCSA", "CHTR"],
    
    "🇪🇺 Europe ADR": ["ASML", "SAP", "NVO", "AZN", "HSBC", "BP", "SHEL", "BHP", "RIO", "BTI"],
    
    "🌏 International ADR": ["TSM", "BABA", "PDD", "JD", "NIO", "BIDU"]
}

ALL_STOCKS = []
for stocks in MAJOR_STOCKS.values():
    ALL_STOCKS.extend(stocks)
ALL_STOCKS = list(set(ALL_STOCKS))

@st.cache_data(ttl=300)
def get_stock_data(ticker):
    """Récupère les données d'une action"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")
        
        if hist.empty or not info:
            return None
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or (hist['Close'][-1] if not hist.empty else None)
        market_cap = info.get('marketCap', 0)
        
        # Validation des données
        if market_cap and (market_cap < 1_000_000 or market_cap > 10_000_000_000_000):
            return None
        
        if not current_price or current_price <= 0 or current_price > 100000:
            return None
        
        if len(hist) >= 1:
            perf_1d = ((hist['Close'][-1] - hist['Close'][-2]) / hist['Close'][-2] * 100) if len(hist) >= 2 else 0
        else:
            perf_1d = 0
            
        if len(hist) >= 7:
            perf_7d = ((hist['Close'][-1] - hist['Close'][-7]) / hist['Close'][-7] * 100)
        else:
            perf_7d = 0
            
        if len(hist) >= 30:
            perf_30d = ((hist['Close'][-1] - hist['Close'][-30]) / hist['Close'][-30] * 100)
        else:
            perf_30d = 0
            
        perf_1y = ((hist['Close'][-1] - hist['Close'][0]) / hist['Close'][0] * 100) if len(hist) > 0 else 0
        
        volume = hist['Volume'][-1] if not hist.empty else 0
        
        return {
            'ticker': ticker,
            'name': info.get('longName', ticker),
            'price': current_price,
            'market_cap': market_cap,
            'volume': volume,
            'perf_1d': perf_1d,
            'perf_7d': perf_7d,
            'perf_30d': perf_30d,
            'perf_1y': perf_1y,
            'sector': info.get('sector', 'N/A')
        }
    except Exception as e:
        return None

def format_large_number(num):
    """Formate les grands nombres"""
    if num >= 1e12:
        return f"${num/1e12:.2f}T"
    elif num >= 1e9:
        return f"${num/1e9:.2f}B"
    elif num >= 1e6:
        return f"${num/1e6:.2f}M"
    else:
        return f"${num:,.0f}"

def format_percentage(value, decimals=2):
    """Formate un pourcentage avec couleur"""
    if value > 0:
        return f'<span style="color: #00CC00;">▲ {value:.{decimals}f}%</span>'
    elif value < 0:
        return f'<span style="color: #FF4B4B;">▼ {abs(value):.{decimals}f}%</span>'
    else:
        return f'<span style="color: #888888;">• {value:.{decimals}f}%</span>'

# ============================
# ONGLET 1 : ANALYSE INDIVIDUELLE (CODE ORIGINAL COMPLET)
# ============================
with tab_analyse:
    st.header("🔍 Démarrez l'Analyse")
    
    col_left_pad, col_center_content, col_right_pad = st.columns([1, 4, 1])
    
    with col_center_content:
        
        if SEARCHBOX_AVAILABLE:
            def search_function(query: str):
                if not query or len(query) < 1:
                    return [
                        "AAPL - Apple Inc.",
                        "GOOGL - Alphabet Inc. (Google)",
                        "MSFT - Microsoft Corporation",
                        "NVDA - NVIDIA Corporation",
                        "TSLA - Tesla Inc."
                    ]
                results = smart_search(query, limit=8)
                return results if results else []
            
            selected_company = st_searchbox(
                search_function,
                placeholder="🔍 Tapez : Ferrari, Nintendo, Apple, Samsung...",
                label="Rechercher une entreprise",
                key="company_searchbox",
                clear_on_submit=False,
                rerun_on_update=False
            )
            
            if selected_company:
                company = extract_ticker(selected_company)
            else:
                company = ""
        
        else:
            st.markdown("**Rechercher une entreprise**")
            
            search_input = st.text_input(
                "Entreprise ou Ticker",
                placeholder="Tapez : Ferrari, Nintendo, Apple, Samsung, RACE, NTDOY...",
                key="fallback_search",
                label_visibility="collapsed"
            )
            
            if search_input and len(search_input) >= 1:
                suggestions = smart_search(search_input, limit=6)
                
                if suggestions and not suggestions[0].startswith("❌"):
                    st.markdown("**💡 Suggestions :**")
                    cols = st.columns(2)
                    
                    for idx, suggestion in enumerate(suggestions[:6]):
                        col = cols[idx % 2]
                        with col:
                            if st.button(suggestion, key=f"sug_{idx}", use_container_width=True):
                                company = extract_ticker(suggestion)
                                st.rerun()
            
            company = search_input.upper() if search_input else ""

        col_radio, col_button = st.columns([2, 1])

        with col_radio:
            horizon = st.radio("Horizon d'investissement", ["Court terme", "Long terme"], index=1, horizontal=True)
            h_code = 'court' if 'Court' in horizon else 'long'

        with col_button:
            st.markdown("<br>", unsafe_allow_html=True)
            analyze = st.button("🚀 ANALYSER", type="primary", use_container_width=True)

    st.markdown("---")

    # Fonctions helper (code original complet)
    def get_valuation_analysis(info):
        pe = info.get('trailingPE') or info.get('forwardPE')
        peg = info.get('pegRatio')
        pb = info.get('priceToBook')
        
        signals = []
        
        if pe is not None and pe > 0:
            if pe < 15:
                signals.append(("P/E Ratio", pe, "🟢 Sous-évalué", f"P/E de {pe:.2f} (< 15)"))
            elif pe < 25:
                signals.append(("P/E Ratio", pe, "🟡 Équilibré", f"P/E de {pe:.2f} (15-25)"))
            else:
                signals.append(("P/E Ratio", pe, "🔴 Surévalué", f"P/E de {pe:.2f} (> 25)"))
        
        if peg is not None and peg > 0:
            if peg < 1:
                signals.append(("PEG Ratio", peg, "🟢 Sous-évalué", f"PEG de {peg:.2f} (< 1)"))
            elif peg < 2:
                signals.append(("PEG Ratio", peg, "🟡 Équilibré", f"PEG de {peg:.2f} (1-2)"))
            else:
                signals.append(("PEG Ratio", peg, "🔴 Surévalué", f"PEG de {peg:.2f} (> 2)"))
        
        if pb is not None and pb > 0:
            if pb < 1:
                signals.append(("P/B Ratio", pb, "🟢 Sous-évalué", f"P/B de {pb:.2f} (< 1)"))
            elif pb < 3:
                signals.append(("P/B Ratio", pb, "🟡 Équilibré", f"P/B de {pb:.2f} (1-3)"))
            else:
                signals.append(("P/B Ratio", pb, "🔴 Surévalué", f"P/B de {pb:.2f} (> 3)"))
        
        if not signals:
            return None, "⚠️ Données insuffisantes"
        
        green_count = sum(1 for s in signals if "🟢" in s[2])
        red_count = sum(1 for s in signals if "🔴" in s[2])
        
        if green_count > red_count:
            verdict = "🟢 **SOUS-ÉVALUÉE** - L'action semble attractive"
        elif red_count > green_count:
            verdict = "🔴 **SURÉVALUÉE** - L'action semble chère"
        else:
            verdict = "🟡 **VALORISATION ÉQUILIBRÉE**"
        
        return signals, verdict

    def get_calculation_details(scorer, indicator_name):
        info = scorer.info
        
        def format_percentage(value):
            if value is None or value == 'N/A':
                return 'N/A'
            try:
                return f"{float(value) * 100:.2f}%" if abs(float(value)) < 1 else f"{float(value):.2f}%"
            except:
                return str(value)
        
        def format_number(value):
            if value is None or value == 'N/A':
                return 'N/A'
            try:
                return f"{float(value):,.2f}"
            except:
                return str(value)
        
        details = {
            "Momentum 6M": f"""
**Calcul du Momentum sur 6 mois**
- Performance calculée sur les 6 derniers mois
- **Prix actuel** : ${info.get('currentPrice', 'N/A')}
- **Plus haut 52 sem** : ${info.get('fiftyTwoWeekHigh', 'N/A')}
- **Plus bas 52 sem** : ${info.get('fiftyTwoWeekLow', 'N/A')}
""",
            "Momentum 3M": f"""
**Calcul du Momentum sur 3 mois**
- Performance calculée sur les 3 derniers mois
- **Prix actuel** : ${info.get('currentPrice', 'N/A')}
""",
            "RSI": f"""
**RSI (Relative Strength Index)**
- Indicateur de momentum (0-100)
- RSI > 70 → Surachat
- RSI < 30 → Survente
""",
            "Volume": f"""
**Volume moyen**
- Volume 10j : {format_number(info.get('averageVolume10days', 'N/A'))}
- Volume 3m : {format_number(info.get('averageVolume', 'N/A'))}
""",
            "P/E Ratio": f"""
**Price-to-Earnings Ratio**
- P/E actuel : {format_number(info.get('trailingPE', 'N/A'))}
- Mesure la valorisation
""",
            "P/B Ratio": f"""
**Price-to-Book Ratio**
- P/B actuel : {format_number(info.get('priceToBook', 'N/A'))}
""",
            "ROE": f"""
**Return on Equity**
- ROE actuel : {format_percentage(info.get('returnOnEquity', 'N/A'))}
- Mesure la rentabilité
""",
            "Marge Opérationnelle": f"""
**Marge Opérationnelle**
- Marge : {format_percentage(info.get('operatingMargins', 'N/A'))}
""",
            "Croissance CA": f"""
**Croissance du Chiffre d'Affaires**
- Croissance : {format_percentage(info.get('revenueGrowth', 'N/A'))}
""",
            "Dette/Equity": f"""
**Ratio Dette/Capitaux Propres**
- Ratio : {format_number(info.get('debtToEquity', 'N/A'))}
""",
        }
        
        return details.get(indicator_name, "Détails non disponibles")

    if analyze and company:
        with st.spinner(f"🔄 Analyse de {company} en cours..."):
            try:
                final = StockScorer(company, horizon=h_code)
                global_score = final.calculate_score()
                
                if global_score is None or global_score == 0:
                    st.error(f"❌ Impossible de récupérer les données pour {company}")
                else:
                    info = final.info
                    
                    st.success(f"✅ Analyse terminée pour **{info.get('longName', company)}** ({company})")
                    
                    col_logo, col_title = st.columns([1, 5])
                    
                    with col_logo:
                        logo_url = info.get('logo_url')
                        if logo_url:
                            st.image(logo_url, width=80)
                    
                    with col_title:
                        st.markdown(f"## {info.get('longName', company)}")
                        st.markdown(f"**Secteur** : {info.get('sector', 'N/A')} | **Industrie** : {info.get('industry', 'N/A')}")
                        website = info.get('website', '#')
                        if website and website != '#':
                            st.markdown(f"**Site web** : [{website}]({website})")
                    
                    st.markdown("---")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    score = global_score
                    
                    if score >= 80:
                        verdict_icon = "🟢"
                        verdict_text = "ACHAT FORT"
                        verdict_color = "#00CC00"
                    elif score >= 65:
                        verdict_icon = "🟢"
                        verdict_text = "ACHAT"
                        verdict_color = "#66FF66"
                    elif score >= 50:
                        verdict_icon = "🟡"
                        verdict_text = "NEUTRE"
                        verdict_color = "#FFD700"
                    elif score >= 35:
                        verdict_icon = "🟠"
                        verdict_text = "PRUDENCE"
                        verdict_color = "#FFA500"
                    else:
                        verdict_icon = "🔴"
                        verdict_text = "ÉVITER"
                        verdict_color = "#FF4B4B"
                    
                    with col1:
                        st.markdown(f"""
                            <div style='text-align: center; padding: 20px; background-color: {verdict_color}20; border-radius: 10px; border: 2px solid {verdict_color};'>
                                <h1 style='margin: 0; color: {verdict_color};'>{verdict_icon}</h1>
                                <h2 style='margin: 10px 0; color: {verdict_color};'>{score:.1f}/100</h2>
                                <p style='margin: 0; font-size: 18px; font-weight: bold; color: {verdict_color};'>{verdict_text}</p>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        current_price = info.get('currentPrice', 0)
                        target_price = info.get('targetMeanPrice', 0)
                        
                        if current_price and target_price:
                            upside = ((target_price - current_price) / current_price) * 100
                            upside_color = "#00CC00" if upside > 0 else "#FF4B4B"
                            
                            st.markdown(f"""
                                <div style='text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px;'>
                                    <p style='margin: 0; font-size: 14px; color: #666;'>Prix Actuel</p>
                                    <h2 style='margin: 10px 0;'>${current_price:.2f}</h2>
                                    <p style='margin: 0; font-size: 14px; color: #666;'>Prix Cible</p>
                                    <h3 style='margin: 5px 0;'>${target_price:.2f}</h3>
                                    <p style='margin: 5px 0; font-size: 16px; font-weight: bold; color: {upside_color};'>
                                        {upside:+.1f}% potentiel
                                    </p>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.info("Prix cible non disponible")
                    
                    with col3:
                        recommendation = info.get('recommendationKey', 'N/A').upper()
                        num_analysts = info.get('numberOfAnalystOpinions', 0)
                        
                        rec_colors = {
                            'STRONG_BUY': '#00CC00',
                            'BUY': '#66FF66',
                            'HOLD': '#FFD700',
                            'SELL': '#FFA500',
                            'STRONG_SELL': '#FF4B4B'
                        }
                        
                        rec_color = rec_colors.get(recommendation, '#666666')
                        
                        st.markdown(f"""
                            <div style='text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px;'>
                                <p style='margin: 0; font-size: 14px; color: #666;'>Recommandation Analystes</p>
                                <h2 style='margin: 10px 0; color: {rec_color};'>{recommendation.replace('_', ' ')}</h2>
                                <p style='margin: 0; font-size: 14px; color: #666;'>{num_analysts} analystes</p>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    st.subheader("📊 Détails des Indicateurs")
                    
                    cols_indicators = st.columns(4)
                    
                    for idx, (indicator, score_val) in enumerate(final.scores.items()):
                        col = cols_indicators[idx % 4]
                        
                        with col:
                            if score_val >= 8:
                                color = "#00CC00"
                                icon = "🟢"
                            elif score_val >= 6:
                                color = "#66FF66"
                                icon = "🟢"
                            elif score_val >= 4:
                                color = "#FFD700"
                                icon = "🟡"
                            elif score_val >= 2:
                                color = "#FFA500"
                                icon = "🟠"
                            else:
                                color = "#FF4B4B"
                                icon = "🔴"
                            
                            st.markdown(f"""
                                <div style='text-align: center; padding: 15px; background-color: {color}15; border-radius: 8px; border-left: 4px solid {color}; margin-bottom: 10px;'>
                                    <p style='margin: 0; font-size: 12px; color: #666;'>{indicator}</p>
                                    <h3 style='margin: 5px 0; color: {color};'>{icon} {score_val:.1f}/10</h3>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            with st.expander("ℹ️ Détails", expanded=False):
                                st.markdown(get_calculation_details(final, indicator))
                    
                    st.markdown("---")
                    
                    valuation_signals, valuation_verdict = get_valuation_analysis(info)
                    
                    if valuation_signals:
                        st.subheader("💰 Analyse de Valorisation")
                        st.markdown(valuation_verdict)
                        
                        cols_val = st.columns(len(valuation_signals))
                        
                        for idx, (metric_name, value, status, description) in enumerate(valuation_signals):
                            with cols_val[idx]:
                                st.markdown(f"""
                                    <div style='text-align: center; padding: 15px; background-color: #f0f2f6; border-radius: 8px;'>
                                        <p style='margin: 0; font-size: 14px; color: #666;'>{metric_name}</p>
                                        <h3 style='margin: 10px 0;'>{value:.2f}</h3>
                                        <p style='margin: 0; font-size: 14px;'>{status}</p>
                                    </div>
                                """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    st.subheader("📈 Évolution du Prix")
                    
                    period_options = [
                        ("1S", "1wk"), ("1M", "1mo"), ("3M", "3mo"), ("6M", "6mo"),
                        ("1A", "1y"), ("YTD", "ytd"), ("5A", "5y"), ("MAX", "max")
                    ]
                    
                    if 'selected_period_key' not in st.session_state:
                        st.session_state.selected_period_key = "1A"
                    
                    col_spacer, col_buttons = st.columns([2, 2])
                    
                    with col_buttons:
                        cols = st.columns(8)
                        for idx, (label, period_code) in enumerate(period_options):
                            with cols[idx]:
                                if st.button(
                                    label,
                                    key=f"period_{label}",
                                    use_container_width=True,
                                    type="primary" if st.session_state.selected_period_key == label else "secondary"
                                ):
                                    st.session_state.selected_period_key = label
                                    st.rerun()
                    
                    period_options_dict = dict(period_options)
                    selected_period = period_options_dict[st.session_state.selected_period_key]
                    
                    try:
                        import plotly.graph_objects as go
                        
                        hist = final.stock.history(period=selected_period)
                        
                        if not hist.empty:
                            perf_period = ((hist['Close'][-1] - hist['Close'][0]) / hist['Close'][0]) * 100
                            
                            plot_color = '#00CC00' if perf_period > 0 else '#FF4B4B'
                            fill_color = 'rgba(0, 204, 0, 0.1)' if perf_period > 0 else 'rgba(255, 75, 75, 0.1)'
                            
                            price_min = hist['Close'].min()
                            price_max = hist['Close'].max()
                            price_range = price_max - price_min
                            
                            y_min = price_min - (price_range * 0.05)
                            y_max = price_max + (price_range * 0.05)
                            
                            fig = go.Figure()
                            
                            fig.add_trace(go.Scatter(
                                x=hist.index, y=[y_min] * len(hist),
                                mode='lines', line=dict(width=0),
                                showlegend=False, hoverinfo='skip'
                            ))
                            
                            fig.add_trace(go.Scatter(
                                x=hist.index, y=hist['Close'],
                                mode='lines', name='Prix',
                                line=dict(color=plot_color, width=2.5),
                                fill='tonexty', fillcolor=fill_color
                            ))
                            
                            fig.update_layout(
                                xaxis_title="Date", yaxis_title="Prix ($)",
                                hovermode='x unified', height=400,
                                showlegend=False, margin=dict(l=0, r=0, t=30, b=0),
                                yaxis=dict(hoverformat='$.2f', range=[y_min, y_max])
                            )
                            
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        else:
                            st.info("Historique non disponible")
                    except Exception as e:
                        st.warning("Impossible de charger l'historique")
                    
                    st.markdown("---")
                    st.warning("⚠️ **Avertissement :** Outil éducatif - Pas un conseil financier")
                    
            except Exception as e:
                st.error(f"Erreur : {e}")

# ============================
# ONGLET 2 : TOP 100 CAPITALISATION (LIGNES COMPACTES)
# ============================
with tab_top100:
    st.header("🏆 Top 100 Capitalisation Boursière")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("📊 Actions US & ADR - Données en temps réel")
    with col2:
        if st.button("🔄 Actualiser", key="refresh_mcap", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    with st.spinner("📊 Chargement..."):
        stock_data = []
        progress_bar = st.progress(0)
        
        for idx, ticker in enumerate(ALL_STOCKS[:120]):
            data = get_stock_data(ticker)
            if data and data['market_cap'] > 0:
                stock_data.append(data)
            progress_bar.progress((idx + 1) / 120)
            time.sleep(0.03)
        
        progress_bar.empty()
        
        df = pd.DataFrame(stock_data)
        df = df.sort_values('market_cap', ascending=False).reset_index(drop=True)
        df.index = df.index + 1
        
        # Table compacte
        for idx, row in df.head(100).iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([0.3, 1.5, 0.8, 1, 0.8, 0.8])
            
            with col1:
                st.markdown(f"**{idx}**")
            with col2:
                st.markdown(f"**{row['ticker']}**")
                st.caption(row['name'][:25] + "..." if len(row['name']) > 25 else row['name'])
            with col3:
                st.markdown(f"${row['price']:.2f}")
            with col4:
                st.markdown(format_large_number(row['market_cap']))
            with col5:
                st.markdown(format_percentage(row['perf_1d']), unsafe_allow_html=True)
            with col6:
                st.markdown(format_percentage(row['perf_1y']), unsafe_allow_html=True)
            
            st.divider()

# ============================
# ONGLET 3 : MEILLEURES PERFORMANCES (LIGNES COMPACTES)
# ============================
with tab_perf_pos:
    st.header("📈 Top 50 Meilleures Performances 1 an")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("🚀 Les actions qui ont le plus progressé")
    with col2:
        if st.button("🔄 Actualiser", key="refresh_perf_pos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    with st.spinner("📊 Chargement..."):
        if 'stock_data' not in locals() or not stock_data:
            stock_data = []
            progress_bar = st.progress(0)
            for idx, ticker in enumerate(ALL_STOCKS):
                data = get_stock_data(ticker)
                if data:
                    stock_data.append(data)
                progress_bar.progress((idx + 1) / len(ALL_STOCKS))
                time.sleep(0.03)
            progress_bar.empty()
        
        df = pd.DataFrame(stock_data)
        df_sorted = df.sort_values('perf_1y', ascending=False).reset_index(drop=True)
        df_sorted.index = df_sorted.index + 1
        
        # Table compacte
        for idx, row in df_sorted.head(50).iterrows():
            col1, col2, col3, col4, col5 = st.columns([0.3, 1.5, 0.8, 1, 1.2])
            
            with col1:
                if idx == 1:
                    st.markdown("🥇")
                elif idx == 2:
                    st.markdown("🥈")
                elif idx == 3:
                    st.markdown("🥉")
                else:
                    st.markdown(f"**{idx}**")
            with col2:
                st.markdown(f"**{row['ticker']}**")
                st.caption(row['name'][:25] + "..." if len(row['name']) > 25 else row['name'])
            with col3:
                st.markdown(f"${row['price']:.2f}")
            with col4:
                st.markdown(format_large_number(row['market_cap']))
            with col5:
                st.markdown(f'<span style="color: #00CC00; font-size: 16px; font-weight: bold;">▲ {row["perf_1y"]:.1f}%</span>', unsafe_allow_html=True)
            
            st.divider()

# ============================
# ONGLET 4 : PIRES PERFORMANCES (LIGNES COMPACTES)
# ============================
with tab_perf_neg:
    st.header("📉 Top 50 Pires Performances 1 an")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("⚠️ Les actions qui ont le plus baissé")
    with col2:
        if st.button("🔄 Actualiser", key="refresh_perf_neg", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    with st.spinner("📊 Chargement..."):
        if 'stock_data' not in locals() or not stock_data:
            stock_data = []
            progress_bar = st.progress(0)
            for idx, ticker in enumerate(ALL_STOCKS):
                data = get_stock_data(ticker)
                if data:
                    stock_data.append(data)
                progress_bar.progress((idx + 1) / len(ALL_STOCKS))
                time.sleep(0.03)
            progress_bar.empty()
        
        df = pd.DataFrame(stock_data)
        df_sorted = df.sort_values('perf_1y', ascending=True).reset_index(drop=True)
        df_sorted.index = df_sorted.index + 1
        
        # Table compacte
        for idx, row in df_sorted.head(50).iterrows():
            col1, col2, col3, col4, col5 = st.columns([0.3, 1.5, 0.8, 1, 1.2])
            
            with col1:
                st.markdown(f"**{idx}**")
            with col2:
                st.markdown(f"**{row['ticker']}**")
                st.caption(row['name'][:25] + "..." if len(row['name']) > 25 else row['name'])
            with col3:
                st.markdown(f"${row['price']:.2f}")
            with col4:
                st.markdown(format_large_number(row['market_cap']))
            with col5:
                st.markdown(f'<span style="color: #FF4B4B; font-size: 16px; font-weight: bold;">▼ {abs(row["perf_1y"]):.1f}%</span>', unsafe_allow_html=True)
            
            st.divider()

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; font-size: small;'>
        <span style='margin: 0 50px;'>📈 Analyseur d'Actions v2.0</span>
        <span style='margin: 0 50px;'>⚠️ Pas un conseil financier</span>
        <span style='margin: 0 50px;'>Créé par @Mathieugird</span>
    </div>
    """, unsafe_allow_html=True)

# CSS
st.markdown("""
<style>
    .main { padding-top: 2rem; }
    
    div[data-testid="column"] button[kind="secondary"] {
        background-color: #f0f2f6 !important;
        color: #31333F !important;
        border: 1px solid #e0e0e0 !important;
        font-size: 0.45em !important;
        padding: 1px 2px !important;
        min-height: 16px !important;
    }
    
    div[data-testid="column"] button[kind="primary"] {
        background-color: #1f77b4 !important;
        color: white !important;
        font-size: 0.45em !important;
        padding: 1px 2px !important;
        min-height: 16px !important;
    }
    
    /* Lignes compactes */
    .stDivider { margin: 0.2rem 0 !important; }
</style>
""", unsafe_allow_html=True)
