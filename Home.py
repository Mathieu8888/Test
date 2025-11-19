import streamlit as st
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from Algorithmev1 import StockScorer
from smart_search import smart_search, extract_ticker

# Importer streamlit-searchbox pour l'autocompletion
try:
    from streamlit_searchbox import st_searchbox
    SEARCHBOX_AVAILABLE = True
except ImportError:
    SEARCHBOX_AVAILABLE = False
    st.warning("⚠️ Pour une meilleure expérience : `pip install streamlit-searchbox`")

st.set_page_config(page_title="Analyseur Actions Boursières", page_icon="📈", layout="wide")

# Navigation sidebar
st.sidebar.title("📊 Navigation")
st.sidebar.info("🏠 Page d'Analyse Individuelle")

st.title("📈 Analyseur d'Actions Boursières")

st.header("🔍 Démarrez l'Analyse")

col_left_pad, col_center_content, col_right_pad = st.columns([1, 4, 1])

with col_center_content:
    
    if SEARCHBOX_AVAILABLE:
        # VERSION AVEC AUTOCOMPLETION GOOGLE-LIKE
        
        def search_function(query: str):
            """Fonction de recherche pour l'autocompletion"""
            if not query or len(query) < 1:
                # Suggestions par défaut
                return [
                    "AAPL - Apple Inc.",
                    "GOOGL - Alphabet Inc. (Google)",
                    "MSFT - Microsoft Corporation",
                    "NVDA - NVIDIA Corporation",
                    "TSLA - Tesla Inc."
                ]
            
            # Recherche avec le système hybride
            results = smart_search(query, limit=8)
            return results if results else []
        
        # BARRE DE RECHERCHE AVEC DROPDOWN INTÉGRÉ (comme Google)
        selected_company = st_searchbox(
            search_function,
            placeholder="🔍 Tapez : Ferrari, Nintendo, Apple, Samsung...",
            label="Rechercher une entreprise",
            key="company_searchbox",
            clear_on_submit=False,
            rerun_on_update=False
        )
        
        # Extraire le ticker
        if selected_company:
            company = extract_ticker(selected_company)
        else:
            company = ""
    
    else:
        # VERSION FALLBACK (si streamlit-searchbox pas installé)
        st.markdown("**Rechercher une entreprise**")
        
        search_input = st.text_input(
            "Entreprise ou Ticker",
            placeholder="Tapez : Ferrari, Nintendo, Apple, Samsung, RACE, NTDOY...",
            key="fallback_search",
            label_visibility="collapsed"
        )
        
        # Suggestions en boutons
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
- Score = Performance ajustée sur une échelle de 0 à 10
- Plus la performance est élevée, meilleur est le score
- **Prix actuel** : ${info.get('currentPrice', 'N/A')}
- **Plus haut 52 sem** : ${info.get('fiftyTwoWeekHigh', 'N/A')}
- **Plus bas 52 sem** : ${info.get('fiftyTwoWeekLow', 'N/A')}

**Barèmes :**
- Performance > +30% → Score 9-10
- Performance +15% à +30% → Score 7-8
- Performance 0% à +15% → Score 5-6
- Performance négative → Score 0-4
""",
        "Momentum 3M": f"""
**Calcul du Momentum sur 3 mois**
- Performance calculée sur les 3 derniers mois
- Score = Performance ajustée sur une échelle de 0 à 10
- Utile pour détecter les tendances court terme
- **Prix actuel** : ${info.get('currentPrice', 'N/A')}

**Barèmes :**
- Performance > +20% → Score 9-10
- Performance +10% à +20% → Score 7-8
- Performance 0% à +10% → Score 5-6
- Performance négative → Score 0-4
""",
        "RSI": f"""
**Calcul du RSI (Relative Strength Index)**
- Indicateur de momentum qui mesure la vitesse et l'amplitude des mouvements de prix
- Échelle de 0 à 100
- **RSI actuel** : {format_number(info.get('rsi', 'N/A'))}

**Interprétation :**
- RSI > 70 → Surachat (possible correction à la baisse)
- RSI 30-70 → Zone neutre
- RSI < 30 → Survente (possible rebond)

**Barèmes :**
- RSI 40-60 (neutre) → Score 8-10
- RSI 30-40 ou 60-70 → Score 5-7
- RSI < 30 ou > 70 (extrême) → Score 0-4
""",
        "Volatilité": f"""
