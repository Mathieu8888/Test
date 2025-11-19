"""
Module de recherche intelligente HYBRIDE d'entreprises
- Cache local pour les entreprises populaires (instantané)
- API Yahoo Finance pour TOUTES les entreprises mondiales (60,000+)
"""

from fuzzywuzzy import fuzz, process
from typing import List, Tuple, Optional
import yfinance as yf

# Dictionnaire des entreprises POPULAIRES (cache rapide)
# FORMAT AMÉLIORÉ : On ajoute aussi les recherches par nom complet
POPULAR_COMPANIES = {
    # Tech
    'google': ('GOOGL', 'Alphabet Inc. (Google)'),
    'alphabet': ('GOOGL', 'Alphabet Inc.'),
    'microsoft': ('MSFT', 'Microsoft Corporation'),
    'apple': ('AAPL', 'Apple Inc.'),
    'amazon': ('AMZN', 'Amazon.com Inc.'),
    'meta': ('META', 'Meta Platforms Inc.'),
    'facebook': ('META', 'Meta Platforms Inc. (Facebook)'),
    'nvidia': ('NVDA', 'NVIDIA Corporation'),
    'tesla': ('TSLA', 'Tesla Inc.'),
    'netflix': ('NFLX', 'Netflix Inc.'),
    'intel': ('INTC', 'Intel Corporation'),
    'amd': ('AMD', 'Advanced Micro Devices'),
    'oracle': ('ORCL', 'Oracle Corporation'),
    'salesforce': ('CRM', 'Salesforce Inc.'),
    'adobe': ('ADBE', 'Adobe Inc.'),
    'cisco': ('CSCO', 'Cisco Systems Inc.'),
    'ibm': ('IBM', 'International Business Machines'),
    
    # Automotive & Luxury
    'ferrari': ('RACE', 'Ferrari N.V.'),
    'lamborghini': ('POAHY', 'Porsche Automobil Holding SE'),
    'porsche': ('POAHY', 'Porsche Automobil Holding SE'),
    'bmw': ('BMWYY', 'Bayerische Motoren Werke AG'),
    'mercedes': ('DDAIF', 'Mercedes-Benz Group AG'),
    'volkswagen': ('VWAGY', 'Volkswagen AG'),
    
    # Gaming & Entertainment
    'nintendo': ('NTDOY', 'Nintendo Co., Ltd.'),
    'sony': ('SONY', 'Sony Group Corporation'),
    'activision': ('ATVI', 'Activision Blizzard Inc.'),
    'electronic arts': ('EA', 'Electronic Arts Inc.'),
    'ea': ('EA', 'Electronic Arts Inc.'),
    'take two': ('TTWO', 'Take-Two Interactive Software'),
    'ubisoft': ('UBSFY', 'Ubisoft Entertainment SA'),
    
    # Asian Tech Giants
    'samsung': ('005930.KS', 'Samsung Electronics Co., Ltd.'),
    'alibaba': ('BABA', 'Alibaba Group Holding Limited'),
    'tencent': ('TCEHY', 'Tencent Holdings Limited'),
    'xiaomi': ('1810.HK', 'Xiaomi Corporation'),
    'baidu': ('BIDU', 'Baidu Inc.'),
    'jd': ('JD', 'JD.com Inc.'),
    'jd.com': ('JD', 'JD.com Inc.'),
    
    # Finance
    'jpmorgan': ('JPM', 'JPMorgan Chase & Co.'),
    'jp morgan': ('JPM', 'JPMorgan Chase & Co.'),
    'bank of america': ('BAC', 'Bank of America Corp.'),
    'wells fargo': ('WFC', 'Wells Fargo & Company'),
    'goldman sachs': ('GS', 'Goldman Sachs Group Inc.'),
    'morgan stanley': ('MS', 'Morgan Stanley'),
    'visa': ('V', 'Visa Inc.'),
    'mastercard': ('MA', 'Mastercard Inc.'),
    'american express': ('AXP', 'American Express Company'),
    'amex': ('AXP', 'American Express Company'),
    'paypal': ('PYPL', 'PayPal Holdings Inc.'),
    'citigroup': ('C', 'Citigroup Inc.'),
    
    # Healthcare
    'johnson & johnson': ('JNJ', 'Johnson & Johnson'),
    'johnson and johnson': ('JNJ', 'Johnson & Johnson'),
    'pfizer': ('PFE', 'Pfizer Inc.'),
    'moderna': ('MRNA', 'Moderna Inc.'),
    'abbott': ('ABT', 'Abbott Laboratories'),
    'merck': ('MRK', 'Merck & Co. Inc.'),
    'unitedhealth': ('UNH', 'UnitedHealth Group Inc.'),
    'eli lilly': ('LLY', 'Eli Lilly and Company'),
    'bristol myers': ('BMY', 'Bristol-Myers Squibb'),
    
    # Consumer
    'coca cola': ('KO', 'The Coca-Cola Company'),
    'coca-cola': ('KO', 'The Coca-Cola Company'),
    'pepsi': ('PEP', 'PepsiCo Inc.'),
    'pepsico': ('PEP', 'PepsiCo Inc.'),
    'procter & gamble': ('PG', 'Procter & Gamble Co.'),
    'procter and gamble': ('PG', 'Procter & Gamble Co.'),
    'walmart': ('WMT', 'Walmart Inc.'),
    'costco': ('COST', 'Costco Wholesale Corp.'),
    'nike': ('NKE', 'NIKE Inc.'),
    'adidas': ('ADDYY', 'adidas AG'),
    'starbucks': ('SBUX', 'Starbucks Corporation'),
    'mcdonald': ('MCD', 'McDonald\'s Corporation'),
    "mcdonald's": ('MCD', 'McDonald\'s Corporation'),
    'mcdonalds': ('MCD', 'McDonald\'s Corporation'),
    'home depot': ('HD', 'The Home Depot Inc.'),
    'disney': ('DIS', 'The Walt Disney Company'),
    
    # Energy
    'exxon': ('XOM', 'Exxon Mobil Corporation'),
    'exxon mobil': ('XOM', 'Exxon Mobil Corporation'),
    'chevron': ('CVX', 'Chevron Corporation'),
    'conocophillips': ('COP', 'ConocoPhillips'),
    'shell': ('SHEL', 'Shell plc'),
    'totalenergies': ('TTE', 'TotalEnergies SE'),
    'total energies': ('TTE', 'TotalEnergies SE'),
    'total': ('TTE', 'TotalEnergies SE'),
    'bp': ('BP', 'BP plc'),
    
    # French Companies
    'lvmh': ('MC.PA', 'LVMH Moët Hennessy Louis Vuitton'),
    'hermès': ('RMS.PA', 'Hermès International'),
    'hermes': ('RMS.PA', 'Hermès International'),
    'kering': ('KER.PA', 'Kering SA'),
    'l\'oréal': ('OR.PA', 'L\'Oréal SA'),
    'loreal': ('OR.PA', 'L\'Oréal SA'),
    'l\'oreal': ('OR.PA', 'L\'Oréal SA'),
    'dior': ('CDI.PA', 'Christian Dior SE'),
    'airbus': ('AIR.PA', 'Airbus SE'),
    'sanofi': ('SAN.PA', 'Sanofi SA'),
    'bnp paribas': ('BNP.PA', 'BNP Paribas SA'),
    'bnp': ('BNP.PA', 'BNP Paribas SA'),
    'axa': ('CS.PA', 'AXA SA'),
    'schneider': ('SU.PA', 'Schneider Electric SE'),
    'schneider electric': ('SU.PA', 'Schneider Electric SE'),
    'safran': ('SAF.PA', 'Safran SA'),
    'danone': ('BN.PA', 'Danone SA'),
    'stellantis': ('STLA', 'Stellantis N.V.'),
    'peugeot': ('STLA', 'Stellantis N.V. (Peugeot)'),
    'renault': ('RNO.PA', 'Renault SA'),
    'carrefour': ('CA.PA', 'Carrefour SA'),
    'veolia': ('VIE.PA', 'Veolia Environnement SA'),
    'orange': ('ORA.PA', 'Orange SA'),
    'michelin': ('ML.PA', 'Compagnie Générale des Établissements Michelin'),
    'publicis': ('PUB.PA', 'Publicis Groupe SA'),
    'capgemini': ('CAP.PA', 'Capgemini SE'),
    'bouygues': ('EN.PA', 'Bouygues SA'),
    'vinci': ('DG.PA', 'Vinci SA'),
    'saint-gobain': ('SGO.PA', 'Compagnie de Saint-Gobain SA'),
    'saint gobain': ('SGO.PA', 'Compagnie de Saint-Gobain SA'),
    'legrand': ('LR.PA', 'Legrand SA'),
    'essilor': ('EL.PA', 'EssilorLuxottica SA'),
    'essilorluxottica': ('EL.PA', 'EssilorLuxottica SA'),
    
    # Automotive Traditional
    'toyota': ('TM', 'Toyota Motor Corporation'),
    'ford': ('F', 'Ford Motor Company'),
    'general motors': ('GM', 'General Motors Company'),
    'gm': ('GM', 'General Motors Company'),
    'honda': ('HMC', 'Honda Motor Co., Ltd.'),
    'nissan': ('NSANY', 'Nissan Motor Co., Ltd.'),
    
    # Telecom
    'verizon': ('VZ', 'Verizon Communications Inc.'),
    'at&t': ('T', 'AT&T Inc.'),
    'att': ('T', 'AT&T Inc.'),
    't-mobile': ('TMUS', 'T-Mobile US Inc.'),
    'comcast': ('CMCSA', 'Comcast Corporation'),
    
    # Aerospace & Defense
    'boeing': ('BA', 'The Boeing Company'),
    'lockheed martin': ('LMT', 'Lockheed Martin Corporation'),
    'lockheed': ('LMT', 'Lockheed Martin Corporation'),
    'raytheon': ('RTX', 'Raytheon Technologies Corporation'),
    'northrop grumman': ('NOC', 'Northrop Grumman Corporation'),
    
    # Retail & E-commerce
    'alibaba': ('BABA', 'Alibaba Group Holding Limited'),
    'target': ('TGT', 'Target Corporation'),
    'best buy': ('BBY', 'Best Buy Co. Inc.'),
    'ebay': ('EBAY', 'eBay Inc.'),
    'shopify': ('SHOP', 'Shopify Inc.'),
    
    # Food & Beverage
    'nestle': ('NSRGY', 'Nestlé S.A.'),
    'nestlé': ('NSRGY', 'Nestlé S.A.'),
    'unilever': ('UL', 'Unilever PLC'),
    'mondelez': ('MDLZ', 'Mondelez International Inc.'),
    'kraft heinz': ('KHC', 'The Kraft Heinz Company'),
    'general mills': ('GIS', 'General Mills Inc.'),
}

