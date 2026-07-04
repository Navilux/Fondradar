import streamlit as st
import requests
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Rederiets Fondradar", layout="wide")
st.title("⚓ HANSSONS Rederi - Mekanisk Innehavsanalys")

# Mekaniskt lexikon (Aktier)
# Mekaniskt lexikon (Aktier)
TICKER_MAP = {
    "Investor B": "INVE-B.ST",
    "Investor A": "INVE-A.ST",
    "Atlas Copco A": "ATCO-A.ST",
    "Atlas Copco B": "ATCO-B.ST",
    "Volvo B": "VOLV-B.ST",
    "Assa Abloy B": "ASSA-B.ST",
    "SEB A": "SEB-A.ST",
    "Swedbank A": "SWED-A.ST", # Rättad ticker
    "Handelsbanken A": "SHB-A.ST",
    "Nordea Bank": "NDA-SE.ST", # Tillagd
    "Hexagon B": "HEXA-B.ST",
    "Sandvik": "SAND.ST",
    "Evolution": "EVO.ST",
    "Industrivärden C": "INDU-C.ST",
    "Essity B": "ESSITY-B.ST",
    "Nibe Industrier B": "NIBE-B.ST",
    "AstraZeneca": "AZN.ST",
    "Ericsson B": "ERIC-B.ST",
    "Saab-B": "SAAB-B.ST",
   "TRATON SE": "8TRA.ST",
    "Traton": "8TRA.ST",
    "SKF B": "SKF-B.ST", # Tillagd
    "Autoliv 0%": "ALIV-SDB.ST", # Tillagd (med Avanzas specifika syntax)
    "Autoliv": "ALIV-SDB.ST",
    "Hennes & Mauritz B": "HM-B.ST",
    "Epiroc A": "EPI-A.ST",
    "Epiroc B": "EPI-B.ST",
    "Alfa Laval": "ALFA.ST",
    "Boliden": "BOL.ST",
    "SCA B": "SCA-B.ST",
    "Skanska B": "SKA-B.ST",
    "Tele2 B": "TEL2-B.ST",
    "Telia Company": "TELIA.ST",
    "EQT": "EQT.ST",
    "EQT AB": "EQT.ST",
    "ABB": "ABB.ST",
    "ABB Ltd": "ABB.ST",
    "Lundberg B": "LUND-B.ST",
    "Lundbergföretagen B": "LUND-B.ST",
    "L E Lundbergföretagen B": "LUND-B.ST",
    "LIFCO": "LIFCO-B.ST",
    "Lifco B": "LIFCO-B.ST",
    "Hennes & Mauritz B": "HM-B.ST",
    "Hennes & Mauritz": "HM-B.ST",
    "H&M B": "HM-B.ST",
    "H & M Hennes & Mauritz B": "HM-B.ST",
    "Lifco": "LIFCO-B.ST"
}

# Mekaniskt lexikon (Rullgardinsmeny för fonder)
FUND_MENU = {
    "Avanza Zero": "41567",
    "SEB Swedish Value": "87987",
    "Avanza Sweden": "2480007",
    "Spiltan Aktiefond Investmentbolag": "325406",
    "PLUS Allabolag Sverige Index": "1151293",
    "AMF Aktiefond Sverige": "1949",
    "Mata in manuellt ID...": "CUSTOM"
}

def get_avanza_fund_data(fund_id):
    """Hämtar all fonddata mekaniskt via Avanzas publika API."""
    url = f"https://www.avanza.se/_api/fund-guide/guide/{fund_id}"
    headers = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X)'}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
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

# Skapar rullgardinsmenyn
selected_fund_name = st.sidebar.selectbox("Välj fond i listan:", list(FUND_MENU.keys()))

# Om Kapten väljer manuell inmatning, visa textfältet
if FUND_MENU[selected_fund_name] == "CUSTOM":
    fund_id = st.sidebar.text_input("Mata in fondens unika Avanza-ID:")
else:
    fund_id = FUND_MENU[selected_fund_name]

if st.sidebar.button("Kör Analys") and fund_id:
    with st.spinner("Ansluter till Avanza och beräknar MA200..."):
        fund_data = get_avanza_fund_data(fund_id)
        
        if fund_data:
            # Extraherar och skriver ut fondens officiella namn från Avanza
            actual_fund_name = fund_data.get('name', 'Okänd Fond')
            st.subheader(f"📊 Resultat för: {actual_fund_name}")
            st.markdown("Innehav **≥ 3%** och deras relation till **MA200**")
            
            holdings = fund_data.get('holdingChartData', [])
            results = []
            
            for item in holdings:
                name = item.get('name')
                weight = item.get('y', 0)
                
                if weight >= 3.0:
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
                        price = "-"
                        ma200 = "-"
                        
                    results.append({
                        "Aktie": name,
                        "Vikt (%)": round(weight, 2),
                        "Ticker": ticker,
                        "Aktuell Kurs": price,
                        "MA200": ma200,
                        "Styrmannens Signal": status
                    })
            
            if results:
                st.dataframe(pd.DataFrame(results), use_container_width=True)
            else:
                st.info("Inga innehav över 3% hittades i denna fond.")
        else:
            st.error("Kunde inte hämta data. Kontrollera ID eller Avanzas anslutning.")
            st.error("Kunde inte hämta data. Kontrollera ID eller Avanzas anslutning.")