**Calcul de la Volatilité**
- Mesure la dispersion des rendements d'un actif
- Calculée comme l'écart-type des rendements quotidiens sur 30 jours
- **Bêta** : {format_number(info.get('beta', 'N/A'))} (par rapport au marché)

**Interprétation :**
- Volatilité faible → Action stable, moins risquée
- Volatilité élevée → Action risquée, mouvements importants

**Barèmes :**
- Volatilité < 20% → Score 9-10 (très stable)
- Volatilité 20-40% → Score 6-8 (normale)
- Volatilité > 40% → Score 0-5 (très volatile)
""",
        "Volume": f"""
**Calcul du Volume moyen**
- Volume moyen sur 10 jours : {format_number(info.get('averageVolume10days', 'N/A'))}
- Volume moyen sur 3 mois : {format_number(info.get('averageVolume', 'N/A'))}

**Interprétation :**
- Volume élevé → Bonne liquidité, facile à acheter/vendre
- Volume faible → Liquidité limitée, spread plus large

**Barèmes :**
- Volume > 1M actions/jour → Score 9-10
- Volume 100K-1M → Score 6-8
- Volume < 100K → Score 0-5
""",
        "P/E Ratio": f"""
**Calcul du Price-to-Earnings Ratio**
- P/E = Prix de l'action / Bénéfice par action
- **P/E actuel** : {format_number(info.get('trailingPE', info.get('forwardPE', 'N/A')))}
- **P/E sectoriel** : {format_number(info.get('sectorPE', 'N/A'))}

**Interprétation :**
- P/E faible → Action potentiellement sous-évaluée
- P/E élevé → Action chère ou forte croissance attendue

**Barèmes :**
- P/E < 15 → Score 9-10 (sous-évalué)
- P/E 15-25 → Score 5-8 (raisonnable)
- P/E > 25 → Score 0-4 (cher)
""",
        "P/B Ratio": f"""
**Calcul du Price-to-Book Ratio**
- P/B = Prix de l'action / Valeur comptable par action
- **P/B actuel** : {format_number(info.get('priceToBook', 'N/A'))}

**Interprétation :**
- P/B < 1 → Action se négocie en dessous de sa valeur comptable
- P/B > 3 → Action valorisée bien au-dessus de ses actifs

**Barèmes :**
- P/B < 1 → Score 9-10
- P/B 1-3 → Score 5-8
- P/B > 3 → Score 0-4
""",
        "ROE": f"""
**Calcul du Return on Equity**
- ROE = Bénéfice net / Capitaux propres
- **ROE actuel** : {format_percentage(info.get('returnOnEquity', 'N/A'))}

**Interprétation :**
- Mesure l'efficacité avec laquelle l'entreprise génère des profits
- ROE élevé → Entreprise efficace dans l'utilisation de ses capitaux

**Barèmes :**
- ROE > 20% → Score 9-10 (excellent)
- ROE 10-20% → Score 6-8 (bon)
- ROE < 10% → Score 0-5 (faible)
""",
        "Marge Opérationnelle": f"""
**Calcul de la Marge Opérationnelle**
- Marge = Résultat opérationnel / Chiffre d'affaires
- **Marge actuelle** : {format_percentage(info.get('operatingMargins', 'N/A'))}

**Interprétation :**
- Mesure la rentabilité des opérations de l'entreprise
- Marge élevée → Entreprise efficace, bon pouvoir de fixation des prix

**Barèmes :**
- Marge > 20% → Score 9-10
- Marge 10-20% → Score 6-8
- Marge < 10% → Score 0-5
""",
        "Croissance CA": f"""
**Calcul de la Croissance du Chiffre d'Affaires**
- Croissance année sur année
- **Croissance trimestrielle** : {format_percentage(info.get('revenueGrowth', 'N/A'))}

**Interprétation :**
- Croissance positive → Entreprise en expansion
- Croissance élevée → Fort potentiel mais parfois plus risqué

**Barèmes :**
- Croissance > 20% → Score 9-10
- Croissance 5-20% → Score 6-8
- Croissance < 5% → Score 0-5
""",
        "Dette/Equity": f"""
**Calcul du Ratio Dette/Capitaux Propres**
- Dette/Equity = Dette totale / Capitaux propres
- **Ratio actuel** : {format_number(info.get('debtToEquity', 'N/A'))}

**Interprétation :**
- Mesure le levier financier de l'entreprise
- Ratio faible → Entreprise peu endettée, plus sûre
- Ratio élevé → Risque financier plus important

