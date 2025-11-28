
# import streamlit as st
# import pandas as pd
# import requests
# from datetime import datetime
# import plotly.express as px
# from st_copy import copy_button
# from io import BytesIO

# # --- Page Configuration ---
# st.set_page_config(page_title="Trade Analyzer & IP Lookup", page_icon="📊", layout="wide")

# # --- Initialize Session State ---
# if 'ip_history' not in st.session_state:
#     st.session_state.ip_history = []


# def analyze_trades(uploaded_file):
#     """Analyze trading positions from Excel file"""
#     try:
#         df = pd.read_excel(uploaded_file, sheet_name=0, header=None)

#         # --- Find Positions section ---
#         start_idx = df.index[df[0].astype(str).str.contains('Positions', case=False, na=False)].tolist()
#         end_idx = df.index[df[0].astype(str).str.contains('Orders', case=False, na=False)].tolist()

#         if not start_idx:
#             st.error("Could not find 'Positions' section in the file.")
#             return None

#         start = start_idx[0] + 1
#         end = end_idx[0] if end_idx else len(df)
#         positions_raw = df.iloc[start:end]

#         positions_raw = positions_raw.dropna(how='all')
#         positions_raw.columns = positions_raw.iloc[0]
#         positions_df = positions_raw[1:].reset_index(drop=True)

#         # --- Rename key columns ---
#         positions_df = positions_df.rename(columns={
#             'Time': 'Open Time',
#             'Price': 'Open Price'
#         })
#         positions_df.columns.values[8] = 'Close Time'
#         positions_df.columns.values[9] = 'Close Price'

#         # --- Convert datetime (supporting milliseconds) ---
#         positions_df['Open Time'] = pd.to_datetime(
#             positions_df['Open Time'], format='%Y.%m.%d %H:%M:%S.%f', errors='coerce'
#         ).fillna(pd.to_datetime(positions_df['Open Time'], format='%Y.%m.%d %H:%M:%S', errors='coerce'))
#         positions_df['Close Time'] = pd.to_datetime(
#             positions_df['Close Time'], format='%Y.%m.%d %H:%M:%S.%f', errors='coerce'
#         ).fillna(pd.to_datetime(positions_df['Close Time'], format='%Y.%m.%d %H:%M:%S', errors='coerce'))

#         # --- Numeric conversions ---
#         positions_df['Profit'] = pd.to_numeric(positions_df['Profit'], errors='coerce')
#         positions_df['Volume'] = pd.to_numeric(positions_df.get('Volume', 0), errors='coerce').fillna(0)

#         # --- Core calculations ---
#         positions_df['Hold_Time'] = positions_df['Close Time'] - positions_df['Open Time']
#         total_volume = positions_df['Volume'].sum()

#         # --- Identify scalping trades (< 3 minutes) ---
#         scalping_df = positions_df[positions_df['Hold_Time'] <= pd.Timedelta(minutes=3)]

#         # --- Identify reversal trades (opposite type within 20s, same symbol) ---
#         positions_df = positions_df.sort_values(by='Open Time').reset_index(drop=True)
#         positions_df['Reversal'] = False

#         for i in range(1, len(positions_df)):
#             prev_close = positions_df.loc[i - 1, 'Close Time']
#             curr_open = positions_df.loc[i, 'Open Time']
#             prev_type = str(positions_df.loc[i - 1, 'Type']).strip().lower()
#             curr_type = str(positions_df.loc[i, 'Type']).strip().lower()
#             prev_symbol = str(positions_df.loc[i - 1, 'Symbol']).strip().upper()
#             curr_symbol = str(positions_df.loc[i, 'Symbol']).strip().upper()

#             if pd.notnull(prev_close) and pd.notnull(curr_open) and prev_symbol == curr_symbol:
#                 time_diff = abs((curr_open - prev_close).total_seconds())
#                 if time_diff <= 20 and (
#                         (prev_type == 'buy' and curr_type == 'sell') or
#                         (prev_type == 'sell' and curr_type == 'buy')
#                 ):
#                     positions_df.loc[i, 'Reversal'] = True

#         reversal_df = positions_df[positions_df['Reversal']]
#         reversal_count = len(reversal_df)
#         reversal_profit = reversal_df['Profit'].sum()

#         # --- Identify burst trades (2 or more within 2 seconds) ---
#         positions_df['Burst'] = False
#         burst_groups = []
#         current_group = [0]

#         for i in range(1, len(positions_df)):
#             prev_open = positions_df.loc[i - 1, 'Open Time']
#             curr_open = positions_df.loc[i, 'Open Time']

#             if pd.notnull(prev_open) and pd.notnull(curr_open):
#                 time_diff = abs((curr_open - prev_open).total_seconds())
#                 if time_diff <= 2:
#                     current_group.append(i)
#                 else:
#                     if len(current_group) >= 2:
#                         burst_groups.append(current_group)
#                     current_group = [i]

#         if len(current_group) >= 2:
#             burst_groups.append(current_group)

#         for group in burst_groups:
#             positions_df.loc[group, 'Burst'] = True

#         burst_df = positions_df[positions_df['Burst']]
#         burst_count = len(burst_df)
#         burst_profit = burst_df['Profit'].sum()

#         # --- Statistics ---
#         total_positions = len(positions_df)
#         total_profit = positions_df['Profit'].sum()
#         scalping_count = len(scalping_df)
#         scalping_profit = scalping_df['Profit'].sum()

#         # --- Percentages ---
#         scalping_percentage = (scalping_count / total_positions * 100) if total_positions > 0 else 0
#         reversal_percentage = (reversal_count / total_positions * 100) if total_positions > 0 else 0
#         burst_percentage = (burst_count / total_positions * 100) if total_positions > 0 else 0

#         scalping_profit_percentage = (scalping_profit / total_profit * 100) if total_profit != 0 else 0
#         reversal_profit_percentage = (reversal_profit / total_profit * 100) if total_profit != 0 else 0
#         burst_profit_percentage = (burst_profit / total_profit * 100) if total_profit != 0 else 0

#         avg_hold_time = positions_df['Hold_Time'].mean()
#         avg_scalping_hold_time = scalping_df['Hold_Time'].mean() if len(scalping_df) > 0 else pd.Timedelta(0)

