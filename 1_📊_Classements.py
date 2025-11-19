import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="📊 Classements Boursiers", page_icon="📊", layout="wide")

# Navigation sidebar
st.sidebar.title("📊 Navigation")
st.sidebar.success("📊 Page des Classements")

st.title("📊 Classements Boursiers")
st.markdown("*Style CoinMarketCap - Les meilleures actions en temps réel*")

# Liste des principales actions par marché
MAJOR_STOCKS = {
    "🇺🇸 Tech US": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "NFLX", "AMD", "INTC",
                     "ADBE", "CRM", "ORCL", "CSCO", "AVGO", "QCOM", "TXN", "INTU", "NOW", "SNOW"],
    
    "🇺🇸 Finance & Industrie": ["JPM", "BAC", "WFC", "GS", "MS", "V", "MA", "AXP", "C", "BLK",
                                  "UNH", "JNJ", "PFE", "LLY", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY"],
    
    "🇺🇸 Consommation": ["WMT", "HD", "MCD", "NKE", "SBUX", "DIS", "COST", "TGT", "LOW", "TJX",
                          "PG", "KO", "PEP", "PM", "MO", "CL", "KMB", "GIS", "K", "CAG"],
    
    "🇪🇺 Europe": ["ASML", "SAP", "LVMH.PA", "OR.PA", "SAN.PA", "AIR.PA", "MC.PA", "SU.PA", "TTE.PA", "BN.PA",
                    "SIE.DE", "VOW3.DE", "BAS.DE", "ALV.DE", "DTE.DE"],
    
    "🇯🇵 Japon": ["7203.T", "6758.T", "9984.T", "6861.T", "8306.T", "7974.T", "9433.T", "4063.T", "6902.T", "8035.T"],
    
    "🌏 Asie-Pacifique": ["TSM", "BABA", "TCEHY", "005930.KS", "000660.KS", "2330.TW", "1810.HK", "0700.HK"]
}

# Récupérer toutes les actions
ALL_STOCKS = []
for stocks in MAJOR_STOCKS.values():
    ALL_STOCKS.extend(stocks)
ALL_STOCKS = list(set(ALL_STOCKS))  # Supprimer les doublons

