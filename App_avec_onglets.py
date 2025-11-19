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

# --- GESTION DE L'ÉTAT ---
if 'selected_stock' not in st.session_state: st.session_state.selected_stock = None
if 'selected_horizon' not in st.session_state: st.session_state.selected_horizon = 'long'
if 'origin' not in st.session_state: st.session_state.origin = None

def reset_app():
    st.session_state.selected_stock = None
    st.session_state.origin = None
    st.rerun()

# --- EN-TÊTE ---
st.title("📈 Analyseur d'Actions Boursières")

# ---------------------------------------------------------
# DONNÉES ET UTILITAIRES
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
        
        perf_1d = ((hist['Close'][-1] - hist['Close'][-2]) / hist['Close'][-2] * 100) if len(hist) >= 2 else 0
        perf_7d = ((hist['Close'][-1] - hist['Close'][-6]) / hist['Close'][-6] * 100) if len(hist) >= 6 else 0
        perf_30d = ((hist['Close'][-1] - hist['Close'][-22]) / hist['Close'][-22] * 100) if len(hist) >= 22 else 0
        perf_1y = info.get('52WeekChange', 0) * 100
        
        return {
            'ticker': ticker, 'name': info.get('longName', ticker), 'price': current_price,
            'market_cap': market_cap, 'perf_1d': perf_1d, 'perf_7d': perf_7d,
            'perf_30d': perf_30d, 'perf_1y': perf_1y
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

def get_calculation_details(scorer, indicator_name, score_val):
    info = scorer.info
    def fmt_pct(v): 
        try: return f"{float(v)*100:.2f}%" if v is not None else "N/A"
        except: return "N/A"
    def fmt_num(v):
        try: return f"{float(v):,.2f}" if v is not None else "N/A"
        except: return "N/A"

    base_details = {
        "Momentum 6M": f"**Momentum 6 Mois ({score_val:.1f}/10)**\n- Prix actuel : ${info.get('currentPrice', 'N/A')}\n- Plus haut 52s : ${info.get('fiftyTwoWeekHigh', 'N/A')}",
        "Momentum 3M": f"**Momentum 3 Mois ({score_val:.1f}/10)**\n- Performance récente.\n- Prix actuel : ${info.get('currentPrice', 'N/A')}",
        "RSI": f"**RSI (14 jours) ({score_val:.1f}/10)**\n- < 30 : Survente (Potentiel achat)\n- > 70 : Surachat (Potentiel vente)",
        "Volume": f"**Volume ({score_val:.1f}/10)**\n- Volume moyen : {fmt_num(info.get('averageVolume'))}",
        "P/E Ratio": f"**Price to Earnings (PER) ({score_val:.1f}/10)**\n- Ratio actuel : {fmt_num(info.get('trailingPE') or info.get('forwardPE'))}\n- < 15 : Souvent sous-évalué",
        "PEG Ratio": f"**PEG Ratio ({score_val:.1f}/10)**\n- Ratio actuel : {fmt_num(info.get('pegRatio'))}\n- < 1 : Sous-évalué par rapport à la croissance",
        "Croissance CA": f"**Croissance Chiffre d'Affaires ({score_val:.1f}/10)**\n- Taux : {fmt_pct(info.get('revenueGrowth'))}",
        "Marges": f"**Marge Nette ({score_val:.1f}/10)**\n- Taux : {fmt_pct(info.get('profitMargins'))}",
        "Marge Opé": f"**Marge Opérationnelle ({score_val:.1f}/10)**\n- Taux : {fmt_pct(info.get('operatingMargins'))}",
        "ROE": f"**Return on Equity (ROE) ({score_val:.1f}/10)**\n- Taux : {fmt_pct(info.get('returnOnEquity'))}",
        "ROA": f"**Return on Assets (ROA) ({score_val:.1f}/10)**\n- Taux : {fmt_pct(info.get('returnOnAssets'))}",
        "Dette/Capitaux": f"**Dette / Capitaux Propres ({score_val:.1f}/10)**\n- Ratio : {fmt_num(info.get('debtToEquity'))}",
        "Free Cash Flow": f"**Free Cash Flow ({score_val:.1f}/10)**\n- Montant : ${fmt_num(info.get('freeCashflow'))}",
        "Beta": f"**Beta (Volatilité) ({score_val:.1f}/10)**\n- Beta : {fmt_num(info.get('beta'))}",
        "Liquidité": f"**Current Ratio ({score_val:.1f}/10)**\n- Ratio : {fmt_num(info.get('currentRatio'))}",
        "Dividende": f"**Rendement du Dividende ({score_val:.1f}/10)**\n- Yield : {fmt_pct(info.get('dividendYield'))}",
        "Price to Book": f"**Price to Book (P/B) ({score_val:.1f}/10)**\n- Ratio : {fmt_num(info.get('priceToBook'))}"
    }
    return base_details.get(indicator_name, "Détails non disponibles.")

# --- PAGE D'ANALYSE ---
def show_analysis_page(company_ticker, horizon_code):
    if st.session_state.origin == 'ranking':
        if st.button("← Retour aux classements", type="secondary"):
            reset_app()
    elif st.session_state.origin == 'search':
        if st.button("🔍 Nouvelle recherche", type="secondary"):
            reset_app()

    with st.spinner(f"Analyse de {company_ticker}..."):
        try:
            scorer = StockScorer(company_ticker, horizon_code)
            if not scorer.fetch_data():
                st.error(f"❌ Ticker '{company_ticker}' introuvable.")
                return

            final = scorer
            score = final.calculate_score()
            info = final.info
            
            st.subheader(f"🏢 **{info.get('longName', company_ticker)}** ({company_ticker})")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Ticker", company_ticker)
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
            
            st.markdown("### 📊 Indicateurs Détaillés")
            for name, val in sorted(final.scores.items(), key=lambda x: x[1], reverse=True):
                e = "🟢" if val >= 7 else "🟡" if val >= 4 else "🔴"
                if val >= 7: color = "#00CC00"
                elif val >= 4: color = "#FFD700"
                else: color = "#FF4B4B"

                with st.expander(f"{e} **{name}**: {val:.1f}/10"):
                    st.markdown(f"""
                        <div style="position: relative; width: 100%; background-color: #e0e0e0; border-radius: 10px; height: 25px; margin-bottom: 10px;">
                            <div style="width: {val*10}%; background-color: {color}; height: 100%; border-radius: 10px;"></div>
                            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: #333; font-weight: bold; font-size: 12px;">
                                {val:.1f}/10
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    st.markdown(get_calculation_details(final, name, val))
            
            st.markdown("---")

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
            
            col_title, col_btns_spacer, col_btns = st.columns([1.5, 3.5, 3])
            with col_title:
                st.markdown("### 📈 Évolution Prix")
            
            per_opts = [("1S","5d"),("1M","1mo"),("3M","3mo"),("6M","6mo"),("1A","1y"),("5A","5y"), ("MAX", "max")]
            if 'sel_per' not in st.session_state: st.session_state.sel_per = "1A"
            
            with col_btns:
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
                fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], mode='lines', line=dict(color=line_col, width=2), fill='tozeroy', fillcolor=fill_col))
                fig.update_layout(height=400, margin=dict(l=0,r=0,t=10,b=0), showlegend=False, yaxis=dict(range=y_range))
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        except Exception as e:
            st.error(f"Erreur: {e}")

# ---------------------------------------------------------
# FONCTION D'AFFICHAGE LIGNE
# ---------------------------------------------------------
def display_row(rank, ticker, name, price, mcap, p1d, p7d, p30d, p1y, is_header=False, list_suffix=""):
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
        
        if cols[1].button(ticker, key=f"btn_{ticker}_{rank}_{list_suffix}"):
            st.session_state.selected_stock = ticker
            st.session_state.origin = 'ranking'
            st.rerun()
            
        cols[2].markdown(f"<span class='row-text' style='color:#555;'>{name[:20]}</span>", unsafe_allow_html=True)
        cols[3].markdown(f"<span class='row-text'>${price:.2f}</span>", unsafe_allow_html=True)
        cols[4].markdown(f"<span class='row-text'>{format_large_number(mcap)}</span>", unsafe_allow_html=True)
        cols[5].markdown(f"<span class='row-text'>{format_percentage(p1d)}</span>", unsafe_allow_html=True)
        cols[6].markdown(f"<span class='row-text'>{format_percentage(p7d)}</span>", unsafe_allow_html=True)
        cols[7].markdown(f"<span class='row-text'>{format_percentage(p30d)}</span>", unsafe_allow_html=True)
        cols[8].markdown(f"<span class='row-text'>{format_percentage(p1y)}</span>", unsafe_allow_html=True)
        st.markdown("<hr class='row-divider'>", unsafe_allow_html=True)

def render_ranking(sort_col, ascending, list_name):
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
            display_row(0,0,0,0,0,0,0,0,0, is_header=True, list_suffix=list_name)
            for i, r in df.head(50).iterrows():
                display_row(i+1, r['ticker'], r['name'], r['price'], r['market_cap'], r['perf_1d'], r['perf_7d'], r['perf_30d'], r['perf_1y'], list_suffix=list_name)

# ============================
# ORCHESTRATION PRINCIPALE
# ============================

if st.session_state.selected_stock:
    show_analysis_page(st.session_state.selected_stock, st.session_state.selected_horizon)
else:
    tab_analyse, tab_top100, tab_perf_pos, tab_perf_neg = st.tabs([
        "🔍 Analyse Complète", "🏆 Top 100", "📈 Top Hausses", "📉 Top Baisses"
    ])

    with tab_analyse:
        # Centrage du titre de recherche avec style
        st.markdown("<h2 style='text-align: center;'>🔍 Démarrez l'Analyse</h2>", unsafe_allow_html=True)
        st.write("") # Espace

        # 1. Centrage du bloc avec des colonnes
        _, c_main, _ = st.columns([1, 6, 1])
        
        with c_main:
            # Pas de bordure Streamlit st.container(border=True) pour éviter le double cadre
            # Seul le form aura une bordure
            with st.form(key='search_form', clear_on_submit=False):
                
                # LIGNE 1: Input Texte (Label visible)
                ticker_input = st.text_input("Ticker de l'action", placeholder="Ex: AAPL, NVIDIA, Total...", help="Entrez le symbole")
                
                st.write("") # Petit espace
                
                # LIGNE 2: Horizon (Gauche) + Bouton (Droite)
                # 50/50 pour que le bouton ait de la place
                c_opt, c_btn = st.columns([1, 1], vertical_alignment="bottom")
                
                with c_opt:
                    horizon = st.radio("Horizon d'investissement", ["Court terme", "Long terme"], index=1, horizontal=True)
                    
                with c_btn:
                    submit_search = st.form_submit_button("🚀 Lancer l'analyse", type="primary", use_container_width=True)
                
                if submit_search and ticker_input:
                    st.session_state.selected_stock = ticker_input.strip().upper()
                    st.session_state.selected_horizon = 'court' if 'Court' in horizon else 'long'
                    st.session_state.origin = 'search'
                    st.rerun()

        st.markdown("---")
        col1, col2 = st.columns([1, 1])
        with col1:
            st.header("ℹ️ Comment ça marche ?")
            st.markdown("""
            **L'Analyseur** évalue la santé financière selon :
            1. 🏢 **Secteur**
            2. ⏰ **Horizon**
            3. 📊 **100+ Indicateurs**
            """)
            ca, cb, cc = st.columns(3)
            ca.success("**70-100**\n\n🟢 Bon")
            cb.warning("**40-70**\n\n🟡 Moyen")
            cc.error("**0-40**\n\n🔴 Éviter")
        with col2:
            st.header("💡 Exemples")
            st.info("🍎 **AAPL** (Apple)")
            st.info("⚡ **TSLA** (Tesla)")
            st.info("🛢️ **TTE** (TotalEnergies)")
            st.info("🏦 **JPM** (JPMorgan)")
        
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        c1.metric("📊 Indicateurs", "100+")
        c2.metric("🌍 Couverture", "Global")
        c3.metric("⚡ Vitesse", "< 5 sec")

    with tab_top100: render_ranking('market_cap', False, "top100")
    with tab_perf_pos: render_ranking('perf_1y', False, "gainers")
    with tab_perf_neg: render_ranking('perf_1y', True, "losers")

# ---------------------------------------------------------
# CSS
# ---------------------------------------------------------
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .row-text { font-size: 15px; line-height: 1.6; vertical-align: middle; margin: 0; padding: 0; }
    div[data-testid="column"] { padding: 0px 5px !important; margin: 0px !important;}
    .row-divider { margin-top: 8px !important; margin-bottom: 8px !important; border-top: 1px solid #f0f0f0; }
    
    /* Bouton Analyse GRAS et GRAND */
    div[data-testid="stFormSubmitButton"] > button { 
        height: 45px !important;
        width: 100% !important;
        font-size: 18px !important;
        font-weight: bold !important;
    }

    /* Autres boutons standards */
    div[data-testid="stColumn"] button:not([kind="primary"]) { 
        padding: 0px 8px !important;
        font-size: 0.75em !important; 
        min-height: 1.5em !important;
        line-height: 1.2 !important;
        border-radius: 15px !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
    }
    
    h3 { margin-top: 1.5rem; margin-bottom: 0.5rem; }
    h4 { margin-top: 1.2rem; margin-bottom: 0.4rem; }
    
    /* Pour cacher les labels si besoin (non utilisé ici car on veut les labels comme sur l'image) */
    /* label[for^="st-radio"] div[data-testid="stWidgetLabel"] { display: none; } */
</style>
""", unsafe_allow_html=True)
