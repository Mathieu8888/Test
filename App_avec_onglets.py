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
        # On récupère un peu plus d'historique pour avoir le 1 mois et 1 semaine
        hist = stock.history(period="3mo")
        
        if hist.empty or not info:
            return None
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or (hist['Close'][-1] if not hist.empty else None)
        market_cap = info.get('marketCap', 0)
        
        if market_cap and (market_cap < 1_000_000 or market_cap > 10_000_000_000_000):
            return None
        if not current_price or current_price <= 0 or current_price > 100000:
            return None
        
        # Calculs de performance
        # 24h
        perf_1d = ((hist['Close'][-1] - hist['Close'][-2]) / hist['Close'][-2] * 100) if len(hist) >= 2 else 0
        # 1 Semaine (approx 5 jours de trading)
        perf_7d = ((hist['Close'][-1] - hist['Close'][-6]) / hist['Close'][-6] * 100) if len(hist) >= 6 else 0
        # 1 Mois (approx 21 jours de trading)
        perf_30d = ((hist['Close'][-1] - hist['Close'][-22]) / hist['Close'][-22] * 100) if len(hist) >= 22 else 0
        # 1 An (nécessite download plus long, on approxime ou on fait une requête séparée si besoin, ici on garde simple)
        # Pour le tableau 1 an, on va utiliser une valeur stockée ou faire une requête 1y si nécessaire, 
        # mais pour optimiser on peut utiliser le '52WeekChange' de info s'il existe, sinon 0
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
    except:
        return None

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
# FONCTIONS D'ANALYSE (TAB 1 - RESTAURÉES)
# ---------------------------------------------------------
def get_valuation_analysis(info):
    """Analyse la valorisation de l'entreprise (sur/sous-évaluée)"""
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
    
    if not signals:
        return None, "⚠️ Données insuffisantes pour l'analyse de valorisation"
    
    green_count = sum(1 for s in signals if "🟢" in s[2])
    red_count = sum(1 for s in signals if "🔴" in s[2])
    
    if green_count > red_count: verdict = "🟢 **SOUS-ÉVALUÉE** - L'action semble attractive par rapport à ses fondamentaux"
    elif red_count > green_count: verdict = "🔴 **SURÉVALUÉE** - L'action semble chère par rapport à ses fondamentaux"
    else: verdict = "🟡 **VALORISATION ÉQUILIBRÉE** - L'action est valorisée à un niveau raisonnable"
    
    return signals, verdict