#         # --- Return structured results ---
#         return {
#             "total_positions": total_positions,
#             "total_profit": total_profit,
#             "total_volume": total_volume,
#             "scalping_count": scalping_count,
#             "scalping_profit": scalping_profit,
#             "scalping_percentage": scalping_percentage,
#             "scalping_profit_percentage": scalping_profit_percentage,
#             "reversal_count": reversal_count,
#             "reversal_profit": reversal_profit,
#             "reversal_percentage": reversal_percentage,
#             "reversal_profit_percentage": reversal_profit_percentage,
#             "burst_count": burst_count,
#             "burst_profit": burst_profit,
#             "burst_percentage": burst_percentage,
#             "burst_profit_percentage": burst_profit_percentage,
#             "avg_hold_time": avg_hold_time,
#             "avg_scalping_hold_time": avg_scalping_hold_time,
#             "scalping_df": scalping_df,
#             "reversal_df": reversal_df,
#             "burst_df": burst_df,
#             "all_positions_df": positions_df
#         }

#     except Exception as e:
#         st.error(f"Error processing file: {str(e)}")
#         return None


# # --- IP Lookup Helpers ---
# def get_ip_details(ip_address):
#     try:
#         response = requests.get(f'https://ipinfo.io/{ip_address}/json', timeout=5)
#         response.raise_for_status()
#         return response.json()
#     except requests.exceptions.RequestException as e:
#         return {"error": str(e)}


# def add_ip_to_history(ip, details):
#     timestamp = datetime.now().strftime("%H:%M:%S")
#     entry = {"timestamp": timestamp, "ip": ip, "details": details}
#     st.session_state.ip_history.insert(0, entry)
#     if len(st.session_state.ip_history) > 10:
#         st.session_state.ip_history = st.session_state.ip_history[:10]


# # ---------- CSS with Light Mode & Wave Background ----------
# theme_css_light = r"""
# <style>
# /* Prevent horizontal scroll */
# html, body { overflow-x: hidden !important; }

# /* Wave background layer (behind everything, non-interactive) */
# .stv-wave {
#   position: fixed !important;
#   top: 0; left: 0;
#   width: 100vw !important;
#   height: 100vh !important;
#   z-index: -1 !important;
#   pointer-events: none !important;
#   background:
#     radial-gradient(circle at 20% 50%, rgba(0, 255, 255, 0.08), transparent 60%),
#     radial-gradient(circle at 80% 80%, rgba(0, 191, 255, 0.08), transparent 60%),
#     linear-gradient(180deg, #ffffff 0%, #e0f7ff 50%, #ffffff 100%);
#   background-size: 400% 400%, 300% 300%, 400% 400% !important;
#   animation: waveAnimation 20s ease infinite !important;
#   opacity: 0.3 !important;
# }

# @keyframes waveAnimation {
#   0% { background-position: 0% 50%, 100% 50%, 0% 50%; }
#   50% { background-position: 100% 50%, 0% 50%, 100% 50%; }
#   100% { background-position: 0% 50%, 100% 50%, 0% 50%; }
# }

# /* Light mode theme tokens */
# :root {
#   --bg: #ffffff;
#   --panel: #f8f9fa;
#   --text: #000000;
#   --accent-1: #00ffff;
#   --accent-2: #00bfff;
# }

# /* Apply panel background to main container */
# .main .block-container {
#   background-color: var(--panel) !important;
#   color: var(--text) !important;
#   position: relative !important;
#   max-width: 100% !important;
#   padding-left: 2rem !important;
#   padding-right: 2rem !important;
# }

# /* Hide sidebar and header completely */
# [data-testid="stSidebar"] { display: none !important; }
# header[data-testid="stHeader"] { display: none !important; }

# /* Buttons & Inputs - Match image style: cyan/blue gradient, rounded corners, black text */
# .stButton>button {
#   background: linear-gradient(90deg, var(--accent-1), var(--accent-2)) !important;
#   color: #000 !important;
#   border: 1px solid rgba(0,191,255,0.25) !important;
#   border-radius: 8px !important;
#   font-weight: 500 !important;
#   padding: 0.5rem 1rem !important;
#   transition: all 0.3s ease !important;
# }
# .stButton>button:hover {
#   box-shadow: 0 0 20px var(--accent-1) !important;
#   transform: translateY(-1px) !important;
# }

# /* Download buttons - same gradient style */
# button[data-testid*="baseButton-secondary"],
# button[data-testid*="baseButton-primary"],
# [data-testid*="stDownloadButton"]>button,
# [data-testid*="stDownloadButton"] button {
#   background: linear-gradient(90deg, var(--accent-1), var(--accent-2)) !important;
#   color: #000 !important;
#   border: 1px solid rgba(0,191,255,0.25) !important;
#   border-radius: 8px !important;
#   font-weight: 500 !important;
#   padding: 0.5rem 1rem !important;
#   transition: all 0.3s ease !important;
# }
# button[data-testid*="baseButton-secondary"]:hover,
# button[data-testid*="baseButton-primary"]:hover,
# [data-testid*="stDownloadButton"]>button:hover,
# [data-testid*="stDownloadButton"] button:hover {
#   box-shadow: 0 0 20px var(--accent-1) !important;
#   transform: translateY(-1px) !important;
# }

# [data-testid="stFileUploader"] {
#   background: #ffffff !important;
#   border: 1px dashed rgba(0,191,255,0.18) !important;
# }

# .stTextInput input, .stTextArea textarea, select {
#   background: #ffffff !important;
#   color: var(--text) !important;
#   border-color: rgba(0,191,255,0.12) !important;
# }

# /* Lock all text colors */
# h1,h2,h3,h4,h5,h6,p,span,label,div { color: var(--text) !important; }

# /* IP Lookup Cards - Light Mode Styling */
# .ip-card {
#   background-color: #ffffff !important;
#   border: 1px solid rgba(0,191,255,0.2) !important;
#   border-radius: 15px !important;
#   box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
#   padding: 1rem !important;
#   margin-bottom: 1.2rem !important;
#   text-align: center !important;
#   color: #000000 !important;
# }

# .ip-card h4 {
#   color: #000000 !important;
#   margin-bottom: 6px !important;
# }

# .ip-card p {
#   color: #333333 !important;
#   font-size: 0.9rem !important;
# }

# .ip-card hr {
#   border-color: rgba(0,191,255,0.2) !important;
#   margin: 0.5rem 0 !important;
# }

