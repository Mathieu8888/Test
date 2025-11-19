import streamlit as st
import sys, os
import yfinance as yf
import pandas as pd
import time
import plotly.graph_objects as go
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from Algorithmev1 import StockScorer
from smart_search import smart_search, extract_ticker

# ---------------------------------------------------------
# CONFIGURATION ET IMPORTS
# ---------------------------------------------------------
try:
    from streamlit_searchbox import st_searchbox
    SEARCHBOX_AVAILABLE = True
except ImportError:
    SEARCHBOX_AVAILABLE = False
    st.warning("⚠️ Pour une meilleure expérience : `pip install streamlit-searchbox`")

st.set_page_config(page_title="Analyseur Actions Boursières", page_icon="📈", layout="wide")
st.title("📈 Analyseur d'Actions Boursières")

# ---------------------------------------------------------
# DONNÉES ET FONCTIONS POUR LES CLASSEMENTS
# ---------------------------------------------------------
MAJOR_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "NFLX", "AMD", "INTC",
    "ADBE", "CRM", "ORCL", "CSCO", "AVGO", "QCOM", "TXN", "INTU", "NOW", "SNOW",
    "PLTR", "UBER", "ABNB", "CRWD", "PANW", "JPM", "BAC", "WFC", "GS", "MS",
    "V", "MA", "AXP", "C", "BLK", "UNH", "JNJ", "LLY", "ABBV", "MRK",
    "TMO", "ABT", "DHR", "PFE", "BMY", "WMT", "HD", "MCD", "NKE", "SBUX",
    "DIS", "COST", "TGT", "LOW", "PG", "KO", "PEP", "XOM", "CVX", "COP",
    "BA", "CAT", "GE", "HON", "UPS", "T", "VZ", "TMUS", "TSM", "ASML"
]

@st.cache_data(ttl=300)
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")
        
        if hist.empty or not info:
            return None
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or (hist['Close'][-1] if not hist.empty else None)
        market_cap = info.get('marketCap', 0)
        
        if market_cap and (market_cap < 1_000_000 or market_cap > 10_000_000_000_000):
            return None
        if not current_price or current_price <= 0 or current_price > 100000:
            return None
        
        perf_1d = ((hist['Close'][-1] - hist['Close'][-2]) / hist['Close'][-2] * 100) if len(hist) >= 2 else 0
        perf_1y = ((hist['Close'][-1] - hist['Close'][0]) / hist['Close'][0] * 100) if len(hist) > 0 else 0
        
        return {
            'ticker': ticker,
            'name': info.get('longName', ticker),
            'price': current_price,
            'market_cap': market_cap,
            'perf_1d': perf_1d,
            'perf_1y': perf_1y
        }
    except:
        return None

def format_large_number(num):
    if num >= 1e12: return f"${num/1e12:.2f}T"
    elif num >= 1e9: return f"${num/1e9:.2f}B"
    elif num >= 1e6: return f"${num/1e6:.2f}M"
    else: return f"${num:,.0f}"

def format_percentage(value):
    if value > 0: return f'<span style="color: #00CC00;">▲ {value:.2f}%</span>'
    elif value < 0: return f'<span style="color: #FF4B4B;">▼ {abs(value):.2f}%</span>'
    else: return f'<span style="color: #888888;">• {value:.2f}%</span>'

# ---------------------------------------------------------
# FONCTIONS D'ANALYSE (TAB 1)
# ---------------------------------------------------------
def get_valuation_analysis(info):
    pe = info.get('trailingPE') or info.get('forwardPE')
    peg = info.get('pegRatio')
    pb = info.get('priceToBook')
    signals = []
    
    if pe is not None and pe > 0:
        if pe < 15: signals.append(("P/E Ratio", pe, "🟢 Sous-évalué", f"P/E de {pe:.2f} (< 15)"))
        elif pe < 25: signals.append(("P/E Ratio", pe, "🟡 Équilibré", f"P/E de {pe:.2f} (15-25)"))
        else: signals.append(("P/E Ratio", pe, "🔴 Surévalué", f"P/E de {pe:.2f} (> 25)"))
    
    if peg is not None and peg > 0:
        if peg < 1: signals.append(("PEG Ratio", peg, "🟢 Sous-évalué", f"PEG de {peg:.2f} (< 1)"))
        elif peg < 2: signals.append(("PEG Ratio", peg, "🟡 Équilibré", f"PEG de {peg:.2f} (1-2)"))
        else: signals.append(("PEG Ratio", peg, "🔴 Surévalué", f"PEG de {peg:.2f} (> 2)"))
    
    if pb is not None and pb > 0:
        if pb < 1: signals.append(("P/B Ratio", pb, "🟢 Sous-évalué", f"P/B de {pb:.2f} (< 1)"))
        elif pb < 3: signals.append(("P/B Ratio", pb, "🟡 Équilibré", f"P/B de {pb:.2f} (1-3)"))
        else: signals.append(("P/B Ratio", pb, "🔴 Surévalué", f"P/B de {pb:.2f} (> 3)"))
    
    if not signals: return None, "⚠️ Données insuffisantes pour l'analyse de valorisation"
    
    green_count = sum(1 for s in signals if "🟢" in s[2])
    red_count = sum(1 for s in signals if "🔴" in s[2])
    
    if green_count > red_count: verdict = "🟢 **SOUS-ÉVALUÉE**"
    elif red_count > green_count: verdict = "🔴 **SURÉVALUÉE**"
    else: verdict = "🟡 **VALORISATION ÉQUILIBRÉE**"
    
    return signals, verdict