# Index inversé : ticker -> nom
TICKER_TO_NAME = {}
for name, (ticker, full_name) in POPULAR_COMPANIES.items():
    if ticker not in TICKER_TO_NAME:
        TICKER_TO_NAME[ticker] = full_name


def search_local_cache(query: str, limit: int = 5) -> List[Tuple[str, int]]:
    """
    Recherche dans le cache local (entreprises populaires)
    
    Returns:
        Liste de tuples (résultat, score)
    """
    query_lower = query.lower().strip()
    results = []
    seen_tickers = set()
    
    # Match exact sur ticker
    if query.upper() in TICKER_TO_NAME:
        ticker = query.upper()
        return [(f"{ticker} - {TICKER_TO_NAME[ticker]}", 100)]
    
    # Match exact sur nom
    if query_lower in POPULAR_COMPANIES:
        ticker, full_name = POPULAR_COMPANIES[query_lower]
        return [(f"{ticker} - {full_name}", 100)]
    
    # Recherche floue sur les noms
    name_matches = process.extract(
        query_lower,
        POPULAR_COMPANIES.keys(),
        scorer=fuzz.token_sort_ratio,
        limit=limit * 2
    )
    
    for match_name, score in name_matches:
        if score > 60:
            ticker, full_name = POPULAR_COMPANIES[match_name]
            if ticker not in seen_tickers:
                results.append((f"{ticker} - {full_name}", score))
                seen_tickers.add(ticker)
    
    # Recherche floue sur les tickers
    ticker_matches = process.extract(
        query.upper(),
        TICKER_TO_NAME.keys(),
        scorer=fuzz.partial_ratio,
        limit=limit * 2
    )
    
    for match_ticker, score in ticker_matches:
        if score > 60 and match_ticker not in seen_tickers:
            full_name = TICKER_TO_NAME[match_ticker]
            results.append((f"{match_ticker} - {full_name}", score))
            seen_tickers.add(match_ticker)
    
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:limit]