# /* Logo container for equal height alignment */
# .logo-container {
#   display: flex;
#   align-items: center;
#   justify-content: center;
#   gap: 1rem;
#   height: 80px;
# }

# .logo-container img {
#   height: 100%;
#   width: auto;
#   object-fit: contain;
# }

# /* Style Streamlit images for logo alignment */
# [data-testid="stImage"] img {
#   max-height: 80px !important;
#   width: auto !important;
#   object-fit: contain !important;
# }

# /* Enlarge Eye logo specifically - 1/3 larger than Rotex (80px + 26.67px = 107px) */
# .eye-logo-wrapper [data-testid="stImage"],
# .eye-logo-wrapper [data-testid="stImage"] img,
# div.eye-logo-wrapper img,
# .eye-logo-wrapper img {
#   width: 107px !important;
#   height: auto !important;
#   min-height: 107px !important;
#   max-height: none !important;
#   object-fit: contain !important;
#   display: block !important;
# }
# </style>

# <!-- Wave background div -->
# <div class="stv-wave"></div>
# """

# # Inject CSS
# st.markdown(theme_css_light, unsafe_allow_html=True)

# # --- Logo Section ---
# # col1, col2, col3 = st.columns([2, 3, 2])
# # with col2:
# #     logo_col1, logo_col2 = st.columns([1, 1])
# #     with logo_col1:
# #         st.image("Rotex.png", use_container_width=True)
# #     with logo_col2:
# #         st.markdown('<div class="eye-logo-wrapper">', unsafe_allow_html=True)
# #         st.image("Eagleeye.png", width=107)
# #         st.markdown('</div>', unsafe_allow_html=True)
# left_col, right_col = st.columns([0.2, 0.8])

# with left_col:
#     st.image("Rotex.png", use_container_width=True)

# with left_col:
#     st.image("eagleeye_logo.png", use_container_width=True)




# st.title("📊 Trade Analyzer & 🌐 IP Lookup Tool")
# st.markdown("---")

# # --- Trade Analysis Section ---
# st.header("📈 Trade Analysis")

# uploaded_file = st.file_uploader("Upload Excel Trade Report", type=["xlsx"], key="trade_file")

# if uploaded_file:
#     with st.spinner("Analyzing trades..."):
#         result = analyze_trades(uploaded_file)

#     if result:
#         # --- Extract Account Number from Filename ---
#         filename = uploaded_file.name
#         import re

#         acc_match = re.search(r"ReportHistory[-_ ]?(\d+)", filename)
#         account_no = acc_match.group(1) if acc_match else "Unknown"

#         # --- Overall Stats ---
#         st.subheader("📊 Overall Statistics")
#         metric_cols = st.columns(4)
#         with metric_cols[0]:
#             st.metric("Total Trades", result["total_positions"])
#         with metric_cols[1]:
#             st.metric("Total Profit", f"${result['total_profit']:.2f}")
#         with metric_cols[2]:
#             st.metric("Avg Hold Time", str(result["avg_hold_time"]).split('.')[0])
#         with metric_cols[3]:
#             st.metric(
#                 "Profit/Trade",
#                 f"${(result['total_profit'] / result['total_positions']):.2f}"
#                 if result['total_positions'] > 0 else "$0.00"
#             )

#         # --- Scalping ---
#         st.subheader("⚡ Scalping Statistics (<3 min holds)")
#         scalp_cols = st.columns(4)
#         with scalp_cols[0]:
#             st.metric("Scalping Trades", result["scalping_count"],
#                       delta=f"{result['scalping_percentage']:.1f}% of total")
#         with scalp_cols[1]:
#             st.metric("Scalping Profit", f"${result['scalping_profit']:.2f}",
#                       delta=f"{result['scalping_profit_percentage']:.1f}% of total profit")
#         with scalp_cols[2]:
#             st.metric("Scalping Win Rate",
#                       f"{(result['scalping_df']['Profit'] > 0).sum() / len(result['scalping_df']) * 100:.1f}%" if len(
#                           result['scalping_df']) > 0 else "N/A")
#         with scalp_cols[3]:
#             st.metric("Avg Scalp Time",
#                       str(result["avg_scalping_hold_time"]).split('.')[0] if result["scalping_count"] > 0 else "N/A")

#         # --- Download Scalping Trades CSV & Excel ---
#         if result["scalping_count"] > 0:
#             download_cols = st.columns(2)
#             with download_cols[0]:
#                 scalping_csv = result["scalping_df"].to_csv(index=False).encode('utf-8')
#                 st.download_button(
#                     label="📥 Download Scalping Trades CSV",
#                     data=scalping_csv,
#                     file_name=f"scalping_trades_{account_no}.csv",
#                     mime="text/csv",
#                     key="scalping_csv_download"
#                 )
#             with download_cols[1]:
#                 scalping_excel = BytesIO()
#                 with pd.ExcelWriter(scalping_excel, engine='openpyxl') as writer:
#                     result["scalping_df"].to_excel(writer, index=False, sheet_name='Scalping Trades')
#                 scalping_excel.seek(0)
#                 st.download_button(
#                     label="📊 Download Scalping Trades Excel",
#                     data=scalping_excel,
#                     file_name=f"scalping_trades_{account_no}.xlsx",
#                     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#                     key="scalping_excel_download"
#                 )

#         # --- Reversal ---
#         st.subheader("🔁 Reversal Trade Statistics (Opposite Type within 20s, Same Symbol)")
#         rev_cols = st.columns(4)
#         with rev_cols[0]:
#             st.metric("Reversal Trades", result["reversal_count"],
#                       delta=f"{result['reversal_percentage']:.1f}% of total")
#         with rev_cols[1]:
#             st.metric("Reversal Profit", f"${result['reversal_profit']:.2f}",
#                       delta=f"{result['reversal_profit_percentage']:.1f}% of total profit")
#         with rev_cols[2]:
#             st.metric("Reversal Win Rate",
#                       f"{(result['reversal_df']['Profit'] > 0).sum() / len(result['reversal_df']) * 100:.1f}%" if len(
#                           result['reversal_df']) > 0 else "N/A")
#         with rev_cols[3]:
#             st.metric("Avg Reversal Profit",
#                       f"${result['reversal_df']['Profit'].mean():.2f}" if len(result['reversal_df']) > 0 else "N/A")

