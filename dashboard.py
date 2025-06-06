import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
import pandas as pd
from alpaca_trade_api.rest import REST

# ==========================
# Alpaca API Configuration
# ==========================
ALPACA_API_KEY = "PKVONEK0SQQ01ASXQM3C"
ALPACA_SECRET_KEY = "I7aLdtaHNXcz69vKDJPWVgw8RdgRs6yUzTBVGzBt"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

alpaca_api = REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL, api_version='v2')

# ==========================
# Load S&P 500 List
# ==========================
@st.cache_data
def load_sp500():
    df = pd.read_excel("sp500_stocks.xlsx")
    return dict(zip(df['Symbol'], df['Name']))

# ==========================
# Main Streamlit App
# ==========================
def main():
    st.set_page_config(page_title="S&P 500 Dashboard", layout="wide")
    st.title("📊 S&P 500 Stock Dashboard")

    sp500 = load_sp500()

    stock_selection = st.selectbox("Choose a Stock", list(sp500.keys()),
                                   format_func=lambda x: f"{x} - {sp500[x]}")

    stock = yf.Ticker(stock_selection)

    # === Fetch Data with Fallbacks ===
    try:
        fast_info = stock.fast_info
    except:
        fast_info = {}

    try:
        stock_info = stock.get_info()
    except:
        stock_info = {}

    if not fast_info:
        st.error("Failed to fetch price/volume info. Please try another stock.")
        return

    # ==========================
    # Overview
    # ==========================
    st.markdown("## 🏛️ Company Overview")
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader(stock_info.get("longName", stock_selection))
        st.write("**Sector:**", stock_info.get("sector", "N/A"))
        st.write("**Industry:**", stock_info.get("industry", "N/A"))

        market_cap = fast_info.get('market_cap', 'N/A')
        if isinstance(market_cap, (int, float)):
            market_cap = f"{market_cap:,}"
        st.write("**Market Cap:**", market_cap)

        st.write("**52W High / Low:**", fast_info.get("year_high", "N/A"), "/", fast_info.get("year_low", "N/A"))
        st.write("**Volume:**", fast_info.get("last_volume", "N/A"))

    with col2:
        st.subheader("📈 Price Chart")
        try:
            hist = stock.history(period="1y")
            fig = go.Figure(data=[go.Candlestick(
                x=hist.index,
                open=hist['Open'],
                high=hist['High'],
                low=hist['Low'],
                close=hist['Close']
            )])
            fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.warning("Price chart not available.")

    # ==========================
    # Description
    # ==========================
    st.markdown("### 📝 Business Description")
    st.write(stock_info.get("longBusinessSummary", "Description not available."))

    # ==========================
    # Financials (Vertically Oriented)
    # ==========================
    st.markdown("## 📑 Financial Statements")

    def show_financial(df, label):
        try:
            st.subheader(label)
            st.dataframe(df.style.format("{:,.0f}"))
        except:
            st.write(f"{label} not available.")

    show_financial(stock.financials, "📈 Income Statement")
    show_financial(stock.balance_sheet, "📊 Balance Sheet")
    show_financial(stock.cashflow, "💵 Cash Flow")

    # ==========================
    # Valuation Metrics
    # ==========================
    st.markdown("## 📊 Valuation Multiples")
    try:
        valuation = {
            "P/E Ratio": stock_info.get("trailingPE", "N/A"),
            "Forward P/E": stock_info.get("forwardPE", "N/A"),
            "P/S Ratio": stock_info.get("priceToSalesTrailing12Months", "N/A"),
            "P/B Ratio": stock_info.get("priceToBook", "N/A"),
            "EV/Revenue": stock_info.get("enterpriseToRevenue", "N/A"),
            "EV/EBITDA": stock_info.get("enterpriseToEbitda", "N/A")
        }
        st.table(pd.DataFrame(list(valuation.items()), columns=["Metric", "Value"]))
    except:
        st.warning("Valuation data unavailable.")

    # ==========================
    # Ownership
    # ==========================
    st.markdown("## 🏢 Ownership Information")
    try:
        st.markdown("### Major Holders")
        st.table(stock.major_holders)
    except:
        st.write("Major holders data not available.")

    try:
        st.markdown("### Institutional Holders")
        if stock.institutional_holders is not None:
            st.dataframe(stock.institutional_holders)
        else:
            st.write("No institutional holders data.")
    except:
        st.write("Institutional holders data not available.")

    # ==========================
    # Trade via Alpaca
    # ==========================
    st.markdown("## 💸 Trade with Alpaca (Paper Trading)")
    qty = st.number_input("Enter number of shares", min_value=1, step=1)
    action = st.radio("Action", ["Buy", "Sell"])

    if st.button(f"{action} Stock"):
        try:
            order = alpaca_api.submit_order(
                symbol=stock_selection,
                qty=qty,
                side=action.lower(),
                type="market",
                time_in_force="gtc"
            )
            st.success(f"{action} order placed for {qty} shares of {stock_selection}")
            st.write(order)
        except Exception as e:
            st.error(f"Order failed: {e}")

# ==========================
# Run App
# ==========================
if __name__ == "__main__":
    main()