def search_yahoo_api(query: str, limit: int = 5) -> List[str]:
    """
    Recherche via l'API Yahoo Finance (60,000+ entreprises)
    Récupère automatiquement le VRAI nom de l'entreprise
    
    Returns:
        Liste de résultats au format "TICKER - Nom Complet Réel"
    """
    try:
        results = []
        seen_tickers = set()
        
        # Méthode 1 : Essayer le ticker direct
        try:
            ticker_obj = yf.Ticker(query.upper())
            info = ticker_obj.info
            
            if info and 'symbol' in info and info.get('symbol'):
                symbol = info['symbol']
                # Prioriser longName pour avoir le vrai nom complet
                long_name = info.get('longName') or info.get('shortName') or symbol
                
                if symbol not in seen_tickers:
                    results.append(f"{symbol} - {long_name}")
                    seen_tickers.add(symbol)
        except:
            pass
        
        # Méthode 2 : Recherche via différentes variantes
        variants = [
            query.upper(),           # FERRARI
            query.lower(),           # ferrari  
            query.capitalize(),      # Ferrari
            query.upper() + ".MI",   # Pour les actions italiennes
            query.upper() + ".PA",   # Pour les actions françaises
        ]
        
        for variant in variants:
            if len(results) >= limit:
                break
                
            try:
                ticker_obj = yf.Ticker(variant)
                info = ticker_obj.info
                
                if info and 'symbol' in info and info.get('symbol'):
                    symbol = info['symbol']
                    
                    # Extraire le VRAI nom de l'entreprise
                    long_name = info.get('longName')
                    if not long_name:
                        long_name = info.get('shortName')
                    if not long_name:
                        long_name = info.get('name')
                    if not long_name:
                        long_name = symbol
                    
                    # Éviter les doublons
                    if symbol not in seen_tickers and len(long_name) > 1:
                        results.append(f"{symbol} - {long_name}")
                        seen_tickers.add(symbol)
            except:
                continue
        
        return results[:limit]
    
    except Exception as e:
        return []