#         # --- Download Reversal Trades CSV & Excel ---
#         if result["reversal_count"] > 0:
#             download_cols = st.columns(2)
#             with download_cols[0]:
#                 reversal_csv = result["reversal_df"].to_csv(index=False).encode('utf-8')
#                 st.download_button(
#                     label="📥 Download Reversal Trades CSV",
#                     data=reversal_csv,
#                     file_name=f"reversal_trades_{account_no}.csv",
#                     mime="text/csv",
#                     key="reversal_csv_download"
#                 )
#             with download_cols[1]:
#                 reversal_excel = BytesIO()
#                 with pd.ExcelWriter(reversal_excel, engine='openpyxl') as writer:
#                     result["reversal_df"].to_excel(writer, index=False, sheet_name='Reversal Trades')
#                 reversal_excel.seek(0)
#                 st.download_button(
#                     label="📊 Download Reversal Trades Excel",
#                     data=reversal_excel,
#                     file_name=f"reversal_trades_{account_no}.xlsx",
#                     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#                     key="reversal_excel_download"
#                 )

#         # --- Burst Trades ---
#         st.subheader("🚀 Burst Trade Statistics (≥2 Trades within 2s)")
#         burst_cols = st.columns(4)
#         with burst_cols[0]:
#             st.metric("Burst Trades", result["burst_count"], delta=f"{result['burst_percentage']:.1f}% of total")
#         with burst_cols[1]:
#             st.metric("Burst Profit", f"${result['burst_profit']:.2f}",
#                       delta=f"{result['burst_profit_percentage']:.1f}% of total profit")
#         with burst_cols[2]:
#             st.metric("Burst Win Rate",
#                       f"{(result['burst_df']['Profit'] > 0).sum() / len(result['burst_df']) * 100:.1f}%" if len(
#                           result['burst_df']) > 0 else "N/A")
#         with burst_cols[3]:
#             st.metric("Avg Burst Profit",
#                       f"${result['burst_df']['Profit'].mean():.2f}" if len(result['burst_df']) > 0 else "N/A")

#         # --- Download Burst Trades CSV & Excel ---
#         if result["burst_count"] > 0:
#             download_cols = st.columns(2)
#             with download_cols[0]:
#                 burst_csv = result["burst_df"].to_csv(index=False).encode('utf-8')
#                 st.download_button(
#                     label="📥 Download Burst Trades CSV",
#                     data=burst_csv,
#                     file_name=f"burst_trades_{account_no}.csv",
#                     mime="text/csv",
#                     key="burst_csv_download"
#                 )
#             with download_cols[1]:
#                 burst_excel = BytesIO()
#                 with pd.ExcelWriter(burst_excel, engine='openpyxl') as writer:
#                     result["burst_df"].to_excel(writer, index=False, sheet_name='Burst Trades')
#                 burst_excel.seek(0)
#                 st.download_button(
#                     label="📊 Download Burst Trades Excel",
#                     data=burst_excel,
#                     file_name=f"burst_trades_{account_no}.xlsx",
#                     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#                     key="burst_excel_download"
#                 )

#         # --- Total Volume (Sum of Volume Column) ---
#         if "Volume" in result["all_positions_df"].columns:
#             total_volume = result["all_positions_df"]["Volume"].astype(float).sum()
#             st.metric("Total Volume Traded", f"{total_volume:.2f}")

#         # --- Pie Chart (Scalping, Reversal, Burst, Other) ---
#         st.markdown("### 🥧 Trade Type Distribution")
#         scalp = result["scalping_count"]
#         rev = result["reversal_count"]
#         burst = result["burst_count"]
#         others = result["total_positions"] - (scalp + rev + burst)

#         pie_data = pd.DataFrame({
#             'Category': ['Scalping Trades', 'Reversal Trades', 'Burst Trades', 'Other Trades'],
#             'Count': [scalp, rev, burst, others]
#         })

#         fig = px.pie(
#             pie_data,
#             names='Category',
#             values='Count',
#             color='Category',
#             color_discrete_sequence=['#FFA500', '#00BFFF', '#FF69B4', '#90EE90']
#         )
#         fig.update_traces(textinfo='percent+label', textposition='inside', pull=[0.05, 0.05, 0.05, 0])
#         fig.update_layout(height=350, width=350, margin=dict(t=40, b=0, l=0, r=0))
#         st.plotly_chart(fig, use_container_width=True)

#         # --- Copyable Client Report ---
#         notes = []
#         if result["scalping_percentage"] > 30:
#             notes.append("Scalping Acc.")
#         if result["reversal_count"] > 0 and result["reversal_percentage"] > 0:
#             notes.append("Performed Hedging")
#         if result["burst_count"] > 5:
#             notes.append("Performed Burst Trades")

#         client_report = f"""📊 *Trade_Analysis_Report - {account_no}*

# *Overall*
# - Total Trades: {result['total_positions']}
# - Total Profit: ${result['total_profit']:.2f}

# *Scalping Trades*
# - Scalping Trades: {result['scalping_count']}
# - Scalping Profit: ${result['scalping_profit']:.2f}
# - Scalping % of trades: {result['scalping_percentage']:.1f}%
# - Scalping profit % of total: {result['scalping_profit_percentage']:.1f}%

# *Reversal Trades*
# - Reversal Trades: {result['reversal_count']}
# - Reversal Profit: ${result['reversal_profit']:.2f}
# - Reversal Trades % of total trades: {result['reversal_percentage']:.1f}%
# - Reversal Profit % of total profit: {result['reversal_profit_percentage']:.1f}%

# *Burst Trades*
# - Burst Trades: {result['burst_count']}
# - Burst Profit: ${result['burst_profit']:.2f}
# - Burst Trades % of total trades: {result['burst_percentage']:.1f}%
# - Burst Profit % of total: {result['burst_profit_percentage']:.1f}%

# {("💡 " + ", ".join(notes)) if notes else ""}"""

#         st.markdown(client_report, unsafe_allow_html=True)

#         # Add a copy button
#         copy_button(
#             client_report.strip(),
#             tooltip="Copy this text",
#             copied_label="Copied!",
#             icon="st",
#         )

# else:
#     st.info("👆 Upload an Excel file to analyze your trades")

# st.markdown("---")

# # --- 🌐 IP Lookup Section (Modern Card Layout with Embedded Map) ---
# st.header("🌐 IP Address Lookup")

# st.markdown("""
# Enter *one or more IP addresses* below — separated by commas or new lines.
# You'll instantly get their location, ISP, and a small map — all inside elegant cards.
# """)

