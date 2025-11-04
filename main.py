

import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.express as px

# --- Page Configuration ---
st.set_page_config(page_title="Trade Analyzer & IP Lookup", page_icon="📊", layout="wide")

# --- Initialize Session State ---
if 'ip_history' not in st.session_state:
    st.session_state.ip_history = []


def analyze_trades(uploaded_file):
    """Analyze trading positions from Excel file"""
    try:
        df = pd.read_excel(uploaded_file, sheet_name=0, header=None)

        # --- Find Positions section ---
        start_idx = df.index[df[0].astype(str).str.contains('Positions', case=False, na=False)].tolist()
        end_idx = df.index[df[0].astype(str).str.contains('Orders', case=False, na=False)].tolist()

        if not start_idx:
            st.error("Could not find 'Positions' section in the file.")
            return None

        start = start_idx[0] + 1
        end = end_idx[0] if end_idx else len(df)
        positions_raw = df.iloc[start:end]

        positions_raw = positions_raw.dropna(how='all')
        positions_raw.columns = positions_raw.iloc[0]
        positions_df = positions_raw[1:].reset_index(drop=True)

        # --- Rename key columns ---
        positions_df = positions_df.rename(columns={
            'Time': 'Open Time',
            'Price': 'Open Price'
        })
        positions_df.columns.values[8] = 'Close Time'
        positions_df.columns.values[9] = 'Close Price'

        # --- Convert datetime (supporting milliseconds) ---
        positions_df['Open Time'] = pd.to_datetime(
            positions_df['Open Time'], format='%Y.%m.%d %H:%M:%S.%f', errors='coerce'
        ).fillna(pd.to_datetime(positions_df['Open Time'], format='%Y.%m.%d %H:%M:%S', errors='coerce'))
        positions_df['Close Time'] = pd.to_datetime(
            positions_df['Close Time'], format='%Y.%m.%d %H:%M:%S.%f', errors='coerce'
        ).fillna(pd.to_datetime(positions_df['Close Time'], format='%Y.%m.%d %H:%M:%S', errors='coerce'))

        positions_df['Hold_Time'] = positions_df['Close Time'] - positions_df['Open Time']
        positions_df['Profit'] = pd.to_numeric(positions_df['Profit'], errors='coerce')

        # --- Identify scalping trades (< 3 minutes) ---
        scalping_df = positions_df[positions_df['Hold_Time'] <= pd.Timedelta(minutes=3)]

        # --- Identify reversal trades ---
        positions_df = positions_df.sort_values(by='Open Time').reset_index(drop=True)
        positions_df['Reversal'] = False
        for i in range(1, len(positions_df)):
            prev_close = positions_df.loc[i - 1, 'Close Time']
            curr_open = positions_df.loc[i, 'Open Time']
            prev_type = str(positions_df.loc[i - 1, 'Type']).strip().lower()
            curr_type = str(positions_df.loc[i, 'Type']).strip().lower()
            prev_symbol = str(positions_df.loc[i - 1, 'Symbol']).strip().upper()
            curr_symbol = str(positions_df.loc[i, 'Symbol']).strip().upper()

            if pd.notnull(prev_close) and pd.notnull(curr_open) and prev_symbol == curr_symbol:
                time_diff = abs((curr_open - prev_close).total_seconds())
                if time_diff <= 20 and (
                    (prev_type == 'buy' and curr_type == 'sell') or
                    (prev_type == 'sell' and curr_type == 'buy')
                ):
                    positions_df.loc[i, 'Reversal'] = True

        reversal_df = positions_df[positions_df['Reversal']]
        reversal_count = len(reversal_df)
        reversal_profit = reversal_df['Profit'].sum()

        # --- Identify burst trades (2 or more within 2 seconds) ---
        positions_df['Burst'] = False
        burst_groups = []
        current_group = [0]

        for i in range(1, len(positions_df)):
            prev_open = positions_df.loc[i - 1, 'Open Time']
            curr_open = positions_df.loc[i, 'Open Time']

            if pd.notnull(prev_open) and pd.notnull(curr_open):
                time_diff = abs((curr_open - prev_open).total_seconds())
                if time_diff <= 2:
                    current_group.append(i)
                else:
                    if len(current_group) >= 2:
                        burst_groups.append(current_group)
                    current_group = [i]

        if len(current_group) >= 2:
            burst_groups.append(current_group)

        for group in burst_groups:
            positions_df.loc[group, 'Burst'] = True

        burst_df = positions_df[positions_df['Burst']]
        burst_count = len(burst_df)
        burst_profit = burst_df['Profit'].sum()

        # --- Statistics ---
        total_positions = len(positions_df)
        total_profit = positions_df['Profit'].sum()
        scalping_count = len(scalping_df)
        scalping_profit = scalping_df['Profit'].sum()

        scalping_percentage = (scalping_count / total_positions * 100) if total_positions > 0 else 0
        reversal_percentage = (reversal_count / total_positions * 100) if total_positions > 0 else 0
        burst_percentage = (burst_count / total_positions * 100) if total_positions > 0 else 0

        scalping_profit_percentage = (scalping_profit / total_profit * 100) if total_profit != 0 else 0
        reversal_profit_percentage = (reversal_profit / total_profit * 100) if total_profit != 0 else 0
        burst_profit_percentage = (burst_profit / total_profit * 100) if total_profit != 0 else 0

        avg_hold_time = positions_df['Hold_Time'].mean()
        avg_scalping_hold_time = scalping_df['Hold_Time'].mean() if len(scalping_df) > 0 else pd.Timedelta(0)

        # --- Return structured results ---
        return {
            "total_positions": total_positions,
            "total_profit": total_profit,
            "scalping_count": scalping_count,
            "scalping_profit": scalping_profit,
            "scalping_percentage": scalping_percentage,
            "scalping_profit_percentage": scalping_profit_percentage,
            "reversal_count": reversal_count,
            "reversal_profit": reversal_profit,
            "reversal_percentage": reversal_percentage,
            "reversal_profit_percentage": reversal_profit_percentage,
            "burst_count": burst_count,
            "burst_profit": burst_profit,
            "burst_percentage": burst_percentage,
            "burst_profit_percentage": burst_profit_percentage,
            "avg_hold_time": avg_hold_time,
            "avg_scalping_hold_time": avg_scalping_hold_time,
            "scalping_df": scalping_df,
            "reversal_df": reversal_df,
            "burst_df": burst_df,
            "all_positions_df": positions_df
        }

    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None



