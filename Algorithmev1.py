"""
Algorithme de notation des entreprises cotées en bourse
Analyse automatique selon le secteur et l'horizon d'investissement
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class StockScorer:
    """
    Classe principale pour noter les actions sur 100
    """
    
    def __init__(self, ticker, horizon='long'):
        """
        Initialise le scorer
        
        Args:
            ticker (str): Symbole boursier (ex: 'AAPL', 'MSFT')
            horizon (str): 'court' (< 5 ans), 'long' (> 5 ans)
        """
        self.ticker = ticker.upper()
        self.horizon = horizon.lower()
        self.stock = None
        self.info = None
        self.sector = None
        self.industry = None
        self.scores = {}
        self.final_score = 0
        
    def fetch_data(self):
        """Récupère les données de l'action via Yahoo Finance"""
        try:
            self.stock = yf.Ticker(self.ticker)
            self.info = self.stock.info
            
            if not self.info or len(self.info) < 5 or 'symbol' not in self.info:
                print(f"\n✗ ERREUR: Le ticker '{self.ticker}' n'a pas été trouvé!")
                print(f"\n💡 Suggestions:")
                print(f"   • Vérifiez l'orthographe du ticker")
                print(f"   • Assurez-vous que c'est une action cotée aux USA")
                print(f"   • Exemples de tickers valides: AAPL, MSFT, TSLA, GOOGL, AMZN")
                print(f"   • Pour les actions non-US, ajoutez le suffixe (ex: MC.PA pour LVMH à Paris)")
                return False
            
            self.sector = self.info.get('sector', 'Unknown')
            self.industry = self.info.get('industry', 'Unknown')
            
            if self.sector == 'Unknown' and not self.info.get('currentPrice'):
                print(f"\n✗ ERREUR: Données insuffisantes pour '{self.ticker}'")
                print(f"   Le ticker existe peut-être mais Yahoo Finance ne retourne pas assez de données.")
                return False
            
            print(f"✓ Données récupérées pour {self.ticker}")
            print(f"  Entreprise: {self.info.get('longName', 'N/A')}")
            print(f"  Secteur: {self.sector}")
            print(f"  Industrie: {self.industry}")
            print(f"  Horizon: {self.horizon.upper()}\n")
            
            return True
            
        except Exception as e:
            print(f"\n✗ ERREUR lors de la récupération des données:")
            print(f"   {str(e)}")
            print(f"\n💡 Vérifiez votre connexion internet et que le ticker '{self.ticker}' est valide.")
            return False
    
    def search_ticker(self, company_name):
        """
        Recherche un ticker à partir du nom d'une entreprise
        
        Args:
            company_name (str): Nom de l'entreprise (ex: "Google", "Microsoft")
            
        Returns:
            str: Ticker trouvé ou None
        """
        
        common_names = {
            'google': 'GOOGL',
            'alphabet': 'GOOGL',
            'microsoft': 'MSFT',
            'apple': 'AAPL',
            'amazon': 'AMZN',
            'meta': 'META',
            'facebook': 'META',
            'nvidia': 'NVDA',
            'tesla': 'TSLA',
            'netflix': 'NFLX',
            'intel': 'INTC',
            'amd': 'AMD',
            'oracle': 'ORCL',
            'salesforce': 'CRM',
            'adobe': 'ADBE',
            'cisco': 'CSCO',
            'ibm': 'IBM',
            
            'jpmorgan': 'JPM',
            'jp morgan': 'JPM',
            'bank of america': 'BAC',
            'wells fargo': 'WFC',
            'goldman sachs': 'GS',
            'morgan stanley': 'MS',
            'visa': 'V',
            'mastercard': 'MA',
            'american express': 'AXP',
            'amex': 'AXP',
            'paypal': 'PYPL',
            'citigroup': 'C',
            
            'johnson & johnson': 'JNJ',
            'johnson and johnson': 'JNJ',
            'pfizer': 'PFE',
            'moderna': 'MRNA',
            'abbott': 'ABT',
            'merck': 'MRK',
            'unitedhealth': 'UNH',
            'eli lilly': 'LLY',
            'bristol myers': 'BMY',
            
            'coca cola': 'KO',
            'coca-cola': 'KO',
            'pepsi': 'PEP',
            'pepsico': 'PEP',
            'procter & gamble': 'PG',
            'procter and gamble': 'PG',
            'walmart': 'WMT',
            'costco': 'COST',
            'nike': 'NKE',
            'starbucks': 'SBUX',
            'mcdonald': 'MCD',
            "mcdonald's": 'MCD',
            'mcdonalds': 'MCD',
            'home depot': 'HD',
            'disney': 'DIS',
            
            'exxon': 'XOM',
            'exxon mobil': 'XOM',
            'chevron': 'CVX',
            'conocophillips': 'COP',
            'shell': 'SHEL',
            'totalenergies': 'TTE',
            'total energies': 'TTE',
            'total': 'TTE',
            'bp': 'BP',
            
            'lvmh': 'MC.PA',
            'hermès': 'RMS.PA',
            'hermes': 'RMS.PA',
            'kering': 'KER.PA',
            'l\'oréal': 'OR.PA',
            'loreal': 'OR.PA',
            'l\'oreal': 'OR.PA',
            'dior': 'CDI.PA',
            
            'airbus': 'AIR.PA',
            'sanofi': 'SAN.PA',
            'bnp paribas': 'BNP.PA',
            'bnp': 'BNP.PA',
            'axa': 'CS.PA',
            'schneider': 'SU.PA',
            'schneider electric': 'SU.PA',
            'safran': 'SAF.PA',
            'danone': 'BN.PA',
            'stellantis': 'STLA',
            'peugeot': 'STLA',
            'renault': 'RNO.PA',
            'carrefour': 'CA.PA',
            'veolia': 'VIE.PA',
            'orange': 'ORA.PA',
            'michelin': 'ML.PA',
            'publicis': 'PUB.PA',
            'capgemini': 'CAP.PA',
            'bouygues': 'EN.PA',
            'vinci': 'DG.PA',
            'saint-gobain': 'SGO.PA',
            'saint gobain': 'SGO.PA',
            'legrand': 'LR.PA',
            'essilor': 'EL.PA',
            'essilorluxottica': 'EL.PA',
            
            'toyota': 'TM',
            'ford': 'F',
            'general motors': 'GM',
            'gm': 'GM',
            
            'verizon': 'VZ',
            'at&t': 'T',
            'att': 'T',
            't-mobile': 'TMUS',
            'comcast': 'CMCSA',
        }
        
        normalized_name = company_name.lower().strip()
        
        if normalized_name in common_names:
            ticker = common_names[normalized_name]
            print(f"✓ '{company_name}' trouvé → Ticker: {ticker}")
            return ticker
        
        # Si c'est déjà un ticker (court et en majuscules ou contient un point pour les marchés étrangers)
        if len(company_name) <= 6 and (company_name.isupper() or '.' in company_name):
            print(f"✓ '{company_name}' semble être un ticker → Utilisation directe")
            return company_name.upper()
        
        # Sinon, on essaie de chercher via yfinance (optionnel, peut être lent)
        print(f"⚠️ '{company_name}' non reconnu dans la base de données.")
        print(f"💡 Essayez d'entrer directement le ticker (ex: AAPL pour Apple)")
        return None
    
    def safe_get(self, key, default='N/A'):
        """Récupère une valeur de self.info en gérant les None"""
        value = self.info.get(key, default)
        return value if value is not None else default
    
    def score_momentum_6m(self):
        """Score basé sur la performance des 6 derniers mois"""
        try:
            hist = self.stock.history(period="6mo")
            if hist.empty or len(hist) < 2:
                return 5.0
            
            perf = ((hist['Close'][-1] - hist['Close'][0]) / hist['Close'][0]) * 100
            
            if perf > 30:
                return 10.0
            elif perf > 20:
                return 9.0
            elif perf > 15:
                return 8.0
            elif perf > 10:
                return 7.0
            elif perf > 5:
                return 6.0
            elif perf > 0:
                return 5.5
            elif perf > -5:
                return 4.5
            elif perf > -10:
                return 3.5
            elif perf > -15:
                return 2.5
            else:
                return 1.0
        except:
            return 5.0
    
    def score_momentum_3m(self):
        """Score basé sur la performance des 3 derniers mois"""
        try:
            hist = self.stock.history(period="3mo")
            if hist.empty or len(hist) < 2:
                return 5.0
            
            perf = ((hist['Close'][-1] - hist['Close'][0]) / hist['Close'][0]) * 100
            
            if perf > 20:
                return 10.0
            elif perf > 15:
                return 9.0
            elif perf > 10:
                return 8.0
            elif perf > 5:
                return 7.0
            elif perf > 2:
                return 6.0
            elif perf > 0:
                return 5.5
            elif perf > -5:
                return 4.0
            elif perf > -10:
                return 3.0
            else:
                return 1.5
        except:
            return 5.0
    
    def score_rsi(self):
        """Score basé sur le RSI (14 jours)"""
        try:
            hist = self.stock.history(period="3mo")
            if hist.empty or len(hist) < 15:
                return 5.0
            
            delta = hist['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            if pd.isna(current_rsi):
                return 5.0
            
            if current_rsi < 30:
                return 9.0 + (30 - current_rsi) / 30
            elif current_rsi < 40:
                return 7.0 + (40 - current_rsi) / 10 * 2
            elif current_rsi < 50:
                return 6.0 + (50 - current_rsi) / 10
            elif current_rsi < 60:
                return 5.0
            elif current_rsi < 70:
                return 4.0 - (current_rsi - 60) / 10
            else:
                return max(0, 3.0 - (current_rsi - 70) / 10)
        except:
            return 5.0
    
    def score_volume_trend(self):
        """Score basé sur la tendance de volume"""
        try:
            hist = self.stock.history(period="3mo")
            if hist.empty or len(hist) < 20:
                return 5.0
            
            avg_vol_recent = hist['Volume'][-10:].mean()
            avg_vol_old = hist['Volume'][-30:-10].mean()
            
            if avg_vol_old == 0:
                return 5.0
            
            vol_change = ((avg_vol_recent - avg_vol_old) / avg_vol_old) * 100
            
            if vol_change > 50:
                return 9.0
            elif vol_change > 30:
                return 8.0
            elif vol_change > 15:
                return 7.0
            elif vol_change > 0:
                return 6.0
            elif vol_change > -15:
                return 5.0
            elif vol_change > -30:
                return 4.0
            else:
                return 3.0
        except:
            return 5.0
    
    def score_pe_ratio(self):
        """Score basé sur le Price-to-Earnings Ratio"""
        pe = self.safe_get('trailingPE') or self.safe_get('forwardPE')
        
        if pe == 'N/A' or pe <= 0:
            return 5.0
        
        if pe < 10:
            return 10.0
        elif pe < 15:
            return 9.0
        elif pe < 20:
            return 7.5
        elif pe < 25:
            return 6.0
        elif pe < 30:
            return 4.5
        elif pe < 40:
            return 3.0
        else:
            return 1.0
    
    def score_peg_ratio(self):
        """Score basé sur le PEG Ratio"""
        peg = self.safe_get('pegRatio')
        
        if peg == 'N/A' or peg <= 0:
            return 5.0
        
        if peg < 0.5:
            return 10.0
        elif peg < 1.0:
            return 9.0
        elif peg < 1.5:
            return 7.0
        elif peg < 2.0:
            return 5.0
        elif peg < 2.5:
            return 3.5
        else:
            return 1.5
    
    def score_revenue_growth(self):
        """Score basé sur la croissance du chiffre d'affaires"""
        growth = self.safe_get('revenueGrowth')
        
        if growth == 'N/A':
            return 5.0
        
        growth_pct = growth * 100
        
        if growth_pct > 30:
            return 10.0
        elif growth_pct > 20:
            return 9.0
        elif growth_pct > 15:
            return 8.0
        elif growth_pct > 10:
            return 7.0
        elif growth_pct > 5:
            return 6.0
        elif growth_pct > 0:
            return 5.0
        elif growth_pct > -5:
            return 3.5
        else:
            return 1.0
    
    def score_profit_margins(self):
        """Score basé sur les marges bénéficiaires"""
        margin = self.safe_get('profitMargins')
        
        if margin == 'N/A':
            return 5.0
        
        margin_pct = margin * 100
        
        if margin_pct > 25:
            return 10.0
        elif margin_pct > 20:
            return 9.0
        elif margin_pct > 15:
            return 8.0
        elif margin_pct > 10:
            return 7.0
        elif margin_pct > 5:
            return 6.0
        elif margin_pct > 0:
            return 5.0
        else:
            return 2.0
    
    def score_operating_margin(self):
        """Score basé sur la marge opérationnelle"""
        margin = self.safe_get('operatingMargins')
        
        if margin == 'N/A':
            return 5.0
        
        margin_pct = margin * 100
        
        if margin_pct > 30:
            return 10.0
        elif margin_pct > 20:
            return 9.0
        elif margin_pct > 15:
            return 8.0
        elif margin_pct > 10:
            return 7.0
        elif margin_pct > 5:
            return 6.0
        elif margin_pct > 0:
            return 5.0
        else:
            return 2.5
    
    def score_roe(self):
        """Score basé sur le Return on Equity"""
        roe = self.safe_get('returnOnEquity')
        
        if roe == 'N/A':
            return 5.0
        
        roe_pct = roe * 100
        
        if roe_pct > 25:
            return 10.0
        elif roe_pct > 20:
            return 9.0
        elif roe_pct > 15:
            return 8.0
        elif roe_pct > 10:
            return 7.0
        elif roe_pct > 5:
            return 6.0
        elif roe_pct > 0:
            return 5.0
        else:
            return 2.0
    
    def score_roa(self):
        """Score basé sur le Return on Assets"""
        roa = self.safe_get('returnOnAssets')
        
        if roa == 'N/A':
            return 5.0
        
        roa_pct = roa * 100
        
        if roa_pct > 15:
            return 10.0
        elif roa_pct > 10:
            return 9.0
        elif roa_pct > 7:
            return 8.0
        elif roa_pct > 5:
            return 7.0
        elif roa_pct > 3:
            return 6.0
        elif roa_pct > 0:
            return 5.0
        else:
            return 2.0
    
    def score_debt_to_equity(self):
        """Score basé sur le ratio Dette/Capitaux Propres"""
        debt_to_equity = self.safe_get('debtToEquity')
        
        if debt_to_equity == 'N/A':
            return 5.0
        
        if debt_to_equity < 20:
            return 10.0
        elif debt_to_equity < 40:
            return 9.0
        elif debt_to_equity < 60:
            return 8.0
        elif debt_to_equity < 80:
            return 7.0
        elif debt_to_equity < 100:
            return 6.0
        elif debt_to_equity < 150:
            return 4.5
        elif debt_to_equity < 200:
            return 3.0
        else:
            return 1.5
    
    def score_debt_to_assets(self):
        """Score basé sur le ratio Dette/Actifs"""
        try:
            total_debt = self.safe_get('totalDebt')
            total_assets = self.safe_get('totalAssets')
            
            if total_debt == 'N/A' or total_assets == 'N/A' or total_assets == 0:
                return 5.0
            
            debt_to_assets = (total_debt / total_assets) * 100
            
            if debt_to_assets < 20:
                return 10.0
            elif debt_to_assets < 30:
                return 9.0
            elif debt_to_assets < 40:
                return 8.0
            elif debt_to_assets < 50:
                return 7.0
            elif debt_to_assets < 60:
                return 6.0
            elif debt_to_assets < 70:
                return 4.5
            else:
                return 2.5
        except:
            return 5.0
    
    def score_current_ratio(self):
        """Score basé sur le ratio de liquidité (Current Ratio)"""
        current_ratio = self.safe_get('currentRatio')
        
        if current_ratio == 'N/A':
            return 5.0
        
        if current_ratio > 2.5:
            return 10.0
        elif current_ratio > 2.0:
            return 9.0
        elif current_ratio > 1.5:
            return 8.0
        elif current_ratio > 1.2:
            return 7.0
        elif current_ratio > 1.0:
            return 6.0
        elif current_ratio > 0.8:
            return 4.0
        else:
            return 2.0
    
    def score_free_cash_flow(self):
        """Score basé sur le Free Cash Flow"""
        fcf = self.safe_get('freeCashflow')
        
        if fcf == 'N/A':
            return 5.0
        
        if fcf > 10_000_000_000:  # > 10B
            return 10.0
        elif fcf > 5_000_000_000:   # > 5B
            return 9.0
        elif fcf > 1_000_000_000:   # > 1B
            return 8.0
        elif fcf > 500_000_000:     # > 500M
            return 7.0
        elif fcf > 100_000_000:     # > 100M
            return 6.0
        elif fcf > 0:
            return 5.0
        else:
            return 2.0
    
    def score_dividend_yield(self):
        """Score basé sur le rendement du dividende"""
        div_yield = self.safe_get('dividendYield')
        
        if div_yield == 'N/A' or div_yield == 0:
            return 5.0
        
        div_yield_pct = div_yield * 100
        
        if div_yield_pct > 5:
            return 10.0
        elif div_yield_pct > 4:
            return 9.0
        elif div_yield_pct > 3:
            return 8.0
        elif div_yield_pct > 2:
            return 7.0
        elif div_yield_pct > 1:
            return 6.0
        else:
            return 5.0
    
    def score_dividend_growth(self):
        """Score basé sur la croissance du dividende (5 ans)"""
        try:
            dividends = self.stock.dividends
            if dividends.empty or len(dividends) < 2:
                return 5.0
            
            recent_div = dividends[-252:].sum() if len(dividends) >= 252 else dividends.sum()
            old_div = dividends[-504:-252].sum() if len(dividends) >= 504 else 0
            
            if old_div == 0:
                return 5.0
            
            growth = ((recent_div - old_div) / old_div) * 100
            
            if growth > 15:
                return 10.0
            elif growth > 10:
                return 9.0
            elif growth > 7:
                return 8.0
            elif growth > 5:
                return 7.0
            elif growth > 3:
                return 6.0
            elif growth > 0:
                return 5.5
            else:
                return 3.0
        except:
            return 5.0
    
    def score_price_to_book(self):
        """Score basé sur le Price-to-Book Ratio"""
        pb = self.safe_get('priceToBook')
        
        if pb == 'N/A' or pb <= 0:
            return 5.0
        
        if pb < 1:
            return 10.0
        elif pb < 1.5:
            return 9.0
        elif pb < 2:
            return 8.0
        elif pb < 3:
            return 7.0
        elif pb < 4:
            return 6.0
        elif pb < 5:
            return 4.5
        else:
            return 2.5
    
    def score_beta(self):
        """Score basé sur le Beta (volatilité par rapport au marché)"""
        beta = self.safe_get('beta')
        
        if beta == 'N/A':
            return 5.0
        
        if beta < 0.5:
            return 10.0
        elif beta < 0.8:
            return 9.0
        elif beta < 1.0:
            return 8.0
        elif beta < 1.2:
            return 7.0
        elif beta < 1.5:
            return 6.0
        elif beta < 2.0:
            return 4.0
        else:
            return 2.0
    
    def calculate_score(self):
        """
        Calcule le score final en fonction du secteur et de l'horizon
        """
        if not self.fetch_data():
            return None
        
        weighted_scores = []
        
        # SECTEUR TECHNOLOGIE
        if self.sector == 'Technology':
            if self.horizon == 'court':
                weighted_scores.extend([
                    (self.score_momentum_6m(), 0.25, 'Momentum 6M'),
                    (self.score_momentum_3m(), 0.15, 'Momentum 3M'),
                    (self.score_rsi(), 0.15, 'RSI'),
                    (self.score_revenue_growth(), 0.15, 'Croissance CA'),
                    (self.score_volume_trend(), 0.10, 'Volume'),
                    (self.score_pe_ratio(), 0.10, 'P/E Ratio'),
                    (self.score_beta(), 0.10, 'Beta'),
                ])
            else:  # long terme
                weighted_scores.extend([
                    (self.score_revenue_growth(), 0.20, 'Croissance CA'),
                    (self.score_peg_ratio(), 0.20, 'PEG Ratio'),
                    (self.score_roe(), 0.15, 'ROE'),
                    (self.score_profit_margins(), 0.15, 'Marges'),
                    (self.score_free_cash_flow(), 0.15, 'Free Cash Flow'),
                    (self.score_debt_to_equity(), 0.10, 'Dette/Capitaux'),
                    (self.score_beta(), 0.05, 'Beta'),
                ])
        
        # SECTEUR HEALTHCARE
        elif self.sector == 'Healthcare':
            if self.horizon == 'court':
                weighted_scores.extend([
                    (self.score_momentum_6m(), 0.20, 'Momentum 6M'),
                    (self.score_revenue_growth(), 0.15, 'Croissance CA'),
                    (self.score_rsi(), 0.15, 'RSI'),
                    (self.score_profit_margins(), 0.15, 'Marges'),
                    (self.score_pe_ratio(), 0.15, 'P/E Ratio'),
                    (self.score_free_cash_flow(), 0.10, 'Free Cash Flow'),
                    (self.score_beta(), 0.10, 'Beta'),
                ])
            else:  # long terme
                weighted_scores.extend([
                    (self.score_roe(), 0.20, 'ROE'),
                    (self.score_revenue_growth(), 0.20, 'Croissance CA'),
                    (self.score_free_cash_flow(), 0.20, 'Free Cash Flow'),
                    (self.score_profit_margins(), 0.15, 'Marges'),
                    (self.score_debt_to_equity(), 0.15, 'Dette/Capitaux'),
                    (self.score_peg_ratio(), 0.10, 'PEG Ratio'),
                ])
        
        # SECTEUR FINANCE
        elif self.sector == 'Financial Services':
            if self.horizon == 'court':
                weighted_scores.extend([
                    (self.score_momentum_6m(), 0.20, 'Momentum 6M'),
                    (self.score_rsi(), 0.15, 'RSI'),
                    (self.score_pe_ratio(), 0.15, 'P/E Ratio'),
                    (self.score_roe(), 0.15, 'ROE'),
                    (self.score_price_to_book(), 0.15, 'Price/Book'),
                    (self.score_dividend_yield(), 0.10, 'Dividende'),
                    (self.score_beta(), 0.10, 'Beta'),
                ])
            else:  # long terme
                weighted_scores.extend([
                    (self.score_roe(), 0.25, 'ROE'),
                    (self.score_dividend_yield(), 0.20, 'Dividende'),
                    (self.score_price_to_book(), 0.20, 'Price/Book'),
                    (self.score_debt_to_equity(), 0.15, 'Dette/Capitaux'),
                    (self.score_profit_margins(), 0.10, 'Marges'),
                    (self.score_beta(), 0.10, 'Beta'),
                ])
        
        # SECTEUR CONSUMER CYCLICAL
        elif self.sector == 'Consumer Cyclical':
            if self.horizon == 'court':
                weighted_scores.extend([
                    (self.score_momentum_6m(), 0.25, 'Momentum 6M'),
                    (self.score_revenue_growth(), 0.20, 'Croissance CA'),
                    (self.score_rsi(), 0.15, 'RSI'),
                    (self.score_profit_margins(), 0.15, 'Marges'),
                    (self.score_volume_trend(), 0.10, 'Volume'),
                    (self.score_pe_ratio(), 0.10, 'P/E Ratio'),
                    (self.score_beta(), 0.05, 'Beta'),
                ])
            else:  # long terme
                weighted_scores.extend([
                    (self.score_revenue_growth(), 0.20, 'Croissance CA'),
                    (self.score_roe(), 0.20, 'ROE'),
                    (self.score_profit_margins(), 0.20, 'Marges'),
                    (self.score_free_cash_flow(), 0.15, 'Free Cash Flow'),
                    (self.score_debt_to_equity(), 0.15, 'Dette/Capitaux'),
                    (self.score_peg_ratio(), 0.10, 'PEG Ratio'),
                ])
        
        # SECTEUR CONSUMER DEFENSIVE
        elif self.sector == 'Consumer Defensive':
            if self.horizon == 'court':
                weighted_scores.extend([
                    (self.score_dividend_yield(), 0.25, 'Dividende'),
                    (self.score_momentum_6m(), 0.20, 'Momentum 6M'),
                    (self.score_profit_margins(), 0.15, 'Marges'),
                    (self.score_rsi(), 0.15, 'RSI'),
                    (self.score_beta(), 0.15, 'Beta'),
                    (self.score_debt_to_equity(), 0.10, 'Dette/Capitaux'),
                ])
            else:  # long terme
                weighted_scores.extend([
                    (self.score_dividend_yield(), 0.30, 'Dividende'),
                    (self.score_dividend_growth(), 0.20, 'Croiss. Dividende'),
                    (self.score_roe(), 0.15, 'ROE'),
                    (self.score_profit_margins(), 0.15, 'Marges'),
                    (self.score_debt_to_equity(), 0.10, 'Dette/Capitaux'),
                    (self.score_beta(), 0.10, 'Beta'),
                ])
        
        # SECTEUR ÉNERGIE
        elif self.sector == 'Energy':
            if self.horizon == 'court':
                weighted_scores.extend([
                    (self.score_momentum_6m(), 0.25, 'Momentum 6M'),
                    (self.score_operating_margin(), 0.20, 'Marge Opé'),
                    (self.score_rsi(), 0.15, 'RSI'),
                    (self.score_free_cash_flow(), 0.15, 'Free Cash Flow'),
                    (self.score_dividend_yield(), 0.15, 'Dividende'),
                    (self.score_beta(), 0.10, 'Beta'),
                ])
            else:  # long terme
                weighted_scores.extend([
                    (self.score_free_cash_flow(), 0.25, 'Free Cash Flow'),
                    (self.score_dividend_yield(), 0.20, 'Dividende'),
                    (self.score_operating_margin(), 0.20, 'Marge Opé'),
                    (self.score_debt_to_equity(), 0.15, 'Dette/Capitaux'),
                    (self.score_roe(), 0.10, 'ROE'),
                    (self.score_beta(), 0.10, 'Beta'),
                ])
        
        # SECTEUR INDUSTRIEL
        elif self.sector == 'Industrials':
            if self.horizon == 'court':
                weighted_scores.extend([
                    (self.score_momentum_6m(), 0.20, 'Momentum 6M'),
                    (self.score_revenue_growth(), 0.20, 'Croissance CA'),
                    (self.score_rsi(), 0.15, 'RSI'),
                    (self.score_operating_margin(), 0.15, 'Marge Opé'),
                    (self.score_free_cash_flow(), 0.15, 'Free Cash Flow'),
                    (self.score_beta(), 0.15, 'Beta'),
                ])
            else:  # long terme
                weighted_scores.extend([
                    (self.score_roe(), 0.20, 'ROE'),
                    (self.score_free_cash_flow(), 0.20, 'Free Cash Flow'),
                    (self.score_operating_margin(), 0.20, 'Marge Opé'),
                    (self.score_debt_to_equity(), 0.20, 'Dette/Capitaux'),
                    (self.score_dividend_yield(), 0.10, 'Dividende'),
                    (self.score_beta(), 0.10, 'Beta'),
                ])
        
        # SECTEUR REAL ESTATE
        elif self.sector == 'Real Estate':
            if self.horizon == 'court':
                weighted_scores.extend([
                    (self.score_dividend_yield(), 0.25, 'Dividende'),
                    (self.score_price_to_book(), 0.15, 'Price/Book'),
                    (self.score_rsi(), 0.10, 'RSI'),
                    (self.score_debt_to_assets(), 0.15, 'Dette/Actifs'),
                    (self.score_beta(), 0.15, 'Beta'),
                ])
            else:  # long terme
                weighted_scores.extend([
                    (self.score_dividend_yield(), 0.30, 'Dividende'),
                    (self.score_dividend_growth(), 0.20, 'Croiss. Dividende'),
                    (self.score_debt_to_assets(), 0.20, 'Dette/Actifs'),
                    (self.score_price_to_book(), 0.15, 'Price/Book'),
                    (self.score_roe(), 0.10, 'ROE'),
                    (self.score_beta(), 0.05, 'Beta'),
                ])
        
        # SECTEUR UTILITIES
        elif self.sector == 'Utilities':
            if self.horizon == 'court':
                weighted_scores.extend([
                    (self.score_momentum_6m(), 0.15, 'Momentum 6M'),
                    (self.score_dividend_yield(), 0.30, 'Dividende'),
                    (self.score_beta(), 0.15, 'Beta'),
                    (self.score_rsi(), 0.10, 'RSI'),
                    (self.score_debt_to_equity(), 0.15, 'Dette/Capitaux'),
                    (self.score_current_ratio(), 0.15, 'Liquidité'),
                ])
            else:  # long terme
                weighted_scores.extend([
                    (self.score_dividend_yield(), 0.30, 'Dividende'),
                    (self.score_dividend_growth(), 0.25, 'Croiss. Dividende'),
                    (self.score_debt_to_equity(), 0.20, 'Dette/Capitaux'),
                    (self.score_beta(), 0.15, 'Beta'),
                    (self.score_free_cash_flow(), 0.10, 'Free Cash Flow'),
                ])
        
        # SECTEUR BASIC MATERIALS
        elif self.sector == 'Basic Materials':
            if self.horizon == 'court':
                weighted_scores.extend([
                    (self.score_momentum_6m(), 0.20, 'Momentum 6M'),
                    (self.score_operating_margin(), 0.20, 'Marge Opé'),
                    (self.score_free_cash_flow(), 0.15, 'Free Cash Flow'),
                    (self.score_rsi(), 0.10, 'RSI'),
                    (self.score_debt_to_equity(), 0.15, 'Dette/Capitaux'),
                    (self.score_revenue_growth(), 0.10, 'Croissance CA'),
                    (self.score_beta(), 0.10, 'Beta'),
                ])
            else:  # long terme
                weighted_scores.extend([
                    (self.score_free_cash_flow(), 0.25, 'Free Cash Flow'),
                    (self.score_operating_margin(), 0.20, 'Marge Opé'),
                    (self.score_debt_to_equity(), 0.20, 'Dette/Capitaux'),
                    (self.score_roe(), 0.15, 'ROE'),
                    (self.score_current_ratio(), 0.10, 'Liquidité'),
                    (self.score_dividend_yield(), 0.10, 'Dividende'),
                ])
        
        # SECTEUR COMMUNICATION SERVICES
        elif self.sector == 'Communication Services':
            if self.horizon == 'court':
                weighted_scores.extend([
                    (self.score_momentum_6m(), 0.20, 'Momentum 6M'),
                    (self.score_revenue_growth(), 0.20, 'Croissance CA'),
                    (self.score_operating_margin(), 0.15, 'Marge Opé'),
                    (self.score_rsi(), 0.10, 'RSI'),
                    (self.score_free_cash_flow(), 0.15, 'Free Cash Flow'),
                    (self.score_volume_trend(), 0.10, 'Volume'),
                    (self.score_beta(), 0.10, 'Beta'),
                ])
            else:  # long terme
                weighted_scores.extend([
                    (self.score_free_cash_flow(), 0.25, 'Free Cash Flow'),
                    (self.score_operating_margin(), 0.20, 'Marge Opé'),
                    (self.score_revenue_growth(), 0.15, 'Croissance CA'),
                    (self.score_debt_to_equity(), 0.15, 'Dette/Capitaux'),
                    (self.score_roe(), 0.15, 'ROE'),
                    (self.score_dividend_yield(), 0.10, 'Dividende'),
                ])
        
        # SECTEUR PAR DÉFAUT (tous les autres)
        else:
            if self.horizon == 'court':
                weighted_scores.extend([
                    (self.score_momentum_6m(), 0.25, 'Momentum 6M'),
                    (self.score_rsi(), 0.15, 'RSI'),
                    (self.score_volume_trend(), 0.15, 'Volume'),
                    (self.score_revenue_growth(), 0.15, 'Croissance CA'),
                    (self.score_profit_margins(), 0.15, 'Marges'),
                    (self.score_beta(), 0.15, 'Beta'),
                ])
            else:  # long terme
                weighted_scores.extend([
                    (self.score_roe(), 0.20, 'ROE'),
                    (self.score_profit_margins(), 0.20, 'Marges'),
                    (self.score_free_cash_flow(), 0.20, 'Free Cash Flow'),
                    (self.score_debt_to_equity(), 0.20, 'Dette/Capitaux'),
                    (self.score_dividend_yield(), 0.10, 'Dividende'),
                    (self.score_beta(), 0.10, 'Beta'),
                ])
        
        # Calcul du score final
        self.scores = {}
        for score_val, weight, name in weighted_scores:
            self.scores[name] = score_val
        
        weighted_sum = sum(score * weight for score, weight, _ in weighted_scores)
        total_weight = sum(weight for _, weight, _ in weighted_scores)
        
        if total_weight > 0:
            self.final_score = round((weighted_sum / total_weight) * 10, 2)
        else:
            self.final_score = 0
        
        return self.final_score
    
    def display_results(self):
        """Affiche les résultats détaillés"""
        print("=" * 70)
        print(f"ANALYSE DE {self.ticker} - {self.info.get('longName', 'N/A')}")
        print("=" * 70)
        print(f"Secteur: {self.sector}")
        print(f"Horizon d'investissement: {self.horizon.upper()}")
        print(f"\n{'SCORE FINAL':^70}")
        print(f"{'=' * 70}")
        
        score_display = f"{self.final_score}/100"
        if self.final_score >= 70:
            recommendation = "BONNE ENTREPRISE - ACHAT ✓✓✓"
            emoji = "🟢"
        elif self.final_score >= 40:
            recommendation = "ENTREPRISE MOYENNE - PRUDENCE ⚠️"
            emoji = "🟡"
        else:
            recommendation = "MAUVAISE ENTREPRISE - ÉVITER ✗✗✗"
            emoji = "🔴"
        
        print(f"{emoji} {score_display:^60} {emoji}")
        print(f"{recommendation:^70}")
        print(f"{'=' * 70}\n")
        
        print(f"{'DÉTAIL DES SCORES':<50}{'Score':>10}{'(/10)':>10}")
        print("-" * 70)
        
        for indicator, score in sorted(self.scores.items(), key=lambda x: x[1], reverse=True):
            indicator_display = indicator.replace('_', ' ').title()
            print(f"{indicator_display:<50}{score:>10.2f}{'/10':>10}")
        
        print("=" * 70)
        
        print(f"\nINFORMATIONS COMPLÉMENTAIRES")
        print("-" * 70)
        print(f"Prix actuel: ${self.safe_get('currentPrice', 'N/A')}")
        print(f"Capitalisation: ${self.safe_get('marketCap', 0):,.0f}")
        print(f"Volume moyen: {self.safe_get('averageVolume', 0):,.0f}")
        print(f"52 Week High: ${self.safe_get('fiftyTwoWeekHigh', 'N/A')}")
        print(f"52 Week Low: ${self.safe_get('fiftyTwoWeekLow', 'N/A')}")
        print("=" * 70)


def main():
    """Fonction principale pour tester l'algorithme"""
    
    print("\n" + "="*70)
    print(" ALGORITHME DE NOTATION DES ACTIONS BOURSIÈRES ".center(70))
    print(" Échelle: 0-40 (Nul) | 40-70 (Moyen) | 70-100 (Bon) ".center(70))
    print("="*70 + "\n")
    
    user_input = input("Entrez le ticker OU le nom de l'entreprise (ex: AAPL, Google, Microsoft): ").strip()
    
    temp_scorer = StockScorer(user_input, 'long')
    
    ticker = temp_scorer.search_ticker(user_input)
    
    if ticker is None:
        print("\n❌ Impossible de continuer sans ticker valide.")
        return
    
    print()
    
    print("Horizon d'investissement:")
    print("  1. Court terme (< 5 ans)")
    print("  2. Long terme (> 5 ans)")
    
    horizon_choice = input("Votre choix (1/2): ").strip()
    
    horizon_map = {
        '1': 'court',
        '2': 'long'
    }
    
    horizon = horizon_map.get(horizon_choice, 'long')
    
    print(f"\n⏳ Analyse en cours de {ticker.upper()} pour un horizon {horizon.upper()}...\n")
    
    scorer = StockScorer(ticker, horizon)
    score = scorer.calculate_score()
    
    if score is not None:
        scorer.display_results()
    else:
        print("\n" + "="*70)
        print(" ANALYSE IMPOSSIBLE ".center(70))
        print("="*70)
        print("\n⚠️  L'analyse n'a pas pu être effectuée.")
        print("\n💡 Conseils:")
        print("   • Vérifiez que le ticker est correct")
        print("   • Essayez avec un autre ticker (ex: AAPL, MSFT, TSLA)")
        print("   • Vérifiez votre connexion internet")
        print("="*70 + "\n")


if __name__ == "__main__":
    main()
