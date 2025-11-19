import streamlit as st
import sys, os
import yfinance as yf
import pandas as pd
import time
import plotly.graph_objects as go
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))
# Assurez-vous que le fichier s'appelle bien Algorithmev1.py
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
# DONNÉES ET FONCTIONS POUR LES CLASSEMENTS (TABS 2, 3, 4)
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
    if num >= 1e12:
        return f"${num/1e12:.2f}T"
    elif num >= 1e9:
        return f"${num/1e9:.2f}B"
    elif num >= 1e6:
        return f"${num/1e6:.2f}M"
    else:
        return f"${num:,.0f}"

def format_percentage(value):
    if value > 0:
        return f'<span style="color: #00CC00;">▲ {value:.2f}%</span>'
    elif value < 0:
        return f'<span style="color: #FF4B4B;">▼ {abs(value):.2f}%</span>'
    else:
        return f'<span style="color: #888888;">• {value:.2f}%</span>'

# ---------------------------------------------------------
# FONCTIONS D'ANALYSE DÉTAILLÉE (TAB 1)
# ---------------------------------------------------------
def get_valuation_analysis(info):
    """Analyse la valorisation de l'entreprise (sur/sous-évaluée)"""
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
        return None, "⚠️ Données insuffisantes pour l'analyse de valorisation"
    
    green_count = sum(1 for s in signals if "🟢" in s[2])
    red_count = sum(1 for s in signals if "🔴" in s[2])
    
    if green_count > red_count:
        verdict = "🟢 **SOUS-ÉVALUÉE** - L'action semble attractive par rapport à ses fondamentaux"
    elif red_count > green_count:
        verdict = "🔴 **SURÉVALUÉE** - L'action semble chère par rapport à ses fondamentaux"
    else:
        verdict = "🟡 **VALORISATION ÉQUILIBRÉE** - L'action est valorisée à un niveau raisonnable"
    
    return signals, verdict

def get_calculation_details(scorer, indicator_name):
    """Retourne les détails de calcul pour chaque indicateur"""
    info = scorer.info
    
    def format_percentage(value):
        if value is None or value == 'N/A': return 'N/A'
        try: return f"{float(value) * 100:.2f}%" if abs(float(value)) < 1 else f"{float(value):.2f}%"
        except: return str(value)
    
    def format_number(value):
        if value is None or value == 'N/A': return 'N/A'
        try: return f"{float(value):,.2f}"
        except: return str(value)
    
    details = {
        "Momentum 6M": f"**Calcul du Momentum sur 6 mois**\n- Prix actuel : ${info.get('currentPrice', 'N/A')}\n- Plus haut 52s : ${info.get('fiftyTwoWeekHigh', 'N/A')}\n- Plus bas 52s : ${info.get('fiftyTwoWeekLow', 'N/A')}",
        "Momentum 3M": f"**Calcul du Momentum sur 3 mois**\n- Prix actuel : ${info.get('currentPrice', 'N/A')}",
        "RSI": "**Relative Strength Index (14j)**\n- <30: Survente (Achat)\n- >70: Surachat (Vente)",
        "P/E Ratio": f"**Price to Earnings**\n- Ratio : {format_number(info.get('trailingPE') or info.get('forwardPE'))}",
        "PEG Ratio": f"**PEG (P/E to Growth)**\n- PEG : {format_number(info.get('pegRatio'))}\n- <1 : Sous-évalué",
        "Croissance CA": f"**Croissance CA**\n- Taux : {format_percentage(info.get('revenueGrowth'))}",
        "Marges": f"**Marge Nette**\n- Taux : {format_percentage(info.get('profitMargins'))}",
        "Marge Opé": f"**Marge Opérationnelle**\n- Taux : {format_percentage(info.get('operatingMargins'))}",
        "ROE": f"**Return on Equity**\n- Taux : {format_percentage(info.get('returnOnEquity'))}",
        "Dette/Capitaux": f"**Dette/Equity**\n- Ratio : {format_number(info.get('debtToEquity'))}",
        "Free Cash Flow": f"**Free Cash Flow**\n- Montant : ${format_number(info.get('freeCashflow'))}",
        "Beta": f"**Beta (Volatilité)**\n- Beta : {format_number(info.get('beta'))}\n- <1 : Moins volatil que le marché",
        "Liquidité": f"**Current Ratio**\n- Ratio : {format_number(info.get('currentRatio'))}",
        "Dividende": f"**Rendement Dividende**\n- Yield : {format_percentage(info.get('dividendYield'))}",
        "Price to Book": f"**Price to Book**\n- Ratio : {format_number(info.get('priceToBook'))}"
    }
    return details.get(indicator_name, "Détails non disponibles pour cet indicateur.")

