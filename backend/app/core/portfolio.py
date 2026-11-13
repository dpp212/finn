# 20 portfolio companies + 5 extras for ad-hoc research
# engine works for any NSE ticker, this is just the demo set

PORTFOLIO = [
    {"ticker": "TCS.NS",            "name": "TCS",                   "sector": "IT"},
    {"ticker": "INFY.NS",           "name": "Infosys",               "sector": "IT"},
    {"ticker": "PERSISTENT.NS",     "name": "Persistent Systems",    "sector": "IT"},
    {"ticker": "HDFCBANK.NS",       "name": "HDFC Bank",             "sector": "Banking"},
    {"ticker": "ICICIBANK.NS",      "name": "ICICI Bank",            "sector": "Banking"},
    {"ticker": "KOTAKBANK.NS",      "name": "Kotak Mahindra Bank",   "sector": "Banking"},
    {"ticker": "SUNPHARMA.NS",      "name": "Sun Pharma",            "sector": "Pharma"},
    {"ticker": "DIVISLAB.NS",       "name": "Divi's Labs",           "sector": "Pharma"},
    {"ticker": "TATAMOTORS.NS",     "name": "Tata Motors",           "sector": "Auto"},
    {"ticker": "BAJAJ-AUTO.NS",     "name": "Bajaj Auto",            "sector": "Auto"},
    {"ticker": "HINDUNILVR.NS",     "name": "Hindustan Unilever",    "sector": "Consumer"},
    {"ticker": "TITAN.NS",          "name": "Titan",                 "sector": "Consumer"},
    {"ticker": "RELIANCE.NS",       "name": "Reliance Industries",   "sector": "Energy"},
    {"ticker": "NTPC.NS",           "name": "NTPC",                  "sector": "Energy"},
    {"ticker": "LT.NS",             "name": "L&T",                   "sector": "Industrials"},
    {"ticker": "BEL.NS",            "name": "Bharat Electronics",    "sector": "Industrials"},
    {"ticker": "SRF.NS",            "name": "SRF",                   "sector": "Chemicals"},
    {"ticker": "PIDILITIND.NS",     "name": "Pidilite Industries",   "sector": "Chemicals"},
    {"ticker": "BAJFINANCE.NS",     "name": "Bajaj Finance",         "sector": "NBFC"},
    {"ticker": "BHARTIARTL.NS",     "name": "Bharti Airtel",         "sector": "Telecom"},
]

ADHOC_COMPANIES = [
    {"ticker": "ZOMATO.NS",         "name": "Zomato",                "sector": "Internet"},
    {"ticker": "TRENT.NS",          "name": "Trent",                 "sector": "Retail"},
    {"ticker": "DIXON.NS",          "name": "Dixon Technologies",    "sector": "Electronics"},
    {"ticker": "DEEPAKNTR.NS",      "name": "Deepak Nitrite",        "sector": "Chemicals"},
    {"ticker": "CDSL.NS",           "name": "CDSL",                  "sector": "Capital Markets"},
]

ALL_COMPANIES = PORTFOLIO + ADHOC_COMPANIES

ANNOUNCEMENT_CATEGORIES = [
    "results", "m_and_a", "fund_raise", "management_change",
    "litigation", "insider_trading", "earnings_call", "investor_meetings",
    "credit_rating", "dividend", "bonus_split", "capex",
    "press_release", "postal_ballot", "agm_egm", "pledging", "unclassified"
]

HIGH_PRIORITY = ["results", "m_and_a", "management_change", "litigation", "fund_raise"]
MEDIUM_PRIORITY = ["insider_trading", "earnings_call", "credit_rating", "dividend", "capex"]
LOW_PRIORITY = ["investor_meetings", "bonus_split", "press_release", "postal_ballot", "agm_egm", "pledging", "unclassified"]


def get_ticker_map():
    return {c["name"].lower(): c["ticker"] for c in ALL_COMPANIES}

def get_portfolio_tickers():
    return [c["ticker"] for c in PORTFOLIO]

def get_all_tickers():
    return [c["ticker"] for c in ALL_COMPANIES]