# with st.container():
#     ip_input = st.text_area(
#         "Enter IP Addresses",
#         placeholder="e.g., 8.8.8.8, 1.1.1.1 or each on a new line",
#         height=100,
#         key="ip_input_field"
#     )

#     lookup_col1, lookup_col2 = st.columns([4, 1])
#     with lookup_col2:
#         lookup_btn = st.button("🔍 Lookup IPs", use_container_width=True)
#     with lookup_col1:
#         st.caption("You can check multiple IPs at once.")

# if lookup_btn and ip_input.strip():
#     ip_list = [ip.strip() for ip in ip_input.replace("\n", ",").split(",") if ip.strip()]
#     st.info(f"Looking up {len(ip_list)} IP address(es)...")

#     for ip in ip_list:
#         with st.spinner(f"Looking up {ip}..."):
#             details = get_ip_details(ip)
#             add_ip_to_history(ip, details)

# # --- Display Lookup Results as Cards ---
# if st.session_state.ip_history:
#     st.subheader("📜 Recent IP Lookups")

#     cards_per_row = 3
#     ip_entries = st.session_state.ip_history

#     for row_start in range(0, len(ip_entries), cards_per_row):
#         cols = st.columns(cards_per_row)
#         for i, entry in enumerate(ip_entries[row_start:row_start + cards_per_row]):
#             details = entry["details"]
#             with cols[i]:
#                 if "error" in details:
#                     st.error(f"❌ {entry['ip']}\n\n{details['error']}")
#                     continue

#                 city = details.get("city", "N/A")
#                 region = details.get("region", "N/A")
#                 country = details.get("country", "N/A")
#                 org = details.get("org", "N/A")
#                 loc = details.get("loc", None)
#                 timezone = details.get("timezone", "N/A")

#                 # Card container - Light Mode Styling
#                 st.markdown(
#                     f"""
#                     <div class="ip-card">
#                         <h4 style="margin-bottom: 6px; color: #000000 !important;">🌐 {entry['ip']}</h4>
#                         <p style="font-size: 0.9rem; color: #333333 !important;">{city}, {region}, {country}</p>
#                         <hr style="margin: 0.5rem 0; border-color: rgba(0,191,255,0.2);">
#                         <p style="font-size: 0.85rem; color: #000000 !important;">
#                             <b>ISP:</b> {org}<br>
#                             <b>Timezone:</b> {timezone}<br>
#                             <b>Location:</b> {loc if loc else 'N/A'}
#                         </p>
#                         <p style="font-size: 0.75rem; color: #666666 !important; margin-top: 0.5rem;">⏱ {entry['timestamp']}</p>
#                     </div>
#                     """,
#                     unsafe_allow_html=True,
#                 )

#                 # Add small embedded map
#                 if loc:
#                     lat, lon = map(float, loc.split(","))
#                     st.map(
#                         pd.DataFrame({"lat": [lat], "lon": [lon]}),
#                         use_container_width=True,
#                         height=180,
#                     )

#     st.markdown("---")
#     clear_col = st.columns([1, 6, 1])[1]
#     with clear_col:
#         if st.button("🗑 Clear History", use_container_width=True):
#             st.session_state.ip_history = []
#             st.rerun()
# else:
#     st.info("👆 Enter one or more IP addresses to get started")

# # Footer with Logos
# st.markdown("---")

# st.markdown("Built with ❤ using Streamlit • For efficient trade analysis and quick IP insights")

import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.express as px
from st_copy import copy_button
from io import BytesIO

# --- Page Configuration ---
st.set_page_config(page_title="Trade Analyzer & IP Lookup", page_icon="📊", layout="wide")

# --- Initialize Session State ---
if 'ip_history' not in st.session_state:
    st.session_state.ip_history = []