**Barèmes :**
- Dette/Equity < 0.5 → Score 9-10
- Dette/Equity 0.5-1.5 → Score 6-8
- Dette/Equity > 1.5 → Score 0-5
""",
        "Current Ratio": f"""
**Calcul du Current Ratio (Ratio de Liquidité)**
- Current Ratio = Actifs courants / Passifs courants
- **Ratio actuel** : {format_number(info.get('currentRatio', 'N/A'))}

**Interprétation :**
- Mesure la capacité à payer les dettes à court terme
- Ratio > 1 → Entreprise peut couvrir ses obligations

**Barèmes :**
- Current Ratio > 2 → Score 9-10
- Current Ratio 1-2 → Score 6-8
- Current Ratio < 1 → Score 0-5
""",
        "Dividende": f"""
**Analyse du Dividende**
- **Rendement** : {format_percentage(info.get('dividendYield', 'N/A'))}
- **Taux de distribution** : {format_percentage(info.get('payoutRatio', 'N/A'))}

**Interprétation :**
- Rendement élevé → Revenu passif attractif
- Taux de distribution < 60% → Dividende soutenable

**Barèmes :**
- Rendement > 4% ET distribution < 60% → Score 9-10
- Rendement 2-4% → Score 6-8
- Rendement < 2% ou pas de dividende → Score 0-5
""",
    }
    
    return details.get(indicator_name, "Détails non disponibles pour cet indicateur")

if analyze and company:
    with st.spinner(f"🔄 Analyse de {company} en cours..."):
        try:
            final = StockScorer(company)
            results = final.calculate_scores(h_code)
            
            if results['global_score'] == 0:
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
                    st.markdown(f"**Site web** : [{info.get('website', 'N/A')}]({info.get('website', '#')})")
                
                st.markdown("---")
                
                col1, col2, col3 = st.columns(3)
                
                score = results['global_score']
                
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
                
                for idx, (indicator, score_val) in enumerate(results['scores'].items()):
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
                        
                        with st.expander("ℹ️ Détails du calcul", expanded=False):
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
                                <div style='text-align: center; padding: 15px; background-color: #f0f2f6; border-radius: 8px; margin-bottom: 10px;'>
                                    <p style='margin: 0; font-size: 14px; color: #666;'>{metric_name}</p>
                                    <h3 style='margin: 10px 0;'>{value:.2f}</h3>
                                    <p style='margin: 0; font-size: 14px;'>{status}</p>
                                </div>
                            """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                st.subheader("📈 Évolution du Prix")
                
                with st.container():
                    period_options = [
                        ("1S", "1wk"),
                        ("1M", "1mo"),
                        ("3M", "3mo"),
                        ("6M", "6mo"),
                        ("1A", "1y"),
                        ("YTD", "ytd"),
                        ("5A", "5y"),
                        ("MAX", "max")
                    ]
                    
                    if 'selected_period_key' not in st.session_state:
                        st.session_state.selected_period_key = "1A"
                    
                    # Créer les boutons de période alignés beaucoup plus à droite avec largeurs égales
                    col_spacer, col_buttons = st.columns([2, 2])
                    
                    with col_buttons:
                        # Utiliser des largeurs égales pour tous les boutons (1, 1, 1...)
                        cols = st.columns([0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
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
                    
                    # Convertir la liste en dict pour la suite
                    period_options_dict = dict(period_options)
                    selected_period = period_options_dict[st.session_state.selected_period_key]
                    selected_period_label = st.session_state.selected_period_key
                    
                    try:
                        import plotly.graph_objects as go
                        from datetime import datetime, timedelta
                        
                        hist = final.stock.history(period=selected_period)
                        
                        if not hist.empty:
                            
                            # Calcul de la performance sur la période sélectionnée
                            perf_period = ((hist['Close'][-1] - hist['Close'][0]) / hist['Close'][0]) * 100 if len(hist) > 0 else 0
                            
                            if perf_period > 0:
                                plot_color = '#00CC00' 
                                fill_color = 'rgba(0, 204, 0, 0.1)'
                            else:
                                plot_color = '#FF4B4B'  
                                fill_color = 'rgba(255, 75, 75, 0.1)'
                            
                            # Calcul de la plage de prix pour un meilleur zoom
                            price_min = hist['Close'].min()
                            price_max = hist['Close'].max()
                            price_range = price_max - price_min
                            
                            # Ajouter une marge de 5% en haut et en bas pour mieux voir
                            y_min = price_min - (price_range * 0.05)
                            y_max = price_max + (price_range * 0.05)
                            
                            fig = go.Figure()
                            
                            # Ligne de base pour le remplissage (prix minimum de la période)
                            fig.add_trace(go.Scatter(
                                x=hist.index,
                                y=[y_min] * len(hist),
                                mode='lines',
                                line=dict(width=0),
                                showlegend=False,
                                hoverinfo='skip'
                            ))
                            
                            # Ligne de prix avec remplissage
                            fig.add_trace(go.Scatter(
                                x=hist.index,
                                y=hist['Close'],
                                mode='lines',
                                name='Prix de clôture',
                                line=dict(color=plot_color, width=2.5),
                                fill='tonexty',
                                fillcolor=fill_color
                            ))
                            
                            
                            fig.update_layout(
                                xaxis_title="Date",
                                yaxis_title="Prix ($)",
                                hovermode='x unified',
                                height=400,
                                showlegend=False,
                                margin=dict(l=0, r=0, t=30, b=0),
                                yaxis=dict(
                                    hoverformat='$.2f',
                                    range=[y_min, y_max]  # Zoom sur la vraie plage de prix
                                )
                            )
                            
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}) 
                            
                            # Affichage des métriques de performance (centrées sur la même ligne avec espacement égal
                            
                            # Mapping des labels pour l'affichage
                            period_display_names = {
                                "1S": "1 semaine",
                                "1M": "1 mois",
                                "3M": "3 mois",
                                "6M": "6 mois",
                                "1A": "1 an",
                                "YTD": "YTD",
                                "5A": "5 ans",
                                "MAX": "Max"
                            }
                            
                            display_period_name = period_display_names.get(selected_period_label, selected_period_label)
                            
                            # Créer les colonnes avec espacement uniforme centré
                            col_left_spacer, col_metrics, col_right_spacer = st.columns([0.5, 4, 0.5])
                            
                            with col_metrics:
                                cols = st.columns(5)
                                
                        else:
                            st.info("Historique de prix non disponible")
                    except Exception as e:
                        st.warning("Impossible de charger l'historique de prix")
                    
                    st.markdown("---")
                    
                    st.warning("⚠️ **Avertissement :** Cet outil est une aide à la décision automatisée et ne constitue pas un conseil d'investissement personnel. Consultez un professionnel.")
                    
        except Exception as e:
            st.error(f"Une erreur inattendue s'est produite : {e}")