# --- IP Lookup Helpers ---
def get_ip_details(ip_address):
    try:
        response = requests.get(f'https://ipinfo.io/{ip_address}/json', timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def add_ip_to_history(ip, details):
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = {"timestamp": timestamp, "ip": ip, "details": details}
    st.session_state.ip_history.insert(0, entry)
    if len(st.session_state.ip_history) > 10:
        st.session_state.ip_history = st.session_state.ip_history[:10]


# --- Main UI ---
st.title("📊 Trade Analyzer & 🌐 IP Lookup Tool")
st.markdown("---")

# --- Trade Analysis Section ---
st.header("📈 Trade Analysis")

uploaded_file = st.file_uploader("Upload Excel Trade Report", type=["xlsx"], key="trade_file")

if uploaded_file:
    with st.spinner("Analyzing trades..."):
        result = analyze_trades(uploaded_file)

    if result:
        st.subheader("📊 Overall Statistics")
        metric_cols = st.columns(4)
        with metric_cols[0]:
            st.metric("Total Trades", result["total_positions"])
        with metric_cols[1]:
            st.metric("Total Profit", f"${result['total_profit']:.2f}")
        with metric_cols[2]:
            st.metric("Avg Hold Time", str(result["avg_hold_time"]).split('.')[0])
        with metric_cols[3]:
            st.metric("Profit/Trade", f"${result['total_profit'] / result['total_positions']:.2f}" if result['total_positions'] > 0 else "$0.00")

        # --- Scalping Stats ---
        st.subheader("⚡ Scalping Statistics (<3 min holds)")
        scalp_cols = st.columns(4)
        with scalp_cols[0]:
            st.metric("Scalping Trades", result["scalping_count"], delta=f"{result['scalping_percentage']:.1f}% of total")
        with scalp_cols[1]:
            st.metric("Scalping Profit", f"${result['scalping_profit']:.2f}", delta=f"{result['scalping_profit_percentage']:.1f}% of total profit")
        with scalp_cols[2]:
            st.metric("Scalping Win Rate", f"{(result['scalping_df']['Profit'] > 0).sum() / len(result['scalping_df']) * 100:.1f}%" if len(result['scalping_df']) > 0 else "N/A")
        with scalp_cols[3]:
            st.metric("Avg Scalp Time", str(result["avg_scalping_hold_time"]).split('.')[0] if result["scalping_count"] > 0 else "N/A")

        # --- Reversal Stats ---
        st.subheader("🔁 Reversal Trade Statistics (Opposite Type within 20s)")
        rev_cols = st.columns(4)
        with rev_cols[0]:
            st.metric("Reversal Trades", result["reversal_count"], delta=f"{result['reversal_percentage']:.1f}% of total")
        with rev_cols[1]:
            st.metric("Reversal Profit", f"${result['reversal_profit']:.2f}", delta=f"{result['reversal_profit_percentage']:.1f}% of total profit")
        with rev_cols[2]:
            st.metric("Reversal Win Rate", f"{(result['reversal_df']['Profit'] > 0).sum() / len(result['reversal_df']) * 100:.1f}%" if len(result['reversal_df']) > 0 else "N/A")
        with rev_cols[3]:
            st.metric("Avg Reversal Profit", f"${result['reversal_df']['Profit'].mean():.2f}" if len(result['reversal_df']) > 0 else "N/A")

        # --- Pie Chart ---
        st.markdown("### 🥧 Trade Type Distribution")
        scalp = result["scalping_count"]
        rev = result["reversal_count"]
        others = result["total_positions"] - (scalp + rev)

        pie_data = pd.DataFrame({
            'Category': ['Scalping Trades', 'Reversal Trades', 'Other Trades'],
            'Count': [scalp, rev, others]
        })

        fig = px.pie(pie_data, names='Category', values='Count',
                     color='Category',
                     color_discrete_sequence=['#FFA500', '#00BFFF', '#90EE90'])
        fig.update_traces(textinfo='percent+label', textposition='inside', pull=[0.05, 0.05, 0])
        fig.update_layout(height=350, width=350, margin=dict(t=40, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

        # --- Copyable Client Report ---
        st.subheader("📝 Copyable Client Report")

        # Calculate values safely before formatting
        profit_per_trade = (result['total_profit'] / result['total_positions']) if result[
                                                                                       'total_positions'] > 0 else 0.0
        scalping_win_rate = ((result['scalping_df']['Profit'] > 0).sum() / len(result['scalping_df']) * 100) if len(
            result['scalping_df']) > 0 else 0.0
        reversal_win_rate = ((result['reversal_df']['Profit'] > 0).sum() / len(result['reversal_df']) * 100) if len(
            result['reversal_df']) > 0 else 0.0
        avg_reversal_profit = result['reversal_df']['Profit'].mean() if len(result['reversal_df']) > 0 else 0.0

        client_report = f"""
       📊 **Trade Analysis Report*

       *Overall Statistics*
       - Total Trades: {result['total_positions']}
       - Total Profit: ${result['total_profit']:.2f}
       - Average Hold Time: {str(result['avg_hold_time']).split('.')[0]}
       - Profit per Trade: ${profit_per_trade:.2f}

       *Scalping Statistics (< 3 min holds)*
       - Scalping Trades: {result['scalping_count']} ({result['scalping_percentage']:.1f}% of total)
       - Scalping Profit: ${result['scalping_profit']:.2f} ({result['scalping_profit_percentage']:.1f}% of total profit)
       - Scalping Win Rate: {scalping_win_rate:.1f}%
       - Average Scalping Hold Time: {str(result['avg_scalping_hold_time']).split('.')[0]}

       **Reversal Trades (Opposite Type within 20s)*
       - Reversal Trades: {result['reversal_count']} ({result['reversal_percentage']:.1f}% of total)
       - Reversal Profit: ${result['reversal_profit']:.2f} ({result['reversal_profit_percentage']:.1f}% of total profit)
       - Reversal Win Rate: {reversal_win_rate:.1f}%
       - Average Reversal Profit: ${avg_reversal_profit:.2f}

       *Trade Type Distribution*
       - Scalping: {result['scalping_count']}
       - Reversal: {result['reversal_count']}
       - Others: {result['total_positions'] - (result['scalping_count'] + result['reversal_count'])}

       *Report generated automatically via EagleEye Trade Analyzer*
       """

        st.text_area(
            "📋 Copy & Share Report",
            value=client_report.strip(),
            height=400,
            key="client_report",
        )


else:
    st.info("👆 Upload an Excel file to analyze your trades")

st.markdown("---")


# --- 🌐 IP Lookup Section (Modern Card Layout with Embedded Map) ---
st.header("🌐 IP Address Lookup")

st.markdown("""
Enter **one or more IP addresses** below — separated by commas or new lines.
You’ll instantly get their location, ISP, and a small map — all inside elegant cards.
""")

with st.container():
    ip_input = st.text_area(
        "Enter IP Addresses",
        placeholder="e.g., 8.8.8.8, 1.1.1.1 or each on a new line",
        height=100
    )

    lookup_col1, lookup_col2 = st.columns([4, 1])
    with lookup_col2:
        lookup_btn = st.button("🔍 Lookup IPs", use_container_width=True)
    with lookup_col1:
        st.caption("You can check multiple IPs at once.")

if lookup_btn and ip_input.strip():
    ip_list = [ip.strip() for ip in ip_input.replace("\n", ",").split(",") if ip.strip()]
    st.info(f"Looking up {len(ip_list)} IP address(es)...")

    for ip in ip_list:
        with st.spinner(f"Looking up {ip}..."):
            details = get_ip_details(ip)
            add_ip_to_history(ip, details)

# --- Display Lookup Results as Cards ---
if st.session_state.ip_history:
    st.subheader("📜 Recent IP Lookups")

    cards_per_row = 3
    ip_entries = st.session_state.ip_history

    for row_start in range(0, len(ip_entries), cards_per_row):
        cols = st.columns(cards_per_row)
        for i, entry in enumerate(ip_entries[row_start:row_start + cards_per_row]):
            details = entry["details"]
            with cols[i]:
                if "error" in details:
                    st.error(f"❌ {entry['ip']}\n\n{details['error']}")
                    continue

                city = details.get("city", "N/A")
                region = details.get("region", "N/A")
                country = details.get("country", "N/A")
                org = details.get("org", "N/A")
                loc = details.get("loc", None)
                timezone = details.get("timezone", "N/A")

                # Card container
                st.markdown(
                    f"""
                    <div style="
                        background-color: #f8f9fa;
                        border-radius: 15px;
                        box-shadow: 0 4px 14px rgba(0,0,0,0.08);
                        padding: 1rem;
                        margin-bottom: 1.2rem;
                        text-align: center;
                        transition: all 0.3s ease;
                    ">
                        <h4 style="margin-bottom: 6px;">🌐 {entry['ip']}</h4>
                        <p style="font-size: 0.9rem; color: #555;">{city}, {region}, {country}</p>
                        <hr style="margin: 0.5rem 0;">
                        <p style="font-size: 0.85rem; color: #444;">
                            <b>ISP:</b> {org}<br>
                            <b>Timezone:</b> {timezone}<br>
                            <b>Location:</b> {loc if loc else 'N/A'}
                        </p>
                        <p style="font-size: 0.75rem; color: gray; margin-top: 0.5rem;">⏱️ {entry['timestamp']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Add small embedded map
                if loc:
                    lat, lon = map(float, loc.split(","))
                    st.map(
                        pd.DataFrame({"lat": [lat], "lon": [lon]}),
                        use_container_width=True,
                        height=180,
                    )

    st.markdown("---")
    clear_col = st.columns([1, 6, 1])[1]
    with clear_col:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.ip_history = []
            st.rerun()
else:
    st.info("👆 Enter one or more IP addresses to get started")

# Footer
st.markdown("---")
st.markdown("*Built with ❤️ using Streamlit • For efficient trade analysis and quick IP insights*")