# ---------------------------------------------------------
# INTERFACE UTILISATEUR AVEC ONGLETS
# ---------------------------------------------------------

tab_analyse, tab_top100, tab_perf_pos, tab_perf_neg = st.tabs([
    "🔍 Analyse Individuelle",
    "🏆 Top 100 Capitalisation", 
    "📈 Meilleures Perfs 1Y",
    "📉 Pires Perfs 1Y"
])

# =========================================================
# ONGLET 1: ANALYSE INDIVIDUELLE (VOTRE CODE ORIGINAL)
# =========================================================
with tab_analyse:
    st.header("🔍 Démarrez l'Analyse")

    col_left_pad, col_center_content, col_right_pad = st.columns([1, 4, 1])

    with col_center_content:
        if SEARCHBOX_AVAILABLE:
            def search_function(query: str):
                if not query or len(query) < 1:
                    return ["AAPL - Apple Inc.", "GOOGL - Alphabet Inc. (Google)", "MSFT - Microsoft Corporation", "NVDA - NVIDIA Corporation", "TSLA - Tesla Inc."]
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
            company = extract_ticker(selected_company) if selected_company else ""
        else:
            st.markdown("**Rechercher une entreprise**")
            search_input = st.text_input("Entreprise ou Ticker", placeholder="Tapez : Ferrari, Apple, RACE...", key="fallback_search", label_visibility="collapsed")
            if search_input and len(search_input) >= 1:
                suggestions = smart_search(search_input, limit=6)
                if suggestions and not suggestions[0].startswith("❌"):
                    st.markdown("**💡 Suggestions :**")
                    cols = st.columns(2)
                    for idx, suggestion in enumerate(suggestions[:6]):
                        with cols[idx % 2]:
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

    if not company:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.header("ℹ️ Comment ça marche ?")
            st.markdown("""
            **L'Analyseur** évalue la santé financière selon :
            1. 🏢 **Secteur** (Tech, Finance...)
            2. ⏰ **Horizon** (Court/Long terme)
            3. 📊 **100+ indicateurs**
            """)
            ca, cb, cc = st.columns(3)
            ca.success("**70-100**\n\n🟢 Bon")
            cb.warning("**40-70**\n\n🟡 Moyen")
            cc.error("**0-40**\n\n🔴 Éviter")
        with col2:
            st.header("💡 Exemples")
            st.info("🍎 **Apple (AAPL)**")
            st.info("⚡ **Tesla (TSLA)**")
            st.info("🛢️ **TotalEnergies (TTE)**")

    elif analyze or company:
        with st.spinner(f"🔍 Analyse en cours de **{company}** pour l'horizon **{horizon}**..."):
            try:
                scorer = StockScorer(company, h_code)
                ticker = scorer.search_ticker(company)
                
                if not ticker:
                    st.error(f"❌ Entreprise ou Ticker '{company}' non trouvée.")
                else:
                    final = StockScorer(ticker, h_code)
                    score = final.calculate_score()
                    
                    if score is None:
                        st.error("❌ Impossible de calculer le score.")
                    else:
                        # --- AFFICHAGE DES RÉSULTATS (ORIGINAL APP.PY) ---
                        st.subheader(f"🏢 **{final.info.get('longName', ticker)}** ({ticker})")
                        st.markdown(f"**Horizon d'Analyse :** {horizon}")
                        
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Ticker", ticker)
                        c2.metric("Secteur", final.sector)
                        c3.metric("Prix Actuel", f"${final.info.get('currentPrice', 'N/A')}")
                        c4.metric("Score Global", f"{score}/100")
                        
                        st.markdown("---")
                        
                        if score >= 70:
                            st.success(f"## 🟢 {score}/100 - RECOMMANDATION : ACHAT")
                            st.markdown("**Conclusion :** Forte santé financière et bonnes perspectives.")
                        elif score >= 40:
                            st.warning(f"## 🟡 {score}/100 - RECOMMANDATION : PRUDENCE")
                            st.markdown("**Conclusion :** Forces et faiblesses équilibrées.")
                        else:
                            st.error(f"## 🔴 {score}/100 - RECOMMANDATION : ÉVITER")
                            st.markdown("**Conclusion :** Signes de faiblesse importants.")
                        
                        st.markdown("---")
                        
                        st.markdown("### 💰 Analyse de Valorisation")
                        valuation_signals, valuation_verdict = get_valuation_analysis(final.info)
                        if valuation_signals:
                            st.markdown(valuation_verdict)
                            with st.expander("📊 Voir les ratios de valorisation"):
                                for name, value, signal, description in valuation_signals:
                                    col1, col2 = st.columns([3, 1])
                                    with col1: st.markdown(f"**{name}** : {description}")
                                    with col2: st.markdown(signal)
                        else:
                            st.info(valuation_verdict)
                        
                        st.markdown("---")
                        
                        st.markdown("### 🎯 Vue d'ensemble des Performances")
                        col_radar, col_top = st.columns([2, 1])
                        
                        with col_radar:
                            categories = list(final.scores.keys())
                            values = list(final.scores.values())
                            fig = go.Figure()
                            fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill='toself', name='Scores', line=dict(color='#FF4B4B', width=2), fillcolor='rgba(255, 75, 75, 0.3)'))
                            fig.add_trace(go.Scatterpolar(r=[7]*len(categories), theta=categories, name='Seuil Bon (7/10)', line=dict(color='#00CC00', width=2, dash='dash'), showlegend=True))
                            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), height=450, margin=dict(l=80, r=80, t=20, b=20))
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col_top:
                            st.markdown("#### 💪 Top 3 Forces")
                            forces = [(name, val) for name, val in final.scores.items() if val >= 7]
                            top_forces = sorted(forces, key=lambda x: x[1], reverse=True)[:3]
                            if top_forces:
                                for i, (name, val) in enumerate(top_forces, 1):
                                    st.success(f"**{i}. {name}**\n\n{val:.1f}/10")
                            else:
                                st.info("Aucune force majeure détectée.")

                        st.markdown("---")
                        st.markdown("### 📊 Indicateurs Détaillés (Performance sur 10)")
                        
                        for name, val in sorted(final.scores.items(), key=lambda x: x[1], reverse=True):
                            e = "🟢" if val >= 7 else "🟡" if val >= 4 else "🔴"
                            bar_color = "#00CC00" if val >= 7 else "#FFD700" if val >= 4 else "#FF4B4B"
                            
                            with st.expander(f"{e} **{name}**: **{val:.2f}**/10"):
                                progress_percent = (val / 10) * 100
                                st.markdown(f"""<div style="position: relative; background-color: #e0e0e0; border-radius: 10px; height: 25px; margin: 10px 0;"><div style="background-color: {bar_color}; width: {progress_percent}%; height: 100%; border-radius: 10px;"></div><div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: #333; font-weight: bold; font-size: 12px;">{val:.1f}/10</div></div>""", unsafe_allow_html=True)
                                st.markdown("#### 📋 Détails du calcul")
                                st.markdown(get_calculation_details(final, name))
                        
                        st.markdown("---")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**📊 Données de Marché**")
                            st.write(f"- **Cap** : ${final.info.get('marketCap', 0):,.0f}")
                            st.write(f"- **Vol. Moy** : {final.info.get('averageVolume', 0):,.0f}")
                        with col2:
                            st.markdown("**💼 Ratios**")
                            st.write(f"- **P/E** : {final.info.get('trailingPE', 'N/A')}")
                            st.write(f"- **Yield** : {final.info.get('dividendYield', 0)*100:.2f}%")
                        
                        st.markdown("---")
                        st.markdown("### 📈 Évolution du Prix")
                        
                        # Sélecteur de période
                        period_options = [("1S", "5d"), ("1M", "1mo"), ("3M", "3mo"), ("6M", "6mo"), ("1A", "1y"), ("YTD", "ytd"), ("5A", "5y"), ("MAX", "max")]
                        if 'selected_period_key' not in st.session_state: st.session_state.selected_period_key = "1A"
                        
                        col_spacer, col_buttons = st.columns([2, 2])
                        with col_buttons:
                            cols = st.columns(8)
                            for idx, (label, period_code) in enumerate(period_options):
                                with cols[idx]:
                                    if st.button(label, key=f"period_{label}", use_container_width=True, type="primary" if st.session_state.selected_period_key == label else "secondary"):
                                        st.session_state.selected_period_key = label
                                        st.rerun()
                        
                        selected_period = dict(period_options)[st.session_state.selected_period_key]
                        hist = final.stock.history(period=selected_period)
                        
                        if not hist.empty:
                            perf_period = ((hist['Close'][-1] - hist['Close'][0]) / hist['Close'][0]) * 100
                            plot_color = '#00CC00' if perf_period > 0 else '#FF4B4B'
                            fill_color = 'rgba(0, 204, 0, 0.1)' if perf_period > 0 else 'rgba(255, 75, 75, 0.1)'
                            
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], mode='lines', name='Prix', line=dict(color=plot_color, width=2.5), fill='tozeroy', fillcolor=fill_color))
                            fig.update_layout(xaxis_title="Date", yaxis_title="Prix ($)", height=400, showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        else:
                            st.info("Historique non disponible")

            except Exception as e:
                st.error(f"Erreur inattendue : {e}")

# =========================================================
# ONGLET 2: TOP 100
# =========================================================
with tab_top100:
    st.header("🏆 Top 100 Capitalisation Boursière")
    col1, col2 = st.columns([3, 1])
    with col1: st.info("📊 ~70 actions US principales")
    with col2:
        if st.button("🔄 Actualiser", key="refresh_top100", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    with st.spinner("Chargement..."):
        stock_data = []
        progress_bar = st.progress(0)
        for idx, ticker in enumerate(MAJOR_STOCKS):
            data = get_stock_data(ticker)
            if data: stock_data.append(data)
            progress_bar.progress((idx + 1) / len(MAJOR_STOCKS))
            time.sleep(0.01)
        progress_bar.empty()
        
        df = pd.DataFrame(stock_data)
        if not df.empty:
            df = df.sort_values('market_cap', ascending=False).reset_index(drop=True)
            df.index = df.index + 1
            
            for idx, row in df.iterrows():
                c1, c2, c3, c4, c5, c6 = st.columns([0.3, 1.5, 0.8, 1.2, 0.8, 0.8])
                with c1: st.markdown(f"**{idx}**")
                with c2: 
                    st.markdown(f"**{row['ticker']}**")
                    st.caption(row['name'][:25])
                with c3: st.markdown(f"${row['price']:.2f}")
                with c4: st.markdown(format_large_number(row['market_cap']))
                with c5: st.markdown(format_percentage(row['perf_1d']), unsafe_allow_html=True)
                with c6: st.markdown(format_percentage(row['perf_1y']), unsafe_allow_html=True)
                st.divider()

# =========================================================
# ONGLET 3: MEILLEURES PERFS
# =========================================================
with tab_perf_pos:
    st.header("📈 Top 50 Meilleures Performances 1 an")
    col1, col2 = st.columns([3, 1])
    with col1: st.info("🚀 Les plus fortes hausses")
    with col2:
        if st.button("🔄 Actualiser", key="refresh_perf_pos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    with st.spinner("Chargement..."):
        if 'stock_data' not in locals() or not stock_data:
            stock_data = []
            for ticker in MAJOR_STOCKS:
                data = get_stock_data(ticker)
                if data: stock_data.append(data)
        
        df = pd.DataFrame(stock_data)
        if not df.empty:
            df_sorted = df.sort_values('perf_1y', ascending=False).reset_index(drop=True)
            df_sorted.index = df_sorted.index + 1
            
            for idx, row in df_sorted.head(50).iterrows():
                c1, c2, c3, c4, c5 = st.columns([0.3, 1.5, 0.8, 1.2, 1.2])
                with c1: st.markdown("🥇" if idx==1 else "🥈" if idx==2 else "🥉" if idx==3 else f"**{idx}**")
                with c2: 
                    st.markdown(f"**{row['ticker']}**")
                    st.caption(row['name'][:25])
                with c3: st.markdown(f"${row['price']:.2f}")
                with c4: st.markdown(format_large_number(row['market_cap']))
                with c5: st.markdown(f'<span style="color: #00CC00; font-weight: bold;">▲ {row["perf_1y"]:.1f}%</span>', unsafe_allow_html=True)
                st.divider()

# =========================================================
# ONGLET 4: PIRES PERFS
# =========================================================
with tab_perf_neg:
    st.header("📉 Top 50 Pires Performances 1 an")
    col1, col2 = st.columns([3, 1])
    with col1: st.info("⚠️ Les plus fortes baisses")
    with col2:
        if st.button("🔄 Actualiser", key="refresh_perf_neg", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    with st.spinner("Chargement..."):
        if 'stock_data' not in locals() or not stock_data:
            stock_data = []
            for ticker in MAJOR_STOCKS:
                data = get_stock_data(ticker)
                if data: stock_data.append(data)
        
        df = pd.DataFrame(stock_data)
        if not df.empty:
            df_sorted = df.sort_values('perf_1y', ascending=True).reset_index(drop=True)
            df_sorted.index = df_sorted.index + 1
            
            for idx, row in df_sorted.head(50).iterrows():
                c1, c2, c3, c4, c5 = st.columns([0.3, 1.5, 0.8, 1.2, 1.2])
                with c1: st.markdown(f"**{idx}**")
                with c2: 
                    st.markdown(f"**{row['ticker']}**")
                    st.caption(row['name'][:25])
                with c3: st.markdown(f"${row['price']:.2f}")
                with c4: st.markdown(format_large_number(row['market_cap']))
                with c5: st.markdown(f'<span style="color: #FF4B4B; font-weight: bold;">▼ {abs(row["perf_1y"]):.1f}%</span>', unsafe_allow_html=True)
                st.divider()

# ---------------------------------------------------------
# PIED DE PAGE ET STYLES CSS
# ---------------------------------------------------------
st.markdown("---")
col_left_f, col_center_f, col_right_f = st.columns([1, 4, 1])
with col_center_f:
    st.markdown("<div style='text-align: center; font-size: small;'><span style='margin: 0 50px;'>📈 Analyseur d'Actions Boursières v1.0</span><span style='margin: 0 50px;'>⚠️ Pas un conseil financier</span><span style='margin: 0 50px;'>Créé par @Mathieugird</span></div>", unsafe_allow_html=True)

st.markdown("""
<style>
    .main { padding-top: 2rem; }
    div[data-testid="column"] button[kind="secondary"] {
        background-color: #f0f2f6 !important; color: #31333F !important;
        border: 1px solid #e0e0e0 !important; font-size: 0.45em !important;
        padding: 1px 2px !important; min-height: 16px !important; line-height: 1 !important;
    }
    div[data-testid="column"] button[kind="primary"] {
        background-color: #1f77b4 !important; color: white !important;
        border: 1px solid #1f77b4 !important; font-size: 0.45em !important;
        padding: 1px 2px !important; min-height: 16px !important; line-height: 1 !important;
    }
    div[data-testid="metric-container"] { text-align: center !important; }
    div[data-testid="metric-container"] > div { justify-content: center !important; }
    .stDivider { margin: 0.2rem 0 !important; }
</style>
""", unsafe_allow_html=True)