def get_calculation_details(scorer, indicator_name):
    """Retourne les détails de calcul pour chaque indicateur"""
    info = scorer.info
    
    def format_percentage_val(value):
        if value is None or value == 'N/A': return 'N/A'
        try: return f"{float(value) * 100:.2f}%" if abs(float(value)) < 1 else f"{float(value):.2f}%"
        except: return str(value)
    
    def format_number_val(value):
        if value is None or value == 'N/A': return 'N/A'
        try: return f"{float(value):,.2f}"
        except: return str(value)
    
    # Dictionnaire simplifié pour l'exemple, peut être étendu comme dans le code original
    details = {
        "Momentum 6M": f"**Calcul du Momentum sur 6 mois**\n- Prix actuel : ${info.get('currentPrice', 'N/A')}\n- Plus haut 52s : ${info.get('fiftyTwoWeekHigh', 'N/A')}\n- Plus bas 52s : ${info.get('fiftyTwoWeekLow', 'N/A')}",
        "Momentum 3M": f"**Calcul du Momentum sur 3 mois**\n- Prix actuel : ${info.get('currentPrice', 'N/A')}",
        "RSI": "**Relative Strength Index (14 jours)**\n- < 30 : Zone de survente (achat)\n- > 70 : Zone de surachat (vente)",
        "P/E Ratio": f"**Price to Earnings**\n- Ratio actuel : {format_number_val(info.get('trailingPE') or info.get('forwardPE'))}",
        "PEG Ratio": f"**Price/Earnings to Growth**\n- Ratio actuel : {format_number_val(info.get('pegRatio'))}",
        "Croissance CA": f"**Croissance Chiffre d'Affaires**\n- Taux : {format_percentage_val(info.get('revenueGrowth'))}",
        "Marges": f"**Marge Nette**\n- Taux : {format_percentage_val(info.get('profitMargins'))}",
        "Marge Opé": f"**Marge Opérationnelle**\n- Taux : {format_percentage_val(info.get('operatingMargins'))}",
        "ROE": f"**Return on Equity**\n- Taux : {format_percentage_val(info.get('returnOnEquity'))}",
        "Dette/Capitaux": f"**Dette / Capitaux Propres**\n- Ratio : {format_number_val(info.get('debtToEquity'))}",
        "Free Cash Flow": f"**Free Cash Flow**\n- Montant : ${format_number_val(info.get('freeCashflow'))}",
        "Beta": f"**Beta (Volatilité)**\n- Beta : {format_number_val(info.get('beta'))}",
        "Liquidité": f"**Current Ratio**\n- Ratio : {format_number_val(info.get('currentRatio'))}",
        "Dividende": f"**Rendement Dividende**\n- Taux : {format_percentage_val(info.get('dividendYield'))}",
        "Price to Book": f"**Price to Book**\n- Ratio : {format_number_val(info.get('priceToBook'))}"
    }
    
    return details.get(indicator_name, "Détails non disponibles pour cet indicateur.")

# ---------------------------------------------------------
# INTERFACE UTILISATEUR
# ---------------------------------------------------------

tab_analyse, tab_top100, tab_perf_pos, tab_perf_neg = st.tabs([
    "🔍 Analyse Complète",
    "🏆 Top 100", 
    "📈 Top Hausses",
    "📉 Top Baisses"
])