st.markdown("---")

col_left_f, col_center_f, col_right_f = st.columns([1, 4, 1])

with col_center_f:
    st.markdown("""
        <div style='text-align: center; font-size: small;'>
            <span style='margin: 0 50px;'>📈 Analyseur d'Actions Boursières v1.0</span>
            <span style='margin: 0 50px;'>⚠️ Pas un conseil financier - Outil éducatif</span>
            <span style='margin: 0 50px;'>Créé par @Mathieugird</span>
    
        </div>
        """, unsafe_allow_html=True)


st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    
    /* Styling pour les boutons de période - version ultra mini */
    div[data-testid="column"] button[kind="secondary"] {
        background-color: #f0f2f6 !important;
        color: #31333F !important;
        border: 1px solid #e0e0e0 !important;
        font-weight: 500 !important;
        font-size: 0.45em !important;
        padding: 1px 2px !important;
        min-height: 16px !important;
        max-height: 16px !important;
        line-height: 1 !important;
        transition: all 0.2s ease !important;
    }
    
    div[data-testid="column"] button[kind="secondary"]:hover {
        background-color: #e8eaf0 !important;
        border-color: #1f77b4 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1) !important;
    }
    
    div[data-testid="column"] button[kind="primary"] {
        background-color: #1f77b4 !important;
        color: white !important;
        border: 1px solid #1f77b4 !important;
        font-weight: 600 !important;
        font-size: 0.45em !important;
        padding: 1px 2px !important;
        min-height: 16px !important;
        max-height: 16px !important;
        line-height: 1 !important;
        box-shadow: 0 1px 3px rgba(31, 119, 180, 0.3) !important;
    }
    
    div[data-testid="column"] button {
        border-radius: 3px !important;
    }
    
    /* Centrer les métriques */
    div[data-testid="metric-container"] {
        text-align: center !important;
    }
    
    div[data-testid="metric-container"] > div {
        justify-content: center !important;
    }
</style>
""", unsafe_allow_html=True)