@st.cache_data(ttl=300)  # Cache de 5 minutes
def get_stock_data(ticker):
    """Récupère les données d'une action"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")
        
        if hist.empty or not info:
            return None
        
        # Prix actuel
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or (hist['Close'][-1] if not hist.empty else None)
        
        # Calculs de performance
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
        
        # Volume
        volume = hist['Volume'][-1] if not hist.empty else 0
        
        # Capitalisation
        market_cap = info.get('marketCap', 0)
        
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
            'sector': info.get('sector', 'N/A'),
            'pe_ratio': info.get('trailingPE', 0),
            'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
        }
    except Exception as e:
        return None

def format_large_number(num):
    """Formate les grands nombres (Milliards, Millions)"""
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

# Tabs pour différents classements
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Top 100 Capitalisation",
    "📈 Meilleures Performances 1Y",
    "📉 Pires Performances 1Y",
    "💰 Meilleurs Dividendes",
    "🔥 Plus Gros Volumes"
])

with tab1:
    st.subheader("🏆 Top 100 des Actions par Capitalisation Boursière")
    st.markdown("*Les entreprises les plus valorisées au monde*")
    
    if st.button("🔄 Actualiser les données", key="refresh_mcap"):
        st.cache_data.clear()
        st.rerun()
    
    with st.spinner("📊 Chargement des données en cours..."):
        # Récupérer les données
        stock_data = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, ticker in enumerate(ALL_STOCKS[:100]):  # Limiter à 100
            status_text.text(f"Chargement: {ticker} ({idx+1}/{min(100, len(ALL_STOCKS))})")
            data = get_stock_data(ticker)
            if data and data['market_cap'] > 0:
                stock_data.append(data)
            progress_bar.progress((idx + 1) / min(100, len(ALL_STOCKS)))
            time.sleep(0.1)  # Éviter le rate limiting
        
        progress_bar.empty()
        status_text.empty()
        
        # Créer le DataFrame
        df = pd.DataFrame(stock_data)
        df = df.sort_values('market_cap', ascending=False).reset_index(drop=True)
        df.index = df.index + 1  # Commencer à 1
        
        # Affichage du tableau
        st.markdown("---")
        
        # Header du tableau
        col_rank, col_name, col_price, col_mcap, col_1d, col_7d, col_30d, col_1y, col_volume = st.columns([0.5, 2, 1, 1.5, 1, 1, 1, 1, 1.5])
        
        with col_rank:
            st.markdown("**#**")
        with col_name:
            st.markdown("**Nom**")
        with col_price:
            st.markdown("**Prix**")
        with col_mcap:
            st.markdown("**Cap. Boursière**")
        with col_1d:
            st.markdown("**24h**")
        with col_7d:
            st.markdown("**7j**")
        with col_30d:
            st.markdown("**30j**")
        with col_1y:
            st.markdown("**1an**")
        with col_volume:
            st.markdown("**Volume (24h)**")
        
        st.markdown("---")
        
        # Afficher les 100 premières
        for idx, row in df.head(100).iterrows():
            col_rank, col_name, col_price, col_mcap, col_1d, col_7d, col_30d, col_1y, col_volume = st.columns([0.5, 2, 1, 1.5, 1, 1, 1, 1, 1.5])
            
            with col_rank:
                st.markdown(f"**{idx}**")
            
            with col_name:
                st.markdown(f"**{row['ticker']}**")
                st.caption(row['name'][:30] + "..." if len(row['name']) > 30 else row['name'])
            
            with col_price:
                st.markdown(f"${row['price']:.2f}")
            
            with col_mcap:
                st.markdown(format_large_number(row['market_cap']))
            
            with col_1d:
                st.markdown(format_percentage(row['perf_1d']), unsafe_allow_html=True)
            
            with col_7d:
                st.markdown(format_percentage(row['perf_7d']), unsafe_allow_html=True)
            
            with col_30d:
                st.markdown(format_percentage(row['perf_30d']), unsafe_allow_html=True)
            
            with col_1y:
                st.markdown(format_percentage(row['perf_1y']), unsafe_allow_html=True)
            
            with col_volume:
                st.markdown(format_large_number(row['volume']))
            
            st.markdown("---")

with tab2:
    st.subheader("📈 Top 50 Meilleures Performances sur 1 an")
    st.markdown("*Les actions qui ont le plus progressé*")
    
    if st.button("🔄 Actualiser les données", key="refresh_perf_pos"):
        st.cache_data.clear()
        st.rerun()
    
    with st.spinner("📊 Chargement des données..."):
        if 'df' not in locals() or df.empty:
            stock_data = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, ticker in enumerate(ALL_STOCKS):
                status_text.text(f"Chargement: {ticker} ({idx+1}/{len(ALL_STOCKS)})")
                data = get_stock_data(ticker)
                if data:
                    stock_data.append(data)
                progress_bar.progress((idx + 1) / len(ALL_STOCKS))
                time.sleep(0.1)
            
            progress_bar.empty()
            status_text.empty()
            df = pd.DataFrame(stock_data)
        
        df_sorted = df.sort_values('perf_1y', ascending=False).reset_index(drop=True)
        df_sorted.index = df_sorted.index + 1
        
        # Affichage
        st.markdown("---")
        
        col_rank, col_name, col_price, col_mcap, col_1y, col_sector = st.columns([0.5, 2, 1, 1.5, 1.5, 1.5])
        
        with col_rank:
            st.markdown("**#**")
        with col_name:
            st.markdown("**Nom**")
        with col_price:
            st.markdown("**Prix**")
        with col_mcap:
            st.markdown("**Cap. Boursière**")
        with col_1y:
            st.markdown("**Performance 1an**")
        with col_sector:
            st.markdown("**Secteur**")
        
        st.markdown("---")
        
        for idx, row in df_sorted.head(50).iterrows():
            col_rank, col_name, col_price, col_mcap, col_1y, col_sector = st.columns([0.5, 2, 1, 1.5, 1.5, 1.5])
            
            with col_rank:
                if idx == 1:
                    st.markdown("🥇")
                elif idx == 2:
                    st.markdown("🥈")
                elif idx == 3:
                    st.markdown("🥉")
                else:
                    st.markdown(f"**{idx}**")
            
            with col_name:
                st.markdown(f"**{row['ticker']}**")
                st.caption(row['name'][:30] + "..." if len(row['name']) > 30 else row['name'])
            
            with col_price:
                st.markdown(f"${row['price']:.2f}")
            
            with col_mcap:
                st.markdown(format_large_number(row['market_cap']))
            
            with col_1y:
                st.markdown(f'<span style="color: #00CC00; font-size: 18px; font-weight: bold;">▲ {row["perf_1y"]:.2f}%</span>', unsafe_allow_html=True)
            
            with col_sector:
                st.markdown(row['sector'])
            
            st.markdown("---")

with tab3:
    st.subheader("📉 Top 50 Pires Performances sur 1 an")
    st.markdown("*Les actions qui ont le plus baissé*")
    
    if st.button("🔄 Actualiser les données", key="refresh_perf_neg"):
        st.cache_data.clear()
        st.rerun()
    
    with st.spinner("📊 Chargement des données..."):
        if 'df' not in locals() or df.empty:
            stock_data = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, ticker in enumerate(ALL_STOCKS):
                status_text.text(f"Chargement: {ticker} ({idx+1}/{len(ALL_STOCKS)})")
                data = get_stock_data(ticker)
                if data:
                    stock_data.append(data)
                progress_bar.progress((idx + 1) / len(ALL_STOCKS))
                time.sleep(0.1)
            
            progress_bar.empty()
            status_text.empty()
            df = pd.DataFrame(stock_data)
        
        df_sorted = df.sort_values('perf_1y', ascending=True).reset_index(drop=True)
        df_sorted.index = df_sorted.index + 1
        
        # Affichage
        st.markdown("---")
        
        col_rank, col_name, col_price, col_mcap, col_1y, col_sector = st.columns([0.5, 2, 1, 1.5, 1.5, 1.5])
        
        with col_rank:
            st.markdown("**#**")
        with col_name:
            st.markdown("**Nom**")
        with col_price:
            st.markdown("**Prix**")
        with col_mcap:
            st.markdown("**Cap. Boursière**")
        with col_1y:
            st.markdown("**Performance 1an**")
        with col_sector:
            st.markdown("**Secteur**")
        
        st.markdown("---")
        
        for idx, row in df_sorted.head(50).iterrows():
            col_rank, col_name, col_price, col_mcap, col_1y, col_sector = st.columns([0.5, 2, 1, 1.5, 1.5, 1.5])
            
            with col_rank:
                st.markdown(f"**{idx}**")
            
            with col_name:
                st.markdown(f"**{row['ticker']}**")
                st.caption(row['name'][:30] + "..." if len(row['name']) > 30 else row['name'])
            
            with col_price:
                st.markdown(f"${row['price']:.2f}")
            
            with col_mcap:
                st.markdown(format_large_number(row['market_cap']))
            
            with col_1y:
                st.markdown(f'<span style="color: #FF4B4B; font-size: 18px; font-weight: bold;">▼ {abs(row["perf_1y"]):.2f}%</span>', unsafe_allow_html=True)
            
            with col_sector:
                st.markdown(row['sector'])
            
            st.markdown("---")

with tab4:
    st.subheader("💰 Top 50 Meilleurs Dividendes")
    st.markdown("*Les actions avec les meilleurs rendements de dividende*")
    
    if st.button("🔄 Actualiser les données", key="refresh_div"):
        st.cache_data.clear()
        st.rerun()
    
    with st.spinner("📊 Chargement des données..."):
        if 'df' not in locals() or df.empty:
            stock_data = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, ticker in enumerate(ALL_STOCKS):
                status_text.text(f"Chargement: {ticker} ({idx+1}/{len(ALL_STOCKS)})")
                data = get_stock_data(ticker)
                if data:
                    stock_data.append(data)
                progress_bar.progress((idx + 1) / len(ALL_STOCKS))
                time.sleep(0.1)
            
            progress_bar.empty()
            status_text.empty()
            df = pd.DataFrame(stock_data)
        
        df_sorted = df[df['dividend_yield'] > 0].sort_values('dividend_yield', ascending=False).reset_index(drop=True)
        df_sorted.index = df_sorted.index + 1
        
        # Affichage
        st.markdown("---")
        
        col_rank, col_name, col_price, col_div, col_pe, col_sector = st.columns([0.5, 2, 1, 1.5, 1, 1.5])
        
        with col_rank:
            st.markdown("**#**")
        with col_name:
            st.markdown("**Nom**")
        with col_price:
            st.markdown("**Prix**")
        with col_div:
            st.markdown("**Rendement Dividende**")
        with col_pe:
            st.markdown("**P/E**")
        with col_sector:
            st.markdown("**Secteur**")
        
        st.markdown("---")
        
        for idx, row in df_sorted.head(50).iterrows():
            col_rank, col_name, col_price, col_div, col_pe, col_sector = st.columns([0.5, 2, 1, 1.5, 1, 1.5])
            
            with col_rank:
                if idx == 1:
                    st.markdown("🥇")
                elif idx == 2:
                    st.markdown("🥈")
                elif idx == 3:
                    st.markdown("🥉")
                else:
                    st.markdown(f"**{idx}**")
            
            with col_name:
                st.markdown(f"**{row['ticker']}**")
                st.caption(row['name'][:30] + "..." if len(row['name']) > 30 else row['name'])
            
            with col_price:
                st.markdown(f"${row['price']:.2f}")
            
            with col_div:
                st.markdown(f'<span style="color: #00CC00; font-size: 18px; font-weight: bold;">{row["dividend_yield"]:.2f}%</span>', unsafe_allow_html=True)
            
            with col_pe:
                if row['pe_ratio'] > 0:
                    st.markdown(f"{row['pe_ratio']:.2f}")
                else:
                    st.markdown("N/A")
            
            with col_sector:
                st.markdown(row['sector'])
            
            st.markdown("---")

with tab5:
    st.subheader("🔥 Top 50 Plus Gros Volumes")
    st.markdown("*Les actions les plus échangées*")
    
    if st.button("🔄 Actualiser les données", key="refresh_vol"):
        st.cache_data.clear()
        st.rerun()
    
    with st.spinner("📊 Chargement des données..."):
        if 'df' not in locals() or df.empty:
            stock_data = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, ticker in enumerate(ALL_STOCKS):
                status_text.text(f"Chargement: {ticker} ({idx+1}/{len(ALL_STOCKS)})")
                data = get_stock_data(ticker)
                if data:
                    stock_data.append(data)
                progress_bar.progress((idx + 1) / len(ALL_STOCKS))
                time.sleep(0.1)
            
            progress_bar.empty()
            status_text.empty()
            df = pd.DataFrame(stock_data)
        
        df_sorted = df.sort_values('volume', ascending=False).reset_index(drop=True)
        df_sorted.index = df_sorted.index + 1
        
        # Affichage
        st.markdown("---")
        
        col_rank, col_name, col_price, col_volume, col_1d, col_mcap = st.columns([0.5, 2, 1, 1.5, 1.5, 1.5])
        
        with col_rank:
            st.markdown("**#**")
        with col_name:
            st.markdown("**Nom**")
        with col_price:
            st.markdown("**Prix**")
        with col_volume:
            st.markdown("**Volume (24h)**")
        with col_1d:
            st.markdown("**24h**")
        with col_mcap:
            st.markdown("**Cap. Boursière**")
        
        st.markdown("---")
        
        for idx, row in df_sorted.head(50).iterrows():
            col_rank, col_name, col_price, col_volume, col_1d, col_mcap = st.columns([0.5, 2, 1, 1.5, 1.5, 1.5])
            
            with col_rank:
                st.markdown(f"**{idx}**")
            
            with col_name:
                st.markdown(f"**{row['ticker']}**")
                st.caption(row['name'][:30] + "..." if len(row['name']) > 30 else row['name'])
            
            with col_price:
                st.markdown(f"${row['price']:.2f}")
            
            with col_volume:
                st.markdown(f'<span style="font-size: 16px; font-weight: bold;">{format_large_number(row["volume"])}</span>', unsafe_allow_html=True)
            
            with col_1d:
                st.markdown(format_percentage(row['perf_1d']), unsafe_allow_html=True)
            
            with col_mcap:
                st.markdown(format_large_number(row['market_cap']))
            
            st.markdown("---")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; font-size: small;'>
        <span style='margin: 0 50px;'>📊 Classements Boursiers v1.0</span>
        <span style='margin: 0 50px;'>⚠️ Données indicatives - Pas un conseil financier</span>
        <span style='margin: 0 50px;'>Créé par @Mathieugird</span>
    </div>
    """, unsafe_allow_html=True)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    
    /* Style pour les tableaux */
    div[data-testid="column"] {
        padding: 5px;
    }
    
    /* Hover effect sur les lignes */
    div[data-testid="stHorizontalBlock"]:hover {
        background-color: #f0f2f6;
        border-radius: 5px;
        transition: all 0.2s ease;
    }
</style>
""", unsafe_allow_html=True)