def smart_search(query: str, limit: int = 8) -> List[str]:
    """
    Recherche HYBRIDE intelligente
    
    Niveau 1 : Cache local (instantané, entreprises populaires)
    Niveau 2 : API Yahoo Finance (60,000+ entreprises mondiales)
    
    Args:
        query: Texte de recherche
        limit: Nombre de résultats max
        
    Returns:
        Liste de suggestions au format "TICKER - Nom complet"
    """
    if not query or len(query) < 1:
        # Retourner les entreprises les plus populaires par défaut
        return [
            "AAPL - Apple Inc.",
            "GOOGL - Alphabet Inc. (Google)",
            "MSFT - Microsoft Corporation",
            "NVDA - NVIDIA Corporation",
            "TSLA - Tesla Inc.",
            "AMZN - Amazon.com Inc.",
            "META - Meta Platforms Inc.",
            "NFLX - Netflix Inc."
        ]
    
    # NIVEAU 1 : Recherche dans le cache local
    local_results = search_local_cache(query, limit=limit)
    
    # Si on a un excellent match local (score > 85), on retourne direct
    if local_results and local_results[0][1] > 85:
        return [result[0] for result in local_results]
    
    # NIVEAU 2 : Recherche via API Yahoo si pas de bon match local
    yahoo_results = search_yahoo_api(query, limit=5)
    
    # Combiner les résultats (local + Yahoo)
    combined = []
    seen = set()
    
    # Ajouter les résultats locaux
    for result, score in local_results:
        ticker = result.split(" - ")[0]
        if ticker not in seen:
            combined.append(result)
            seen.add(ticker)
    
    # Ajouter les résultats Yahoo
    for result in yahoo_results:
        ticker = result.split(" - ")[0]
        if ticker not in seen:
            combined.append(result)
            seen.add(ticker)
    
    # Si on n'a rien trouvé, retourner un message
    if not combined:
        # Essayer une recherche plus permissive
        permissive_local = search_local_cache(query, limit=limit)
        if permissive_local:
            return [result[0] for result in permissive_local]
        return [f"❌ Aucune entreprise trouvée pour '{query}'"]
    
    return combined[:limit]


def extract_ticker(selection: str) -> str:
    """
    Extrait le ticker d'une sélection au format "TICKER - Nom"
    
    Args:
        selection: Texte sélectionné
        
    Returns:
        Le ticker extrait
    """
    if not selection:
        return ""
    
    # Si c'est un message d'erreur
    if "❌" in selection or "Aucune" in selection:
        return ""
    
    # Si c'est juste un ticker (pas de " - ")
    if " - " not in selection:
        return selection.strip().upper()
    
    # Extraire la partie avant " - "
    ticker = selection.split(" - ")[0].strip()
    return ticker


# Pour tester le module
if __name__ == "__main__":
    print("🔍 Test de recherche HYBRIDE intelligente:\n")
    
    print("=" * 60)
    print("TEST 1 : Entreprises populaires (cache local - instantané)")
    print("=" * 60)
    
    tests_local = ["appl", "microsft", "goog", "tesla", "lvmh"]
    for test in tests_local:
        print(f"\n🔎 Recherche '{test}':")
        results = smart_search(test, limit=3)
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r}")
    
    print("\n" + "=" * 60)
    print("TEST 2 : Entreprises rares (API Yahoo)")
    print("=" * 60)
    
    tests_yahoo = ["Nintendo", "Samsung", "Sony", "Alibaba", "Tencent"]
    for test in tests_yahoo:
        print(f"\n🔎 Recherche '{test}':")
        results = smart_search(test, limit=3)
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r}")
    
    print("\n" + "=" * 60)
    print("✅ Tests terminés !")
    print("=" * 60)