# =========================================================
# TAB 1: ANALYSE (RESTAURATION COMPLÈTE)
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

    # --- ÉCRAN D'ACCUEIL (Si pas de recherche) ---
    if not company:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.header("ℹ️ Comment ça marche ?")
            st.markdown("""
            **L'Analyseur d'Actions Boursières** évalue automatiquement la santé financière 
            et le potentiel d'une entreprise selon :
            
            1. 🏢 **Son secteur d'activité** (Tech, Finance, Énergie...)
            2. ⏰ **Votre horizon d'investissement** (Court ou Long terme)
            3. 📊 **Plus de 100 indicateurs financiers** adaptés
            
            ### 🎯 Échelle de notation
            """)
            
            # Code couleur de la notation (Comme screenshot 1)
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.success("**70-100**\n\n🟢 Bon")
            with col_b:
                st.warning("**40-70**\n\n🟡 Moyen")
            with col_c:
                st.error("**0-40**\n\n🔴 Éviter")
        
        with col2:
            st.header("💡 Exemples d'actions")
            st.markdown("Testez avec ces entreprises populaires :")
            
            # Liste d'exemples (Comme screenshot 1)
            st.info("🍎 **Apple (AAPL)** - Tech géant, forte croissance")
            st.info("🥤 **Coca-Cola (KO)** - Dividendes stables, défensif")
            st.info("⚡ **Tesla (TSLA)** - Croissance aggressive, volatil")
            st.info("💊 **Johnson & Johnson (JNJ)** - Santé, dividendes élevés")
            st.info("🛢️ **TotalEnergies (TTE)** - Énergie, bons dividendes")
            st.info("🏦 **JPMorgan (JPM)** - Finance, solide")
        
        st.markdown("---")
        
        # Métriques du bas (Comme screenshot 1)
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            st.metric("📊 Indicateurs analysés", "100+", help="Adapté selon le secteur et l'horizon")
        with col_stat2:
            st.metric("🌍 Marchés couverts", "Global", help="Actions US, Europe, Asie...")
        with col_stat3:
            st.metric("⚡ Temps d'analyse", "< 5 sec", help="Résultats quasi instantanés")

    # --- RÉSULTATS DE L'ANALYSE (Si recherche) ---
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
                        st.error("❌ Impossible de calculer le score (données financières manquantes ou invalides).")
                    else:
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
                            st.markdown("**Conclusion :** L'entreprise montre une **forte santé financière** et de bonnes perspectives sur cet horizon.")
                        elif score >= 40:
                            st.warning(f"## 🟡 {score}/100 - RECOMMANDATION : PRUDENCE")
                            st.markdown("**Conclusion :** L'entreprise présente des **forces et faiblesses**. Une analyse approfondie est requise.")
                        else:
                            st.error(f"## 🔴 {score}/100 - RECOMMANDATION : ÉVITER")
                            st.markdown("**Conclusion :** L'entreprise affiche des **signes de faiblesse importants**. Investissement non recommandé.")
                        
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
                        
                        # TOILE D'ARAIGNÉE (RADAR CHART)
                        st.markdown("### 🎯 Vue d'ensemble des Performances")
                        
                        col_radar, col_top = st.columns([2, 1])
                        
                        with col_radar:
                            categories = list(final.scores.keys())
                            values = list(final.scores.values())
                            
                            fig = go.Figure()
                            fig.add_trace(go.Scatterpolar(
                                r=values, theta=categories, fill='toself', name='Scores',
                                line=dict(color='#FF4B4B', width=2), fillcolor='rgba(255, 75, 75, 0.3)'
                            ))
                            fig.add_trace(go.Scatterpolar(
                                r=[7] * len(categories), theta=categories, name='Seuil Bon (7/10)',
                                line=dict(color='#00CC00', width=2, dash='dash'), showlegend=True
                            ))
                            fig.update_layout(
                                polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
                                showlegend=True, height=450, margin=dict(l=80, r=80, t=20, b=20)
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col_top:
                            st.markdown("#### 💪 Top 3 Forces")
                            forces = [(name, val) for name, val in final.scores.items() if val >= 7]
                            top_forces = sorted(forces, key=lambda x: x[1], reverse=True)[:3]
                            if top_forces:
                                for i, (name, val) in enumerate(top_forces, 1):
                                    st.success(f"**{i}. {name}**\n\n{val:.1f}/10")
                            else:
                                st.info("Aucune force majeure détectée (score ≥ 7/10)")
                        
                        st.markdown("---")
                        
                        # DÉTAILS DES INDICATEURS (BARRES)
                        st.markdown("### 📊 Indicateurs Détaillés (Performance sur 10)")
                        
                        for name, val in sorted(final.scores.items(), key=lambda x: x[1], reverse=True):
                            e = "🟢" if val >= 7 else "🟡" if val >= 4 else "🔴"
                            bar_color = "#00CC00" if val >= 7 else "#FFD700" if val >= 4 else "#FF4B4B"
                            
                            with st.expander(f"{e} **{name}**: **{val:.2f}**/10"):
                                progress_percent = (val / 10) * 100
                                st.markdown(f"""
                                    <div style="position: relative; background-color: #e0e0e0; border-radius: 10px; height: 25px; margin: 10px 0;">
                                        <div style="background-color: {bar_color}; width: {progress_percent}%; height: 100%; border-radius: 10px;"></div>
                                        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: #333; font-weight: bold; font-size: 12px;">
                                            {val:.1f}/10
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)
                                st.markdown("#### 📋 Détails du calcul")
                                st.markdown(get_calculation_details(final, name))
                        
                        st.markdown("---")
                        
                        # DONNÉES SUPPLÉMENTAIRES
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**📊 Données de Marché**")
                            st.write(f"- **Capitalisation** : ${final.info.get('marketCap', 0):,.0f}")
                            st.write(f"- **Volume moyen** : {final.info.get('averageVolume', 0):,.0f}")
                            st.write(f"- **Plus haut 52 sem** : ${final.info.get('fiftyTwoWeekHigh', 'N/A')}")
                            st.write(f"- **Plus bas 52 sem** : ${final.info.get('fiftyTwoWeekLow', 'N/A')}")
                        with col2:
                            st.markdown("**💼 Ratios Financiers**")
                            pe_ratio = final.info.get('trailingPE') or final.info.get('forwardPE')
                            st.write(f"- **P/E Ratio** : {f'{pe_ratio:.2f}' if pe_ratio else 'N/A'}")
                            st.write(f"- **PEG Ratio** : {final.info.get('pegRatio', 'N/A')}")
                            st.write(f"- **Price to Book** : {final.info.get('priceToBook', 'N/A')}")
                            div_yield = final.info.get('dividendYield')
                            st.write(f"- **Dividend Yield** : {f'{div_yield*100:.2f}%' if div_yield else 'N/A'}")
                        
                        st.markdown("---")
                        
                        # GRAPHIQUE DE PRIX
                        st.markdown("### 📈 Évolution du Prix")
                        
                        # Sélecteur de période
                        period_options = [
                            ("1S", "5d"), ("1M", "1mo"), ("3M", "3mo"), ("6M", "6mo"),
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
                            hist = final.stock.history(period=selected_period)
                            if not hist.empty:
                                perf_period = ((hist['Close'][-1] - hist['Close'][0]) / hist['Close'][0]) * 100 if len(hist) > 0 else 0
                                plot_color = '#00CC00' if perf_period > 0 else '#FF4B4B'
                                fill_color = 'rgba(0, 204, 0, 0.1)' if perf_period > 0 else 'rgba(255, 75, 75, 0.1)'
                                
                                fig = go.Figure()
                                fig.add_trace(go.Scatter(
                                    x=hist.index, y=hist['Close'], mode='lines', name='Prix',
                                    line=dict(color=plot_color, width=2.5), fill='tozeroy', fillcolor=fill_color
                                ))
                                fig.update_layout(
                                    xaxis_title="Date", yaxis_title="Prix ($)", height=400,
                                    showlegend=False, margin=dict(l=0, r=0, t=30, b=0), hovermode='x unified'
                                )
                                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                            else:
                                st.info("Historique de prix non disponible")
                        except Exception as e:
                            st.warning("Impossible de charger l'historique de prix")
                            
            except Exception as e:
                st.error(f"Une erreur inattendue s'est produite : {e}")

# ============================
# FONCTION D'AFFICHAGE LIGNE (PLUS AÉRÉE + COLONNES AJOUTÉES)
# ============================
def display_expanded_row(rank, ticker, name, price, mcap, p1d, p7d, p30d, p1y, is_header=False):
    # Nouvelles colonnes ajoutées: 7j et 30j. Ratio ajusté pour tout faire tenir proprement.
    cols = st.columns([0.4, 0.8, 2, 1, 1.2, 1, 1, 1, 1])
    
    if is_header:
        # En-tête
        cols[0].markdown("**#**")
        cols[1].markdown("**Ticker**")
        cols[2].markdown("**Nom**")
        cols[3].markdown("**Prix**")
        cols[4].markdown("**Cap.**")
        cols[5].markdown("**24h**")
        cols[6].markdown("**1 Sem**") # NOUVEAU
        cols[7].markdown("**1 Mois**") # NOUVEAU
        cols[8].markdown("**1 An**")
        st.markdown("<hr style='margin: 0; padding: 0; border-top: 2px solid #555;'>", unsafe_allow_html=True)
    else:
        # Lignes de données (Plus aérées avec du padding CSS)
        cols[0].markdown(f"<span class='row-text'>**{rank}**</span>", unsafe_allow_html=True)
        cols[1].markdown(f"<span class='row-text'>**{ticker}**</span>", unsafe_allow_html=True)
        cols[2].markdown(f"<span class='row-text' style='color:#555;'>{name[:22]}</span>", unsafe_allow_html=True)
        cols[3].markdown(f"<span class='row-text'>${price:.2f}</span>", unsafe_allow_html=True)
        cols[4].markdown(f"<span class='row-text'>{format_large_number(mcap)}</span>", unsafe_allow_html=True)
        cols[5].markdown(f"<span class='row-text'>{format_percentage(p1d)}</span>", unsafe_allow_html=True)
        cols[6].markdown(f"<span class='row-text'>{format_percentage(p7d)}</span>", unsafe_allow_html=True) # NOUVEAU
        cols[7].markdown(f"<span class='row-text'>{format_percentage(p30d)}</span>", unsafe_allow_html=True) # NOUVEAU
        cols[8].markdown(f"<span class='row-text'>{format_percentage(p1y)}</span>", unsafe_allow_html=True)
        st.markdown("<hr class='row-divider'>", unsafe_allow_html=True)

# ============================
# TAB 2: TOP 100
# ============================
with tab_top100:
    st.caption("Classement par Capitalisation Boursière")
    
    with st.spinner("Chargement des données de marché..."):
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
            display_expanded_row(0,0,0,0,0,0,0,0,0, is_header=True)
            
            # Rows
            for idx, row in df.iterrows():
                display_expanded_row(
                    idx + 1,
                    row['ticker'],
                    row['name'],
                    row['price'],
                    row['market_cap'],
                    row['perf_1d'],
                    row['perf_7d'],
                    row['perf_30d'],
                    row['perf_1y']
                )

# ============================
# TAB 3: TOP HAUSSES
# ============================
with tab_perf_pos:
    st.caption("Meilleures performances sur 1 an")
    if 'stock_data' in locals() and stock_data:
        df = pd.DataFrame(stock_data)
        df = df.sort_values('perf_1y', ascending=False).reset_index(drop=True)
        
        display_expanded_row(0,0,0,0,0,0,0,0,0, is_header=True)
        for idx, row in df.head(50).iterrows():
            display_expanded_row(idx+1, row['ticker'], row['name'], row['price'], row['market_cap'], row['perf_1d'], row['perf_7d'], row['perf_30d'], row['perf_1y'])

# ============================
# TAB 4: TOP BAISSES
# ============================
with tab_perf_neg:
    st.caption("Pires performances sur 1 an")
    if 'stock_data' in locals() and stock_data:
        df = pd.DataFrame(stock_data)
        df = df.sort_values('perf_1y', ascending=True).reset_index(drop=True)
        
        display_expanded_row(0,0,0,0,0,0,0,0,0, is_header=True)
        for idx, row in df.head(50).iterrows():
            display_expanded_row(idx+1, row['ticker'], row['name'], row['price'], row['market_cap'], row['perf_1d'], row['perf_7d'], row['perf_30d'], row['perf_1y'])

# ---------------------------------------------------------
# STYLES CSS (AJUSTÉS POUR PLUS DE MARGE)
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Augmenter un peu l'espace global */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Texte des lignes du tableau : Taille correcte et alignement */
    .row-text {
        font-size: 15px;
        line-height: 1.6; /* Plus aéré */
        vertical-align: middle;
    }
    
    /* Ajouter du padding aux colonnes pour que ce soit moins serré */
    div[data-testid="column"] {
        padding-top: 10px !important;
        padding-bottom: 10px !important;
    }
    
    /* Séparateur fin mais avec de la marge autour */
    .row-divider {
        margin-top: 5px !important;
        margin-bottom: 5px !important;
        border-top: 1px solid #f0f0f0;
    }
    
    /* Style des boutons de période (graphique) */
    div[data-testid="column"] button[kind="secondary"] {
        padding: 2px 5px !important;
        font-size: 0.8em !important;
    }
</style>
""", unsafe_allow_html=True)
