import streamlit as st
import requests
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Rederiets Fondradar", layout="wide")
st.title("⚓ HANSSONS Rederi - Mekanisk Innehavsanalys")

# Mekaniskt lexikon: Översätter Avanzas aktienamn till Yahoo-tickers för stora svenska bolag
TICKER_MAP = {
    "Investor B": "INVE-B.ST",
    "Investor A": "INVE-A.ST",
    "Atlas Copco A": "ATCO-A.ST",
    "Atlas Copco B": "ATCO-B.ST",
    "Volvo B": "VOLV-B.ST",
    "Assa Abloy B": "ASSA-B.ST",
    "SEB A": "SEB-A.ST",
    "Swedbank A": "SWEDA.ST",
    "Handelsbanken A": "SHB-A.ST",
    "Hexagon B": "HEXA-B.ST",
    "Sandvik": "SAND.ST",
    "Evolution": "EVO.ST",
    "Industrivärden C": "INDU-C.ST",
    "Essity B": "ESSITY-B.ST",
    "Nibe Industrier B": "NIBE-B.ST",
    "AstraZeneca": "AZN.ST"
}

def get_avanza_fund_holdings(fund_id):
    """Hämtar fondens innehav mekaniskt via Avanzas publika API."""
    url = f"https://www.avanza.se/_api/fund-guide/guide/{fund_id}"
    headers = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X)'}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Plockar ut holdingList om den finns
            return data.get('holdingChartData', [])
        else:
            return None
    except Exception:
        return None

def calculate_ma200(ticker):
    """Hämtar kurs och MA200 från Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if hist.empty or len(hist) < 200:
            return None, None
        
        current_price = hist['Close'].iloc[-1]
        ma200 = hist['Close'].rolling(window=200).mean().iloc[-1]
        return round(current_price, 2), round(ma200, 2)
    except Exception:
        return None, None

# --- GRÄNSSNITT PÅ IPAD ---
st.sidebar.header("Navigering")
fund_id = st.sidebar.text_input("Mata in fondens Avanza-ID (ex. 41567 för Spiltan):")

if st.sidebar.button("Kör Analys") and fund_id:
    with st.spinner("Ansluter till Avanza och korskopplar med Yahoo Finance..."):
        holdings = get_avanza_fund_holdings(fund_id)
        
        if holdings:
            results = []
            
            for item in holdings:
                name = item.get('name')
                weight = item.get('y', 0) # Avanza anger ofta vikten som 'y' i chart-data
                
                # Styrmannens regel: Exakt 5% eller högre
                if weight >= 5.0:
                    ticker = TICKER_MAP.get(name)
                    
                    if ticker:
                        price, ma200 = calculate_ma200(ticker)
                        if price and ma200:
                            status = "🟢 Över MA200" if price >= ma200 else "🔴 Under MA200"
                       else:
    status = "⚠️ Data saknas"
    price = "-"
    ma200 = "-"
                    else:
                        ticker = "Saknas i lexikon"
                        status = "⚠️ Manuell kontroll krävs"
                        price, ma200 = "-", "-"
                        
                    results.append({
                        "Aktie": name,
                        "Vikt (%)": round(weight, 2),
                        "Ticker": ticker,
                        "Aktuell Kurs": price,
                        "MA200": ma200,
                        "Styrmannens Signal": status
                    })
            
            if results:
                st.subheader(f"Innehav > 5% och deras relation till MA200")
                st.dataframe(pd.DataFrame(results), use_container_width=True)
            else:
                st.info("Inga innehav över 5% hittades i denna fond.")
        else:
            st.error("Kunde inte hämta data. Kontrollera ID eller Avanzas anslutning.")
