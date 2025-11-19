import streamlit as st
import sys, os
import yfinance as yf
import pandas as pd
import time
import plotly.graph_objects as go
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from Algorithmev1 import StockScorer

st.set_page_config(page_title="Analyseur Actions Boursières", page_icon="📈", layout="wide")

# --- TITRE CLIQUABLE (RETOUR ACCUEIL) ---
# Utilisation de HTML pour créer un lien qui recharge la page (.)
st.markdown("""
    <a href="." target="_self" style="text-decoration: none; color: inherit;">
        <h1 style="margin-top: 0; padding-top: 0;">📈 Analyseur d'Actions Boursières</h1>
    </a>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DONNÉES POUR LES CLASSEMENTS
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
        hist = stock.history(period="3mo")
        
        if hist.empty or not info: return None
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or (hist['Close'][-1] if not hist.empty else None)
        market_cap = info.get('marketCap', 0)
        
        if not current_price or current_price <= 0: return None
        
        # Calculs de performance
        perf_1d = ((hist['Close'][-1] - hist['Close'][-2]) / hist['Close'][-2] * 100) if len(hist) >= 2 else 0
        perf_7d = ((hist['Close'][-1] - hist['Close'][-6]) / hist['Close'][-6] * 100) if len(hist) >= 6 else 0
        perf_30d = ((hist['Close'][-1] - hist['Close'][-22]) / hist['Close'][-22] * 100) if len(hist) >= 22 else 0
        perf_1y = info.get('52WeekChange', 0) * 100
        
        return {
            'ticker': ticker,
            'name': info.get('longName', ticker),
            'price': current_price,
            'market_cap': market_cap,
            'perf_1d': perf_1d,
            'perf_7d': perf_7d,
            'perf_30d': perf_30d,
            'perf_1y': perf_1y
        }
    except: return None

def format_large_number(num):
    if num >= 1e12: return f"${num/1e12:.2f}T"
    elif num >= 1e9: return f"${num/1e9:.2f}B"
    elif num >= 1e6: return f"${num/1e6:.2f}M"
    else: return f"${num:,.0f}"

def format_percentage(value):
    if value is None: return "N/A"
    if value > 0: return f'<span style="color: #00CC00;">▲ {value:.2f}%</span>'
    elif value < 0: return f'<span style="color: #FF4B4B;">▼ {abs(value):.2f}%</span>'
    else: return f'<span style="color: #888888;">• {value:.2f}%</span>'

# ---------------------------------------------------------
# FONCTIONS D'ANALYSE
# ---------------------------------------------------------
def get_valuation_analysis(info):
    pe = info.get('trailingPE') or info.get('forwardPE')
    peg = info.get('pegRatio')
    pb = info.get('priceToBook')
    signals = []
    
    if pe and pe > 0:
        if pe < 15: signals.append(("P/E Ratio", pe, "🟢 Sous-évalué", f"P/E de {pe:.2f} (< 15)"))
        elif pe < 25: signals.append(("P/E Ratio", pe, "🟡 Équilibré", f"P/E de {pe:.2f} (15-25)"))
        else: signals.append(("P/E Ratio", pe, "🔴 Surévalué", f"P/E de {pe:.2f} (> 25)"))
    
    if peg and peg > 0:
        if peg < 1: signals.append(("PEG Ratio", peg, "🟢 Sous-évalué", f"PEG de {peg:.2f} (< 1)"))
        elif peg < 2: signals.append(("PEG Ratio", peg, "🟡 Équilibré", f"PEG de {peg:.2f} (1-2)"))
        else: signals.append(("PEG Ratio", peg, "🔴 Surévalué", f"PEG de {peg:.2f} (> 2)"))
    
    if pb and pb > 0:
        if pb < 1: signals.append(("P/B Ratio", pb, "🟢 Sous-évalué", f"P/B de {pb:.2f} (< 1)"))
        elif pb < 3: signals.append(("P/B Ratio", pb, "🟡 Équilibré", f"P/B de {pb:.2f} (1-3)"))
        else: signals.append(("P/B Ratio", pb, "🔴 Surévalué", f"P/B de {pb:.2f} (> 3)"))
    
    if not signals: return None, "⚠️ Données insuffisantes"
    
    green = sum(1 for s in signals if "🟢" in s[2])
    red = sum(1 for s in signals if "🔴" in s[2])
    
    if green > red: verdict = "🟢 **SOUS-ÉVALUÉE**"
    elif red > green: verdict = "🔴 **SURÉVALUÉE**"
    else: verdict = "🟡 **ÉQUILIBRÉE**"
    return signals, verdict

def get_calculation_details(scorer, indicator_name):
    info = scorer.info
    def fmt(v): return f"{float(v):,.2f}" if v else "N/A"
    
    details = {
        "Momentum 6M": f"Prix: ${info.get('currentPrice','N/A')} | Haut 52s: ${info.get('fiftyTwoWeekHigh','N/A')}",
        "RSI": "RSI (14j) : <30 (Achat), >70 (Vente)",
        "P/E Ratio": f"Ratio: {fmt(info.get('trailingPE') or info.get('forwardPE'))}",
    }
    return details.get(indicator_name, "Détails non disponibles.")

# ---------------------------------------------------------
# INTERFACE
# ---------------------------------------------------------
tab_analyse, tab_top100, tab_perf_pos, tab_perf_neg = st.tabs([
    "🔍 Analyse Complète", "🏆 Top 100", "📈 Top Hausses", "📉 Top Baisses"
])

# ============================
# TAB 1: ANALYSE
# ============================
with tab_analyse:
    st.header("🔍 Démarrez l'Analyse")

    col_input, col_radio, col_btn = st.columns([2, 2, 1])
    
    with col_input:
        ticker_input = st.text_input("Entrez le Ticker de l'action", placeholder="ex: AAPL, TSLA, TTE...", label_visibility="collapsed")
        company = ticker_input.strip().upper() if ticker_input else ""
    
    with col_radio:
        horizon = st.radio("Horizon", ["Court terme", "Long terme"], index=1, horizontal=True, label_visibility="collapsed")
        h_code = 'court' if 'Court' in horizon else 'long'
        
    with col_btn:
        analyze = st.button("🚀 ANALYSER", type="primary", use_container_width=True)

    st.markdown("---")

    # --- ÉCRAN D'ACCUEIL ---
    if not company:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.header("ℹ️ Comment ça marche ?")
            st.markdown("""
            **L'Analyseur d'Actions Boursières** évalue la santé financière selon :
            1. 🏢 **Secteur d'activité**
            2. ⏰ **Horizon d'investissement**
            3. 📊 **100+ indicateurs financiers**
            
            ### 🎯 Échelle de notation
            """)
            ca, cb, cc = st.columns(3)
            ca.success("**70-100**\n\n🟢 Bon")
            cb.warning("**40-70**\n\n🟡 Moyen")
            cc.error("**0-40**\n\n🔴 Éviter")
        with col2:
            st.header("💡 Exemples de Tickers")
            st.info("🍎 **AAPL** (Apple)")
            st.info("⚡ **TSLA** (Tesla)")
            st.info("🛢️ **TTE** (TotalEnergies)")
            st.info("🏦 **JPM** (JPMorgan)")
        
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("📊 Indicateurs", "100+")
        c2.metric("🌍 Couverture", "Global")
        c3.metric("⚡ Vitesse", "< 5 sec")

    # --- RÉSULTATS ---
    elif analyze or company:
        with st.spinner(f"Analyse de {company}..."):
            try:
                scorer = StockScorer(company, h_code)
                if not scorer.fetch_data():
                    st.error(f"❌ Ticker '{company}' introuvable ou données invalides.")
                else:
                    final = scorer
                    score = final.calculate_score()
                    info = final.info
                    
                    st.subheader(f"🏢 **{info.get('longName', company)}** ({company})")
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Ticker", company)
                    c2.metric("Secteur", final.sector)
                    c3.metric("Prix", f"${info.get('currentPrice', 'N/A')}")
                    c4.metric("Score", f"{score}/100")
                    
                    st.divider()
                    
                    if score >= 70: st.success(f"## 🟢 {score}/100 - ACHAT")
                    elif score >= 40: st.warning(f"## 🟡 {score}/100 - PRUDENCE")
                    else: st.error(f"## 🔴 {score}/100 - ÉVITER")
                    
                    st.markdown("### 💰 Valorisation")
                    val_sigs, val_verdict = get_valuation_analysis(info)
                    if val_sigs:
                        st.markdown(val_verdict)
                        with st.expander("Détails valorisation"):
                            for n, v, s, d in val_sigs: st.markdown(f"**{n}**: {s} ({d})")
                    
                    st.markdown("---")
                    
                    # Radar Chart
                    col_radar, col_top = st.columns([2, 1])
                    with col_radar:
                        cats = list(final.scores.keys())
                        vals = list(final.scores.values())
                        fig = go.Figure()
                        fig.add_trace(go.Scatterpolar(r=vals, theta=cats, fill='toself', name='Scores', line=dict(color='#FF4B4B', width=2), fillcolor='rgba(255, 75, 75, 0.3)'))
                        fig.add_trace(go.Scatterpolar(r=[7]*len(cats), theta=cats, name='Seuil Bon', line=dict(color='#00CC00', width=2, dash='dash'), showlegend=True))
                        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), height=450, margin=dict(l=80,r=80,t=20,b=20))
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col_top:
                        st.markdown("#### 💪 Top 3 Forces")
                        forces = sorted([(n, v) for n, v in final.scores.items() if v >= 7], key=lambda x:x[1], reverse=True)[:3]
                        if forces:
                            for i, (n, v) in enumerate(forces, 1): st.success(f"**{i}. {n}**\n\n{v:.1f}/10")
                        else: st.info("Aucune force majeure.")

                    st.markdown("---")
                    
                    # Détails barres
                    st.markdown("### 📊 Indicateurs Détaillés")
                    for name, val in sorted(final.scores.items(), key=lambda x: x[1], reverse=True):
                        e = "🟢" if val >= 7 else "🟡" if val >= 4 else "🔴"
                        color = "#00CC00" if val >= 7 else "#FFD700" if val >= 4 else "#FF4B4B"
                        with st.expander(f"{e} **{name}**: {val:.1f}/10"):
                            st.markdown(f"""<div style="background:#e0e0e0;border-radius:10px;height:20px;"><div style="background:{color};width:{val*10}%;height:100%;border-radius:10px;"></div></div>""", unsafe_allow_html=True)
                            st.markdown(get_calculation_details(final, name))
                    
                    st.markdown("---")

                    # --- INFOS COMPLÉMENTAIRES ---
                    st.markdown("### 📊 Informations Complémentaires")
                    col1_info, col2_info = st.columns(2)
                    with col1_info:
                        st.markdown("**📈 Données de Marché**")
                        st.write(f"- **Capitalisation** : ${info.get('marketCap', 0):,.0f}")
                        st.write(f"- **Volume moyen** : {info.get('averageVolume', 0):,.0f}")
                        st.write(f"- **Plus haut 52 sem** : ${info.get('fiftyTwoWeekHigh', 'N/A')}")
                        st.write(f"- **Plus bas 52 sem** : ${info.get('fiftyTwoWeekLow', 'N/A')}")
                        
                        high_52 = info.get('fiftyTwoWeekHigh')
                        low_52 = info.get('fiftyTwoWeekLow')
                        current_price = info.get('currentPrice')
                        if all([high_52, low_52, current_price]) and (high_52 - low_52) > 0:
                            position = ((current_price - low_52) / (high_52 - low_52)) * 100
                            st.write(f"- **Position fourchette 52 sem** : {position:.1f}%")
                    with col2_info:
                        st.markdown("**💼 Ratios Financiers**")
                        pe_ratio = info.get('trailingPE') or info.get('forwardPE')
                        st.write(f"- **P/E Ratio** : {f'{pe_ratio:.2f}' if pe_ratio else 'N/A'}")
                        st.write(f"- **PEG Ratio** : {f'{info.get('pegRatio'):.2f}' if info.get('pegRatio') else 'N/A'}")
                        st.write(f"- **Price to Book** : {f'{info.get('priceToBook'):.2f}' if info.get('priceToBook') else 'N/A'}")
                        div_yield = info.get('dividendYield')
                        st.write(f"- **Dividend Yield** : {f'{div_yield*100:.2f}%' if div_yield else 'N/A'}")
                        beta = info.get('beta')
                        st.write(f"- **Beta** : {f'{beta:.2f}' if beta else 'N/A'}")
                    
                    st.markdown("---")
                    
                    # --- GRAPHIQUE PRIX ---
                    # Layout ajusté pour serrer les boutons
                    col_title, col_btns_spacer, col_btns = st.columns([1.5, 3.5, 3])
                    with col_title:
                        st.markdown("### 📈 Évolution Prix")
                    
                    per_opts = [("1S","5d"),("1M","1mo"),("3M","3mo"),("6M","6mo"),("1A","1y"),("5A","5y"), ("MAX", "max")]
                    if 'sel_per' not in st.session_state: st.session_state.sel_per = "1A"
                    
                    with col_btns:
                        # gap="small" pour réduire l'espace par défaut
                        cols_btns_inner = st.columns(len(per_opts), gap="small")
                        for i, (l, c) in enumerate(per_opts):
                            with cols_btns_inner[i]:
                                if st.button(l, key=f"p_{l}", type="primary" if st.session_state.sel_per==l else "secondary", use_container_width=True):
                                    st.session_state.sel_per = l
                                    st.rerun()
                            
                    sel_code = dict(per_opts)[st.session_state.sel_per]
                    hist = final.stock.history(period=sel_code)
                    
                    if not hist.empty:
                        y_min = hist['Close'].min()
                        y_max = hist['Close'].max()
                        margin = (y_max - y_min) * 0.05
                        y_range = [y_min - margin, y_max + margin]

                        perf = ((hist['Close'][-1] - hist['Close'][0])/hist['Close'][0])*100
                        
                        if perf > 0:
                            line_col = '#00CC00'
                            fill_col = 'rgba(0, 204, 0, 0.1)'
                        else:
                            line_col = '#FF4B4B'
                            fill_col = 'rgba(255, 75, 75, 0.1)'
                            
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=hist.index, 
                            y=hist['Close'], 
                            mode='lines', 
                            line=dict(color=line_col, width=2), 
                            fill='tozeroy', 
                            fillcolor=fill_col
                        ))
                        
                        fig.update_layout(
                            height=400, 
                            margin=dict(l=0,r=0,t=10,b=0), 
                            showlegend=False,
                            yaxis=dict(range=y_range)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

            except Exception as e:
                st.error(f"Erreur: {e}")

# ============================
# FONCTION AFFICHAGE LIGNE
# ============================
def display_row(rank, ticker, name, price, mcap, p1d, p7d, p30d, p1y, is_header=False):
    cols = st.columns([0.4, 0.8, 2, 1, 1.2, 1, 1, 1, 1])
    if is_header:
        cols[0].markdown("**#**")
        cols[1].markdown("**Ticker**")
        cols[2].markdown("**Nom**")
        cols[3].markdown("**Prix**")
        cols[4].markdown("**Cap.**")
        cols[5].markdown("**24h**")
        cols[6].markdown("**1 Sem**")
        cols[7].markdown("**1 Mois**")
        cols[8].markdown("**1 An**")
        st.markdown("<hr style='margin:0;padding:0;border-top:2px solid #555;'>", unsafe_allow_html=True)
    else:
        cols[0].markdown(f"<span class='row-text'>**{rank}**</span>", unsafe_allow_html=True)
        cols[1].markdown(f"<span class='row-text'>**{ticker}**</span>", unsafe_allow_html=True)
        cols[2].markdown(f"<span class='row-text' style='color:#555;'>{name[:20]}</span>", unsafe_allow_html=True)
        cols[3].markdown(f"<span class='row-text'>${price:.2f}</span>", unsafe_allow_html=True)
        cols[4].markdown(f"<span class='row-text'>{format_large_number(mcap)}</span>", unsafe_allow_html=True)
        cols[5].markdown(f"<span class='row-text'>{format_percentage(p1d)}</span>", unsafe_allow_html=True)
        cols[6].markdown(f"<span class='row-text'>{format_percentage(p7d)}</span>", unsafe_allow_html=True)
        cols[7].markdown(f"<span class='row-text'>{format_percentage(p30d)}</span>", unsafe_allow_html=True)
        cols[8].markdown(f"<span class='row-text'>{format_percentage(p1y)}</span>", unsafe_allow_html=True)
        st.markdown("<hr class='row-divider'>", unsafe_allow_html=True)

# ============================
# TABS CLASSEMENTS
# ============================
def render_ranking(sort_col, ascending):
    with st.spinner("Chargement..."):
        data = []
        prog = st.progress(0)
        for i, t in enumerate(MAJOR_STOCKS):
            d = get_stock_data(t)
            if d: data.append(d)
            prog.progress((i+1)/len(MAJOR_STOCKS))
        prog.empty()
        
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values(sort_col, ascending=ascending).reset_index(drop=True)
            display_row(0,0,0,0,0,0,0,0,0, is_header=True)
            for i, r in df.head(50).iterrows():
                display_row(i+1, r['ticker'], r['name'], r['price'], r['market_cap'], r['perf_1d'], r['perf_7d'], r['perf_30d'], r['perf_1y'])

with tab_top100: render_ranking('market_cap', False)
with tab_perf_pos: render_ranking('perf_1y', False)
with tab_perf_neg: render_ranking('perf_1y', True)

# ---------------------------------------------------------
# CSS
# ---------------------------------------------------------
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .row-text { font-size: 15px; line-height: 1.6; vertical-align: middle; }
    
    /* Réduction padding horizontal des colonnes pour serrer les boutons */
    div[data-testid="column"] { 
        padding: 0px 1px !important; 
    }
    
    .row-divider { margin-top: 5px !important; margin-bottom: 5px !important; border-top: 1px solid #f0f0f0; }
    
    /* Boutons compacts et arrondis */
    div[data-testid="stColumn"] button { 
        padding: 1px 8px !important;
        font-size: 0.75em !important; 
        min-height: 1.5em !important;
        line-height: 1.2 !important;
        border-radius: 15px !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
    }

    h3 { margin-top: 1.5rem; margin-bottom: 0.5rem; }
    h4 { margin-top: 1.2rem; margin-bottom: 0.4rem; }
    label[for^="st-radio"] div[data-testid="stWidgetLabel"] { display: none; }

</style>
""", unsafe_allow_html=True)
