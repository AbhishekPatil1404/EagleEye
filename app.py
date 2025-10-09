import streamlit as st
import pandas as pd
import requests

# --- Trade Analysis Section ---
def analyze_trades(uploaded_file):
    df = pd.read_excel(uploaded_file, sheet_name=0, header=None)

    start_idx = df.index[df[0].astype(str).str.contains('Positions', case=False, na=False)].tolist()
    end_idx = df.index[df[0].astype(str).str.contains('Orders', case=False, na=False)].tolist()

    if start_idx:
        start = start_idx[0] + 1
        end = end_idx[0] if end_idx else len(df)
        positions_raw = df.iloc[start:end]
    else:
        st.error("Could not find 'Positions' section in the file.")
        return None

    positions_raw = positions_raw.dropna(how='all')
    positions_raw.columns = positions_raw.iloc[0]
    positions_df = positions_raw[1:].reset_index(drop=True)

    positions_df = positions_df.rename(columns={
        'Time': 'Open Time',
        'Price': 'Open Price'
    })
    positions_df.columns.values[8] = 'Close Time'
    positions_df.columns.values[9] = 'Close Price'

    positions_df['Open Time'] = pd.to_datetime(positions_df['Open Time'], format='%Y.%m.%d %H:%M:%S', errors='coerce')
    positions_df['Close Time'] = pd.to_datetime(positions_df['Close Time'], format='%Y.%m.%d %H:%M:%S', errors='coerce')
    positions_df['Hold_Time'] = positions_df['Close Time'] - positions_df['Open Time']

    short_hold_df = positions_df[positions_df['Hold_Time'] <= pd.Timedelta(minutes=3)]

    return {
        "total_positions": len(positions_df),
        "total_profit": positions_df['Profit'].sum(),
        "short_hold_count": len(short_hold_df),
        "short_hold_profit": short_hold_df['Profit'].sum(),
        "short_hold_df": short_hold_df
    }

# --- IP Lookup Section ---
def get_ip_details(ip_address):
    try:
        response = requests.get(f'https://ipinfo.io/{ip_address}/json')
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# --- Streamlit UI ---
st.title("📊 Trade Analyzer & 🌐 IP Lookup Tool")

# Tabs for separation
tab1, tab2 = st.tabs(["Trade Analysis", "IP Address Lookup"])

with tab1:
    st.header("Upload Trade Report")
    uploaded_file = st.file_uploader("Choose Excel file", type=["xlsx"])
    if uploaded_file:
        result = analyze_trades(uploaded_file)
        if result:
            st.metric("Total Positions", result["total_positions"])
            st.metric("Total Profit", f"{result['total_profit']:.2f}")
            st.metric("Trades Closed < 3 min", result["short_hold_count"])
            st.metric("Profit from Short Holds", f"{result['short_hold_profit']:.2f}")
            st.subheader("Short Hold Trades")
            st.dataframe(result["short_hold_df"])

with tab2:
    st.header("Enter IP Addresses")
    ip_input = st.text_area("Enter IPs separated by commas", "8.8.8.8, 1.1.1.1")
    if st.button("Lookup IPs"):
        ip_list = [ip.strip() for ip in ip_input.split(',') if ip.strip()]
        for ip in ip_list:
            st.subheader(f"Details for {ip}")
            details = get_ip_details(ip)
            if "error" in details:
                st.error(details["error"])
            else:
                for key, value in details.items():
                    st.write(f"**{key.capitalize()}**: {value}")