def get_calculation_details(scorer, indicator_name):
    info = scorer.info
    def format_number(v):
        try: return f"{float(v):,.2f}"
        except: return str(v)
    
    details = {
        "Momentum 6M": f"**Calcul du Momentum sur 6 mois**\n- Prix actuel : ${info.get('currentPrice', 'N/A')}",
        "RSI": "**RSI (14j)**\n- <30: Survente (Achat)\n- >70: Surachat (Vente)",
        "P/E Ratio": f"**Price to Earnings**\n- Ratio : {format_number(info.get('trailingPE') or info.get('forwardPE'))}",
    }
    return details.get(indicator_name, "Détails non disponibles pour cet indicateur.")

# ---------------------------------------------------------
# INTERFACE UTILISATEUR
# ---------------------------------------------------------

tab_analyse, tab_top100, tab_perf_pos, tab_perf_neg = st.tabs([
    "🔍 Analyse",
    "🏆 Top 100", 
    "📈 Top Hausses",
    "📉 Top Baisses"
])

# ============================
# TAB 1: ANALYSE (Classique)
# ============================
with tab_analyse:
    st.subheader("🔍 Analyse Individuelle")
    col_left_pad, col_center_content, col_right_pad = st.columns([1, 4, 1])

    with col_center_content:
        if SEARCHBOX_AVAILABLE:
            def search_function(query: str):
                if not query or len(query) < 1: return ["AAPL - Apple Inc.", "GOOGL - Google", "MSFT - Microsoft", "NVDA - NVIDIA", "TSLA - Tesla"]
                return smart_search(query, limit=8) or []
            
            selected_company = st_searchbox(search_function, placeholder="🔍 Tapez : Apple, Tesla...", label="Recherche", key="company_searchbox")
            company = extract_ticker(selected_company) if selected_company else ""
        else:
            search_input = st.text_input("Entreprise ou Ticker", placeholder="Tapez : Apple...", key="fallback_search")
            company = search_input.upper() if search_input else ""

        col_radio, col_button = st.columns([2, 1])
        with col_radio:
            horizon = st.radio("Horizon", ["Court terme", "Long terme"], index=1, horizontal=True)
            h_code = 'court' if 'Court' in horizon else 'long'
        with col_button:
            st.markdown("<br>", unsafe_allow_html=True)
            analyze = st.button("ANALYSER", type="primary", use_container_width=True)

    st.markdown("---")

    if analyze or company:
        with st.spinner(f"Analyse de {company}..."):
            try:
                scorer = StockScorer(company, h_code)
                ticker = scorer.search_ticker(company)
                
                if not ticker:
                    st.error(f"❌ '{company}' non trouvé.")
                else:
                    final = StockScorer(ticker, h_code)
                    score = final.calculate_score()
                    
                    if score is None:
                        st.error("❌ Erreur de données.")
                    else:
                        st.subheader(f"🏢 {final.info.get('longName', ticker)} ({ticker})")
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Ticker", ticker)
                        c2.metric("Secteur", final.sector)
                        c3.metric("Prix", f"${final.info.get('currentPrice', 'N/A')}")
                        c4.metric("Score", f"{score}/100")
                        
                        st.divider()
                        
                        if score >= 70: st.success(f"🟢 **{score}/100 - ACHAT**")
                        elif score >= 40: st.warning(f"🟡 **{score}/100 - PRUDENCE**")
                        else: st.error(f"🔴 **{score}/100 - ÉVITER**")
                        
                        # Détails compacts
                        st.markdown("### 📊 Indicateurs")
                        for name, val in sorted(final.scores.items(), key=lambda x: x[1], reverse=True):
                            e = "🟢" if val >= 7 else "🟡" if val >= 4 else "🔴"
                            bar_color = "#00CC00" if val >= 7 else "#FFD700" if val >= 4 else "#FF4B4B"
                            with st.expander(f"{e} {name}: {val:.1f}/10"):
                                st.markdown(f"""<div style="background-color: #e0e0e0; border-radius: 5px; height: 15px;"><div style="background-color: {bar_color}; width: {(val/10)*100}%; height: 100%; border-radius: 5px;"></div></div>""", unsafe_allow_html=True)
                                st.write(get_calculation_details(final, name))

            except Exception as e:
                st.error(f"Erreur : {e}")