def analyze_trades(uploaded_file, scalping_limit):
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

        # --- Numeric conversions ---
        positions_df['Profit'] = pd.to_numeric(positions_df['Profit'], errors='coerce')
        positions_df['Volume'] = pd.to_numeric(positions_df.get('Volume', 0), errors='coerce').fillna(0)

        # --- Core calculations ---
        positions_df['Hold_Time'] = positions_df['Close Time'] - positions_df['Open Time']
        total_volume = positions_df['Volume'].sum()

        # --- Identify scalping trades (< 3 minutes) ---
        # scalping_df = positions_df[positions_df['Hold_Time'] <= pd.Timedelta(minutes=3)]
        scalping_df = positions_df[positions_df['Hold_Time'] <= pd.Timedelta(minutes=scalping_limit)]

        # --- Identify reversal trades (opposite type within 20s, same symbol) ---
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
        profit_by_symbol = positions_df.groupby("Symbol")["Profit"].sum()
        trades_count = positions_df["Symbol"].value_counts()

        # --- Percentages ---
        scalping_percentage = (scalping_count / total_positions * 100) if total_positions > 0 else 0
        reversal_percentage = (reversal_count / total_positions * 100) if total_positions > 0 else 0
        burst_percentage = (burst_count / total_positions * 100) if total_positions > 0 else 0

        scalping_profit_percentage = (scalping_profit / total_profit * 100) if total_profit != 0 else 0
        reversal_profit_percentage = (reversal_profit / total_profit * 100) if total_profit != 0 else 0
        burst_profit_percentage = (burst_profit / total_profit * 100) if total_profit != 0 else 0

        avg_hold_time = positions_df['Hold_Time'].mean()
        avg_scalping_hold_time = scalping_df['Hold_Time'].mean() if len(scalping_df) > 0 else pd.Timedelta(0)


                # Cumulative profit over time (for equity curve)
        equity_df = positions_df.sort_values("Close Time").copy()
        equity_df["Cumulative_Profit"] = equity_df["Profit"].cumsum()


        # --- Return structured results ---
        return {
            "total_positions": total_positions,
            "total_profit": total_profit,
            "total_volume": total_volume,
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
            "all_positions_df": positions_df,
            "profit_by_symbol": profit_by_symbol,
            "trades_count": trades_count,
            "equity_df": equity_df
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


# ---------- CSS with Light Mode & Wave Background ----------
theme_css_light = r"""
<style>
/* Prevent horizontal scroll */
html, body { overflow-x: hidden !important; }

/* Wave background layer (behind everything, non-interactive) */
.stv-wave {
  position: fixed !important;
  top: 0; left: 0;
  width: 100vw !important;
  height: 100vh !important;
  z-index: -1 !important;
  pointer-events: none !important;
  background:
    radial-gradient(circle at 20% 50%, rgba(0, 255, 255, 0.08), transparent 60%),
    radial-gradient(circle at 80% 80%, rgba(0, 191, 255, 0.08), transparent 60%),
    linear-gradient(180deg, #ffffff 0%, #e0f7ff 50%, #ffffff 100%);
  background-size: 400% 400%, 300% 300%, 400% 400% !important;
  animation: waveAnimation 20s ease infinite !important;
  opacity: 0.3 !important;
}

@keyframes waveAnimation {
  0% { background-position: 0% 50%, 100% 50%, 0% 50%; }
  50% { background-position: 100% 50%, 0% 50%, 100% 50%; }
  100% { background-position: 0% 50%, 100% 50%, 0% 50%; }
}

/* Light mode theme tokens */
:root {
  --bg: #ffffff;
  --panel: #f8f9fa;
  --text: #000000;
  --accent-1: #00ffff;
  --accent-2: #00bfff;
}

/* Apply panel background to main container */
.main .block-container {
  background-color: var(--panel) !important;
  color: var(--text) !important;
  position: relative !important;
  max-width: 100% !important;
  padding-left: 2rem !important;
  padding-right: 2rem !important;
}

/* Hide sidebar and header completely */
[data-testid="stSidebar"] { display: none !important; }
header[data-testid="stHeader"] { display: none !important; }

/* Buttons & Inputs - Match image style: cyan/blue gradient, rounded corners, black text */
.stButton>button {
  background: linear-gradient(90deg, var(--accent-1), var(--accent-2)) !important;
  color: #000 !important;
  border: 1px solid rgba(0,191,255,0.25) !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
  padding: 0.5rem 1rem !important;
  transition: all 0.3s ease !important;
}
.stButton>button:hover {
  box-shadow: 0 0 20px var(--accent-1) !important;
  transform: translateY(-1px) !important;
}

/* Download buttons - same gradient style */
button[data-testid*="baseButton-secondary"],
button[data-testid*="baseButton-primary"],
[data-testid*="stDownloadButton"]>button,
[data-testid*="stDownloadButton"] button {
  background: linear-gradient(90deg, var(--accent-1), var(--accent-2)) !important;
  color: #000 !important;
  border: 1px solid rgba(0,191,255,0.25) !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
  padding: 0.5rem 1rem !important;
  transition: all 0.3s ease !important;
}
button[data-testid*="baseButton-secondary"]:hover,
button[data-testid*="baseButton-primary"]:hover,
[data-testid*="stDownloadButton"]>button:hover,
[data-testid*="stDownloadButton"] button:hover {
  box-shadow: 0 0 20px var(--accent-1) !important;
  transform: translateY(-1px) !important;
}

[data-testid="stFileUploader"] {
  background: #ffffff !important;
  border: 1px dashed rgba(0,191,255,0.18) !important;
}

.stTextInput input, .stTextArea textarea, select {
  background: #ffffff !important;
  color: var(--text) !important;
  border-color: rgba(0,191,255,0.12) !important;
}

/* Lock all text colors */
h1,h2,h3,h4,h5,h6,p,span,label,div { color: var(--text) !important; }

/* IP Lookup Cards - Light Mode Styling */
.ip-card {
  background-color: #ffffff !important;
  border: 1px solid rgba(0,191,255,0.2) !important;
  border-radius: 15px !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
  padding: 1rem !important;
  margin-bottom: 1.2rem !important;
  text-align: center !important;
  color: #000000 !important;
}

.ip-card h4 {
  color: #000000 !important;
  margin-bottom: 6px !important;
}

.ip-card p {
  color: #333333 !important;
  font-size: 0.9rem !important;
}

.ip-card hr {
  border-color: rgba(0,191,255,0.2) !important;
  margin: 0.5rem 0 !important;
}

/* Logo container for equal height alignment */
.logo-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  height: 80px;
}

.logo-container img {
  height: 100%;
  width: auto;
  object-fit: contain;
}

/* Style Streamlit images for logo alignment */
[data-testid="stImage"] img {
  max-height: 80px !important;
  width: auto !important;
  object-fit: contain !important;
}

/* Enlarge Eye logo specifically - 1/3 larger than Rotex (80px + 26.67px = 107px) */
.eye-logo-wrapper [data-testid="stImage"],
.eye-logo-wrapper [data-testid="stImage"] img,
div.eye-logo-wrapper img,
.eye-logo-wrapper img {
  width: 107px !important;
  height: auto !important;
  min-height: 107px !important;
  max-height: none !important;
  object-fit: contain !important;
  display: block !important;
}
</style>

<!-- Wave background div -->
<div class="stv-wave"></div>
"""

# Inject CSS
st.markdown(theme_css_light, unsafe_allow_html=True)

# --- Logo Section ---
col1, col2, col3 = st.columns([2, 3, 2])
with col2:
    logo_col1, logo_col2 = st.columns([1, 1])
    with logo_col1:
        st.image("Rotex.png", use_container_width=True)
    with logo_col2:
        st.markdown('<div class="eye-logo-wrapper">', unsafe_allow_html=True)
        st.image("eagleeye_logo.png", width=107)
        st.markdown('</div>', unsafe_allow_html=True)

st.title("📊 Trade Analyzer & 🌐 IP Lookup Tool")
st.markdown("---")

# --- Trade Analysis Section ---
st.header("📈 Trade Analysis")

uploaded_file = st.file_uploader("Upload Excel Trade Report", type=["xlsx"], key="trade_file")

if uploaded_file:
    scalping_limit = st.slider(
        "Select Scalping Time (minutes)", min_value=1, max_value=5, value=3
    )
    with st.spinner("Analyzing trades..."):
        # result = analyze_trades(uploaded_file)
        result = analyze_trades(uploaded_file, scalping_limit)

    if result:
        # --- Extract Account Number from Filename ---
        filename = uploaded_file.name
        import re

        acc_match = re.search(r"ReportHistory[-_ ]?(\d+)", filename)
        account_no = acc_match.group(1) if acc_match else "Unknown"

        # --- Overall Stats ---
        st.subheader("📊 Overall Statistics")
        metric_cols = st.columns(4)
        with metric_cols[0]:
            st.metric("Total Trades", result["total_positions"])
        with metric_cols[1]:
            st.metric("Total Profit", f"${result['total_profit']:.2f}")
        with metric_cols[2]:
            st.metric("Avg Hold Time", str(result["avg_hold_time"]).split('.')[0])
        with metric_cols[3]:
            st.metric(
                "Profit/Trade",
                f"${(result['total_profit'] / result['total_positions']):.2f}"
                if result['total_positions'] > 0 else "$0.00"
            )

        # --- Scalping ---
        st.subheader("⚡ Scalping Statistics (<3 min holds)")
        scalp_cols = st.columns(4)
        with scalp_cols[0]:
            st.metric("Scalping Trades", result["scalping_count"],
                      delta=f"{result['scalping_percentage']:.1f}% of total")
        with scalp_cols[1]:
            st.metric("Scalping Profit", f"${result['scalping_profit']:.2f}",
                      delta=f"{result['scalping_profit_percentage']:.1f}% of total profit")
        with scalp_cols[2]:
            st.metric("Scalping Win Rate",
                      f"{(result['scalping_df']['Profit'] > 0).sum() / len(result['scalping_df']) * 100:.1f}%" if len(
                          result['scalping_df']) > 0 else "N/A")
        with scalp_cols[3]:
            st.metric("Avg Scalp Time",
                      str(result["avg_scalping_hold_time"]).split('.')[0] if result["scalping_count"] > 0 else "N/A")

        # --- Download Scalping Trades CSV & Excel ---
        if result["scalping_count"] > 0:
            download_cols = st.columns(2)
            with download_cols[0]:
                scalping_csv = result["scalping_df"].to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Scalping Trades CSV",
                    data=scalping_csv,
                    file_name=f"scalping_trades_{account_no}.csv",
                    mime="text/csv",
                    key="scalping_csv_download"
                )
            with download_cols[1]:
                scalping_excel = BytesIO()
                with pd.ExcelWriter(scalping_excel, engine='openpyxl') as writer:
                    result["scalping_df"].to_excel(writer, index=False, sheet_name='Scalping Trades')
                scalping_excel.seek(0)
                st.download_button(
                    label="📊 Download Scalping Trades Excel",
                    data=scalping_excel,
                    file_name=f"scalping_trades_{account_no}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="scalping_excel_download"
                )

        # --- Reversal ---
        st.subheader("🔁 Reversal Trade Statistics (Opposite Type within 20s, Same Symbol)")
        rev_cols = st.columns(4)
        with rev_cols[0]:
            st.metric("Reversal Trades", result["reversal_count"],
                      delta=f"{result['reversal_percentage']:.1f}% of total")
        with rev_cols[1]:
            st.metric("Reversal Profit", f"${result['reversal_profit']:.2f}",
                      delta=f"{result['reversal_profit_percentage']:.1f}% of total profit")
        with rev_cols[2]:
            st.metric("Reversal Win Rate",
                      f"{(result['reversal_df']['Profit'] > 0).sum() / len(result['reversal_df']) * 100:.1f}%" if len(
                          result['reversal_df']) > 0 else "N/A")
        with rev_cols[3]:
            st.metric("Avg Reversal Profit",
                      f"${result['reversal_df']['Profit'].mean():.2f}" if len(result['reversal_df']) > 0 else "N/A")

        # --- Download Reversal Trades CSV & Excel ---
        if result["reversal_count"] > 0:
            download_cols = st.columns(2)
            with download_cols[0]:
                reversal_csv = result["reversal_df"].to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Reversal Trades CSV",
                    data=reversal_csv,
                    file_name=f"reversal_trades_{account_no}.csv",
                    mime="text/csv",
                    key="reversal_csv_download"
                )
            with download_cols[1]:
                reversal_excel = BytesIO()
                with pd.ExcelWriter(reversal_excel, engine='openpyxl') as writer:
                    result["reversal_df"].to_excel(writer, index=False, sheet_name='Reversal Trades')
                reversal_excel.seek(0)
                st.download_button(
                    label="📊 Download Reversal Trades Excel",
                    data=reversal_excel,
                    file_name=f"reversal_trades_{account_no}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="reversal_excel_download"
                )

        # --- Burst Trades ---
        st.subheader("🚀 Burst Trade Statistics (≥2 Trades within 2s)")
        burst_cols = st.columns(4)
        with burst_cols[0]:
            st.metric("Burst Trades", result["burst_count"], delta=f"{result['burst_percentage']:.1f}% of total")
        with burst_cols[1]:
            st.metric("Burst Profit", f"${result['burst_profit']:.2f}",
                      delta=f"{result['burst_profit_percentage']:.1f}% of total profit")
        with burst_cols[2]:
            st.metric("Burst Win Rate",
                      f"{(result['burst_df']['Profit'] > 0).sum() / len(result['burst_df']) * 100:.1f}%" if len(
                          result['burst_df']) > 0 else "N/A")
        with burst_cols[3]:
            st.metric("Avg Burst Profit",
                      f"${result['burst_df']['Profit'].mean():.2f}" if len(result['burst_df']) > 0 else "N/A")

        # --- Download Burst Trades CSV & Excel ---
        if result["burst_count"] > 0:
            download_cols = st.columns(2)
            with download_cols[0]:
                burst_csv = result["burst_df"].to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Burst Trades CSV",
                    data=burst_csv,
                    file_name=f"burst_trades_{account_no}.csv",
                    mime="text/csv",
                    key="burst_csv_download"
                )
            with download_cols[1]:
                burst_excel = BytesIO()
                with pd.ExcelWriter(burst_excel, engine='openpyxl') as writer:
                    result["burst_df"].to_excel(writer, index=False, sheet_name='Burst Trades')
                burst_excel.seek(0)
                st.download_button(
                    label="📊 Download Burst Trades Excel",
                    data=burst_excel,
                    file_name=f"burst_trades_{account_no}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="burst_excel_download"
                )

        # --- Total Volume (Sum of Volume Column) ---
        if "Volume" in result["all_positions_df"].columns:
            total_volume = result["all_positions_df"]["Volume"].astype(float).sum()
            st.metric("Total Volume Traded", f"{total_volume:.2f}")

        st.subheader("Visual Analysis")

        # Layout: Pie chart (profit distribution) on left, bar chart (trade count) on right
        col1, col2, col3 = st.columns(3)

        # ----- LEFT: Existing Profit Distribution Pie Chart -----
        with col1:
            # --- Pie Chart (Scalping, Reversal, Burst, Other) ---
            st.markdown("###  Trade Type Distribution")
            scalp = result["scalping_count"]
            rev = result["reversal_count"]
            burst = result["burst_count"]
            others = result["total_positions"] - (scalp + rev + burst)

            pie_data = pd.DataFrame({
                'Category': ['Scalping Trades', 'Reversal Trades', 'Burst Trades', 'Other Trades'],
                'Count': [scalp, rev, burst, others]
            })

            fig = px.pie(
                pie_data,
                names='Category',
                values='Count',
                color='Category',
                color_discrete_sequence=['#FFA500', '#00BFFF', '#FF69B4', '#90EE90']
            )
            fig.update_traces(textinfo='percent+label', textposition='inside', pull=[0.05, 0.05, 0.05, 0])
            fig.update_layout(height=350, width=350, margin=dict(t=40, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

        with col2:  # or whichever column is for the profit visual
            st.write("### Profit / Loss by Symbol")

            profit_by_symbol = result["profit_by_symbol"]  # already prepared in your logic

            # Assign colors based on profit or loss
            bar_colors = ["green" if profit_by_symbol[symbol] >= 0 else "red"
                          for symbol in profit_by_symbol.index]

            fig_profit = px.bar(
                x=profit_by_symbol.values,
                y=profit_by_symbol.index,
                orientation='h',
                labels={"x": "Profit / Loss", "y": "Symbol"},
            )

            fig_profit.update_traces(marker_color=bar_colors)
            fig_profit.update_layout(xaxis_title="Profit / Loss (USD)")

            st.plotly_chart(fig_profit, use_container_width=True)

        # ----- RIGHT: NEW - Number of Trades per Symbol -----
        with col3:
            st.write("### Number of Trades per Symbol")

            # Trades count already available from result dict
            trades_count = result["trades_count"]

            # Total profit per symbol already available from result dict
            profit_by_symbol = result["profit_by_symbol"]

            # Assign colors based on total profit for that symbol
            bar_colors = ["green" if profit_by_symbol[symbol] >= 0 else "red"
                          for symbol in trades_count.index]

            fig2 = px.bar(
                x=trades_count.index,
                y=trades_count.values,
                labels={"x": "Symbol", "y": "Number of Trades"},
            )

            fig2.update_traces(marker_color=bar_colors)
            st.plotly_chart(fig2, use_container_width=True)

        st.write("### 📈 Equity Curve — Profit Over Time")

        equity_df = result["equity_df"]

        fig_equity = px.line(
                equity_df,
                x="Close Time",
                y="Cumulative_Profit",
                markers=True,
                labels={"Close Time": "Time", "Cumulative_Profit": "Profit"},
            )

        fig_equity.update_layout(
                height=550,
                xaxis_title="Time",
                yaxis_title="Cumulative Profit (USD)",
                margin=dict(l=10, r=10, t=50, b=10),
                hovermode="x unified",
            )

        # full screen width
        st.plotly_chart(fig_equity, use_container_width=True)


        # --- Copyable Client Report ---
        notes = []
        if result["scalping_percentage"] > 30:
            notes.append("Scalping Acc.")
        if result["reversal_count"] > 0 and result["reversal_percentage"] > 0:
            notes.append("Performed Hedging")
        if result["burst_count"] > 5:
            notes.append("Performed Burst Trades")

        client_report = f"""📊 *Trade_Analysis_Report - {account_no}*

*Overall*
- Total Trades: {result['total_positions']}
- Total Profit: ${result['total_profit']:.2f}

*Scalping Trades*
- Scalping Trades: {result['scalping_count']}
- Scalping Profit: ${result['scalping_profit']:.2f}
- Scalping % of trades: {result['scalping_percentage']:.1f}%
- Scalping profit % of total: {result['scalping_profit_percentage']:.1f}%

*Reversal Trades*
- Reversal Trades: {result['reversal_count']}
- Reversal Profit: ${result['reversal_profit']:.2f}
- Reversal Trades % of total trades: {result['reversal_percentage']:.1f}%
- Reversal Profit % of total profit: {result['reversal_profit_percentage']:.1f}%

*Burst Trades*
- Burst Trades: {result['burst_count']}
- Burst Profit: ${result['burst_profit']:.2f}
- Burst Trades % of total trades: {result['burst_percentage']:.1f}%
- Burst Profit % of total: {result['burst_profit_percentage']:.1f}%

{("💡 " + ", ".join(notes)) if notes else ""}"""

        st.markdown(client_report, unsafe_allow_html=True)

        # Add a copy button
        copy_button(
            client_report.strip(),
            tooltip="Copy this text",
            copied_label="Copied!",
            icon="st",
        )

else:
    st.info("👆 Upload an Excel file to analyze your trades")

st.markdown("---")

# --- 🌐 IP Lookup Section (Modern Card Layout with Embedded Map) ---
st.header("🌐 IP Address Lookup")

st.markdown("""
Enter *one or more IP addresses* below — separated by commas or new lines.
You'll instantly get their location, ISP, and a small map — all inside elegant cards.
""")

with st.container():
    ip_input = st.text_area(
        "Enter IP Addresses",
        placeholder="e.g., 8.8.8.8, 1.1.1.1 or each on a new line",
        height=100,
        key="ip_input_field"
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

                # Card container - Light Mode Styling
                st.markdown(
                    f"""
                    <div class="ip-card">
                        <h4 style="margin-bottom: 6px; color: #000000 !important;">🌐 {entry['ip']}</h4>
                        <p style="font-size: 0.9rem; color: #333333 !important;">{city}, {region}, {country}</p>
                        <hr style="margin: 0.5rem 0; border-color: rgba(0,191,255,0.2);">
                        <p style="font-size: 0.85rem; color: #000000 !important;">
                            <b>ISP:</b> {org}<br>
                            <b>Timezone:</b> {timezone}<br>
                            <b>Location:</b> {loc if loc else 'N/A'}
                        </p>
                        <p style="font-size: 0.75rem; color: #666666 !important; margin-top: 0.5rem;">⏱ {entry['timestamp']}</p>
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
        if st.button("🗑 Clear History", use_container_width=True):
            st.session_state.ip_history = []
            st.rerun()
else:
    st.info("👆 Enter one or more IP addresses to get started")

st.markdown("Built with ❤ using Streamlit • For efficient trade analysis and quick IP insights")