# ============================
# FONCTION D'AFFICHAGE COMPACT
# ============================
def display_compact_row(rank, ticker, name, price, mcap, p1d, p1y, is_header=False):
    cols = st.columns([0.4, 1, 2, 1, 1, 1, 1])
    
    if is_header:
        # En-tête
        cols[0].markdown("**#**")
        cols[1].markdown("**Ticker**")
        cols[2].markdown("**Nom**")
        cols[3].markdown("**Prix**")
        cols[4].markdown("**Cap.**")
        cols[5].markdown("**24h**")
        cols[6].markdown("**1 An**")
        st.markdown("<hr style='margin: 0; padding: 0;'>", unsafe_allow_html=True)
    else:
        # Lignes de données (Compact)
        cols[0].markdown(f"<span class='compact-text'>**{rank}**</span>", unsafe_allow_html=True)
        cols[1].markdown(f"<span class='compact-text'>**{ticker}**</span>", unsafe_allow_html=True)
        cols[2].markdown(f"<span class='compact-text' style='color:#555;'>{name[:25]}</span>", unsafe_allow_html=True)
        cols[3].markdown(f"<span class='compact-text'>${price:.2f}</span>", unsafe_allow_html=True)
        cols[4].markdown(f"<span class='compact-text'>{format_large_number(mcap)}</span>", unsafe_allow_html=True)
        cols[5].markdown(f"<span class='compact-text'>{format_percentage(p1d)}</span>", unsafe_allow_html=True)
        cols[6].markdown(f"<span class='compact-text'>{format_percentage(p1y)}</span>", unsafe_allow_html=True)
        st.markdown("<hr class='compact-divider'>", unsafe_allow_html=True)

# ============================
# TAB 2: TOP 100 (COMPACT)
# ============================
with tab_top100:
    st.caption("Classement par Capitalisation Boursière")
    
    # Chargement silencieux
    with st.spinner("Chargement..."):
        stock_data = []
        progress = st.progress(0)
        for i, ticker in enumerate(MAJOR_STOCKS):
            d = get_stock_data(ticker)
            if d: stock_data.append(d)
            progress.progress((i+1)/len(MAJOR_STOCKS))
        progress.empty()
        
        df = pd.DataFrame(stock_data)
        
        if not df.empty:
            df = df.sort_values('market_cap', ascending=False).reset_index(drop=True)
            
            # Header
            display_compact_row(0,0,0,0,0,0,0, is_header=True)
            
            # Rows
            for idx, row in df.iterrows():
                display_compact_row(
                    idx + 1,
                    row['ticker'],
                    row['name'],
                    row['price'],
                    row['market_cap'],
                    row['perf_1d'],
                    row['perf_1y']
                )

# ============================
# TAB 3: TOP HAUSSES (COMPACT)
# ============================
with tab_perf_pos:
    st.caption("Meilleures performances sur 1 an")
    if 'stock_data' in locals() and stock_data:
        df = pd.DataFrame(stock_data)
        df = df.sort_values('perf_1y', ascending=False).reset_index(drop=True)
        
        display_compact_row(0,0,0,0,0,0,0, is_header=True)
        for idx, row in df.head(50).iterrows():
            display_compact_row(idx+1, row['ticker'], row['name'], row['price'], row['market_cap'], row['perf_1d'], row['perf_1y'])

# ============================
# TAB 4: TOP BAISSES (COMPACT)
# ============================
with tab_perf_neg:
    st.caption("Pires performances sur 1 an")
    if 'stock_data' in locals() and stock_data:
        df = pd.DataFrame(stock_data)
        df = df.sort_values('perf_1y', ascending=True).reset_index(drop=True)
        
        display_compact_row(0,0,0,0,0,0,0, is_header=True)
        for idx, row in df.head(50).iterrows():
            display_compact_row(idx+1, row['ticker'], row['name'], row['price'], row['market_cap'], row['perf_1d'], row['perf_1y'])

# ---------------------------------------------------------
# STYLES CSS ULTRA-COMPACTS
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Réduire les marges globales */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Style du texte compact dans les tableaux */
    .compact-text {
        font-size: 14px;
        line-height: 1.2;
    }
    
    /* Réduire l'espacement entre les colonnes Streamlit */
    div[data-testid="column"] {
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }
    
    /* Réduire les marges des paragraphes Markdown pour coller les lignes */
    div[data-testid="stMarkdownContainer"] p {
        margin-bottom: 2px !important;
    }
    
    /* Style du séparateur ultra-fin */
    .compact-divider {
        margin-top: 2px !important;
        margin-bottom: 2px !important;
        border-top: 1px solid #e0e0e0;
    }
    
    /* Cacher les padding par défaut de Streamlit */
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 10px;
    }
</style>
""", unsafe_allow_html=True)
