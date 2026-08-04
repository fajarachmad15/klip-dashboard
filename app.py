"""
App: app.py
Deskripsi: Multi-Page Corporate Dashboard untuk Analisis KLIP Finance 2026:
            1. Detail Engagement 2026
            2. Fasilitator Corporate
            3. Submission 2026
            Mengambil data CSV otomatis langsung dari Google Drive.
"""

import os
import sys
import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Import modul fetch Google Drive
from fetch_drive_data import (
    DEFAULT_FOLDER_ID,
    ENGAGEMENT_CSV_PATH,
    FASILITATOR_CSV_PATH,
    SUBMISSION_CSV_PATH,
    LATEST_CSV_PATH,
    download_klip_data_from_drive,
    generate_sample_mock_data,
)

# ==============================================================================
# KONFIGURASI HALAMAN STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="KLIP Finance Analytics Dashboard 2026",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
# CUSTOM CSS / DESIGN SYSTEM
# ==============================================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Sembunyikan Sidebar Streamlit Bawaan Secara Total */
    [data-testid="stSidebar"],
    [data-testid="collapsedControl"] {
        display: none !important;
    }

    /* Lebarkan Container Utama & Berikan Ruang Atas yang Cukup Agar Tidak Tertutup Header */
    .block-container {
        padding-top: 4.25rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 95% !important;
    }

    /* Pastikan header Streamlit tidak menutupi tab */
    header[data-testid="stHeader"] {
        background: transparent !important;
        z-index: 1 !important;
    }

    /* Sembunyikan Label Judul 'Dashboard Menu' */
    div[data-testid="stRadio"] > label,
    div[data-testid="stRadio"] [data-testid="stWidgetLabel"],
    div[data-testid="stRadio"] p:empty {
        display: none !important;
    }

    /* Horizontal Tab Navigation Bar Modern */
    div[data-testid="stRadio"] {
        margin-top: 0.2rem !important;
        margin-bottom: 1.2rem !important;
        overflow: visible !important;
        z-index: 10 !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"],
    div[data-testid="stRadio"] > div {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: 12px !important;
        background: transparent !important;
        padding: 0 !important;
        align-items: center !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] > label,
    div[data-testid="stRadio"] label[data-baseweb="radio"] {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        background-color: #F1F5F9 !important;
        border: 1.5px solid #CBD5E1 !important;
        padding: 10px 22px !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #1E293B !important;
        cursor: pointer !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
        margin: 0 !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] > label:hover,
    div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {
        background-color: #E2E8F0 !important;
        border-color: #94A3B8 !important;
        color: #0F172A !important;
        transform: translateY(-1px);
    }

    div[data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"],
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border-color: #2563EB !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3) !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] p,
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* Sembunyikan lingkaran/dot radio button bawaan secara total */
    div[data-testid="stRadio"] input[type="radio"],
    div[data-testid="stRadio"] [data-testid="stRadioButton"] > div:first-child,
    div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child:not(:last-child),
    div[data-testid="stRadio"] label > div:first-child:not(:last-child) {
        display: none !important;
    }

    /* Modern Metric Card Styling */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        margin-bottom: 12px;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
    }
    .metric-title {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #64748B;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.15;
        margin-bottom: 6px;
    }
    .metric-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 0.76rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 9999px;
    }
    .badge-success {
        background-color: #DBEAFE;
        color: #1D4ED8;
    }
    .badge-danger {
        background-color: #FEE2E2;
        color: #DC2626;
    }
    .badge-info {
        background-color: #DBEAFE;
        color: #1D4ED8;
    }
    .badge-warning {
        background-color: #FEE2E2;
        color: #DC2626;
    }

    /* Header Banner */
    .main-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: #FFFFFF;
        padding: 22px 28px;
        border-radius: 14px;
        margin-bottom: 18px;
        box-shadow: 0 6px 20px -3px rgba(15, 23, 42, 0.25);
    }
    .main-header h1 {
        font-size: 1.65rem;
        font-weight: 800;
        margin: 0 0 6px 0;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .main-header p {
        font-size: 0.92rem;
        color: #94A3B8;
        margin: 0;
    }
    .header-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 12px;
    }
    .pill {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        font-size: 0.78rem;
        font-weight: 500;
        background: rgba(255, 255, 255, 0.1);
        padding: 4px 10px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        color: #E2E8F0;
    }

    /* Section Heading */
    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Pastikan Dropdown / Multiselect selalu terbuka ke bawah secara proporsional */
    div[data-baseweb="popover"] {
        z-index: 999999 !important;
    }

    div[data-baseweb="popover"] div[role="listbox"],
    div[data-baseweb="popover"] ul,
    ul[data-baseweb="menu"],
    div[data-baseweb="select"] ul {
        max-height: 250px !important;
        overflow-y: auto !important;
    }

    /* Table / Dataframe Header Styling: Abu-abu muda solid & Font Hitam Bold */
    div[data-testid="stDataFrame"] {
        border-radius: 8px;
        border: 1px solid #CBD5E1 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }

    div[data-testid="stDataFrame"] div[data-testid="stDataFrameHeaderCell"],
    div[data-testid="stDataFrame"] header,
    div[data-testid="stDataFrame"] [role="columnheader"],
    thead th,
    th {
        background-color: #CBD5E1 !important;
        color: #000000 !important;
        font-weight: 800 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    /* Optimasi Tampilan Layar HP / Mobile */
    @media (max-width: 768px) {
        [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
            gap: 0.5rem !important;
        }

        [data-testid="column"] {
            width: calc(50% - 0.5rem) !important;
            flex: 1 1 calc(50% - 0.5rem) !important;
            min-width: calc(50% - 0.5rem) !important;
        }
        
        .metric-card {
            padding: 12px 14px !important;
            margin-bottom: 4px !important;
        }
        .metric-value {
            font-size: 1.4rem !important;
        }
        .metric-title {
            font-size: 0.75rem !important;
        }
        
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 3.5rem !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# FUNGSI PEMUATAN DATA (CACHED)
# ==============================================================================
@st.cache_data(show_spinner=False)
def load_engagement_data() -> Optional[pd.DataFrame]:
    """Memuat dan menormalkan data Detail Engagement 2026."""
    target_path = ENGAGEMENT_CSV_PATH if ENGAGEMENT_CSV_PATH.exists() else LATEST_CSV_PATH
    if not target_path.exists():
        return None

    try:
        df = pd.read_csv(target_path)
        col_map = {
            "Employee ID": "Employee_ID",
            "Employee_ID": "Employee_ID",
            "NIK": "Employee_ID",
            "Employee Name": "Employee_Name",
            "Employee_Name": "Employee_Name",
            "Company Name": "Company_Name",
            "Company_Name": "Company_Name",
            "Status PA": "Status_PA",
            "Status_PA": "Status_PA",
            "SttsPA": "Status_PA",
            "Group BU/CORP": "Group_BU_CORP",
            "Group BU/Corp": "Group_BU_CORP",
            "Loc. Type": "Loc_Type",
            "Loc Type": "Loc_Type",
            "Loc": "Loc_Type",
            "Location": "Loc_Type",
            "Engagement Status": "Engagement_Status",
            "Engagement_Status": "Engagement_Status",
            "Engagement": "Engagement_Status",
            "Score": "Engagement_Score",
            "Engagement Score": "Engagement_Score",
            "Completion Date": "Completion_Date",
        }
        for old_col, new_col in col_map.items():
            if old_col in df.columns and new_col not in df.columns:
                df.rename(columns={old_col: new_col}, inplace=True)

        for col in ["Leader", "Sponsor", "Member", "Fasilitator"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
            else:
                df[col] = 0

        if "Engagement_Status" in df.columns:
            df["Engagement_Status"] = df["Engagement_Status"].astype(str).str.strip()
            def clean_status(val):
                s = str(val).strip().lower()
                if s in ["engaged", "ikut", "true", "1"]:
                    return "Engaged"
                elif s in ["non-engaged", "non engaged", "belum ikut", "false", "0", "nan", "none", ""]:
                    return "Non-Engaged"
                return val
            df["Engagement_Status"] = df["Engagement_Status"].apply(clean_status)
        else:
            def infer_status(row):
                for role_col in ["Leader", "Sponsor", "Member", "Fasilitator"]:
                    if role_col in row and row[role_col] > 0:
                        return "Engaged"
                return "Non-Engaged"
            df["Engagement_Status"] = df.apply(infer_status, axis=1)

        if "Engagement_Score" not in df.columns:
            df["Engagement_Score"] = df["Engagement_Status"].apply(lambda s: 100 if s == "Engaged" else 0)
        else:
            df["Engagement_Score"] = pd.to_numeric(df["Engagement_Score"], errors="coerce").fillna(0).astype(int)

        for col in ["Employee_Name", "Employee_ID", "Division", "Directorate", "Company_Name", "Loc_Type", "Status_PA"]:
            if col in df.columns:
                df[col] = df[col].fillna("-").astype(str).str.strip()

        return df
    except Exception as e:
        st.error(f"Gagal memuat dataset Engagement: {e}")
        return None


@st.cache_data(show_spinner=False)
def load_fasilitator_data() -> Optional[pd.DataFrame]:
    """Memuat dan menormalkan data Fasilitator Corporate."""
    if not FASILITATOR_CSV_PATH.exists():
        return None

    try:
        df = pd.read_csv(FASILITATOR_CSV_PATH)
        for num_col in ["Submitted 2026", "Registered 2026", "Finished 2026"]:
            if num_col in df.columns:
                df[num_col] = pd.to_numeric(df[num_col], errors="coerce").fillna(0).astype(int)
            else:
                df[num_col] = 0

        if "%Finished" in df.columns:
            df["%Finished_Num"] = pd.to_numeric(df["%Finished"].astype(str).str.replace("%", "").str.replace("-", "0"), errors="coerce").fillna(0)
        else:
            df["%Finished_Num"] = df.apply(lambda r: (r["Finished 2026"] / r["Submitted 2026"] * 100) if r["Submitted 2026"] > 0 else 0, axis=1)

        for text_col in ["Nama", "Function"]:
            if text_col in df.columns:
                df[text_col] = df[text_col].fillna("-").astype(str).str.strip()

        return df
    except Exception as e:
        st.error(f"Gagal memuat dataset Fasilitator: {e}")
        return None


@st.cache_data(show_spinner=False)
def load_submission_data() -> Optional[pd.DataFrame]:
    """Memuat dan menormalkan data Submission 2026."""
    if not SUBMISSION_CSV_PATH.exists():
        return None

    try:
        df = pd.read_csv(SUBMISSION_CSV_PATH)
        
        # Bersihkan nama kolom
        df.columns = [c.strip() for c in df.columns]

        if "Stage" in df.columns:
            df["Stage"] = df["Stage"].fillna("PROPOSAL").astype(str).str.strip().str.upper()

        # Ekstraksi bulan dari kolom Submitted
        month_map = {
            "jan": "Januari", "feb": "Februari", "mar": "Maret", "apr": "April",
            "mei": "Mei", "may": "Mei", "jun": "Juni", "jul": "Juli",
            "agu": "Agustus", "aug": "Agustus", "sep": "September", "okt": "Oktober",
            "oct": "Oktober", "nov": "November", "des": "Desember", "dec": "Desember",
        }
        
        def extract_month(val):
            val_str = str(val).lower()
            for k, v in month_map.items():
                if k in val_str:
                    return v
            return "Other"

        if "Submitted" in df.columns:
            df["Month"] = df["Submitted"].apply(extract_month)
        else:
            df["Month"] = "Januari"

        for text_col in ["No.KLIP", "Title", "Leader_Name", "Fasilitator_Name", "Function", "Status", "BU/Corp"]:
            if text_col in df.columns:
                df[text_col] = df[text_col].fillna("-").astype(str).str.strip()

        return df
    except Exception as e:
        st.error(f"Gagal memuat dataset Submission: {e}")
        return None


# Helper fungsi render KPI card
def render_metric_card(title: str, value: str, badge_text: str, badge_type: str = "info"):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-badge badge-{badge_type}">{badge_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Helper fungsi sinkronisasi Google Drive
def perform_drive_sync():
    with st.spinner("⏳ Downloading and synchronizing 3 CSV datasets from Google Drive..."):
        success, message, paths = download_klip_data_from_drive(folder_id=DEFAULT_FOLDER_ID)

    if success:
        st.cache_data.clear()
        st.toast("✅ All datasets successfully synced from Google Drive!", icon="🎉")
        st.success(f"**Success!**\n\n{message}")
        st.rerun()
    else:
        st.error(f"**Sync Failed:**\n\n{message}")
        st.info("💡 Click below to generate sample data for immediate exploration.")
        if st.button("⚡ Generate Demo Data"):
            generate_sample_mock_data()
            st.cache_data.clear()
            st.rerun()


# ==============================================================================
# TOP HORIZONTAL NAVIGATION BAR (TAB MENU)
# ==============================================================================
selected_page = st.radio(
    "Dashboard Menu",
    options=["Detail Engagement 2026", "Fasilitator Corporate", "Submission 2026"],
    horizontal=True,
    label_visibility="collapsed",
)


# ==============================================================================
# 1. HALAMAN: DETAIL ENGAGEMENT 2026
# ==============================================================================
if selected_page == "Detail Engagement 2026":
    df_raw = load_engagement_data()

    if df_raw is None:
        st.warning("⚠️ File data engagement belum ditemukan. Mengunduh data dari Google Drive...")
        perform_drive_sync()
        st.stop()

    sync_time_str = datetime.datetime.fromtimestamp(
        ENGAGEMENT_CSV_PATH.stat().st_mtime if ENGAGEMENT_CSV_PATH.exists() else LATEST_CSV_PATH.stat().st_mtime
    ).strftime("%d %b %Y, %H:%M")

    # Header Banner
    st.markdown(
        f"""
        <div class="main-header">
            <h1>📊 KLIP Finance Engagement Dashboard 2026</h1>
            <p>Corporate Finance Engagement, Department Breakdown & Performance Analytics • 2026 Period</p>
            <div class="header-pills">
                <span class="pill">⚡ Last Sync: {sync_time_str}</span>
                <span class="pill">👥 Total Dataset: {len(df_raw):,} Employees</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Filter Bar Horizontal
    with st.container(border=True):
        fcol1, fcol2, fcol3, fcol4 = st.columns([1.5, 1, 1.1, 0.9])

        with fcol1:
            all_divisions = sorted([d for d in df_raw["Division"].dropna().unique().tolist() if str(d).strip() not in ["-", ""]]) if "Division" in df_raw.columns else []
            selected_divisions = st.multiselect(
                "Division (Dept)",
                options=all_divisions,
                default=[],
                placeholder="All Divisions (Click to select...)",
                help="Select one or multiple divisions to filter the dashboard.",
            )

        with fcol2:
            status_filter = st.selectbox(
                "Engagement Status",
                options=["All Status", "Engaged", "Non-Engaged"],
                index=0,
                help="Filter records by engagement participation status.",
            )

        with fcol3:
            filter_search = st.text_input(
                "Search Name / ID",
                placeholder="Type employee name or ID...",
                help="Quick search across Employee Name and ID.",
            )

        with fcol4:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            refresh_clicked = st.button("🔄 Refresh Data", type="primary", use_container_width=True, key="refresh_eng")

    if refresh_clicked:
        perform_drive_sync()

    # Filter Data
    df_filtered = df_raw.copy()
    if selected_divisions:
        df_filtered = df_filtered[df_filtered["Division"].isin(selected_divisions)]
    if status_filter and status_filter != "All Status":
        df_filtered = df_filtered[df_filtered["Engagement_Status"] == status_filter]
    if filter_search.strip():
        kw = filter_search.strip().lower()
        df_filtered = df_filtered[
            df_filtered["Employee_Name"].astype(str).str.lower().str.contains(kw, na=False)
            | df_filtered["Employee_ID"].astype(str).str.lower().str.contains(kw, na=False)
        ]

    # Metrics
    total_emp = len(df_filtered)
    engaged_emp = len(df_filtered[df_filtered["Engagement_Status"] == "Engaged"])
    non_engaged_emp = len(df_filtered[df_filtered["Engagement_Status"] == "Non-Engaged"])
    part_rate = (engaged_emp / total_emp * 100) if total_emp > 0 else 0.0
    avg_score = df_filtered["Engagement_Score"].mean() if total_emp > 0 else 0.0

    # KPI Cards Row
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        render_metric_card("Total Employees", f"{total_emp:,}", "Filtered Population", "info")
    with kpi2:
        render_metric_card("Engaged", f"{engaged_emp:,}", f"{part_rate:.1f}% Participated", "info")
    with kpi3:
        render_metric_card("Non-Engaged", f"{non_engaged_emp:,}", f"{100-part_rate:.1f}% Pending", "danger")
    with kpi4:
        render_metric_card("Participation Rate", f"{part_rate:.1f}%", "Target: ≥80%", "info" if part_rate >= 80 else "danger")
    with kpi5:
        render_metric_card("Avg Score", f"{avg_score:.1f}", "Scale: 0-100", "info")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Row 1: Donut Chart & Role Participation Breakdown
    c_left, c_right = st.columns([5, 7])

    with c_left:
        with st.container(border=True):
            st.markdown('<div class="section-title">📊 Overall Participation Rate</div>', unsafe_allow_html=True)
            if total_emp > 0:
                donut_df = pd.DataFrame({
                    "Status": ["Engaged", "Non-Engaged"],
                    "Count": [engaged_emp, non_engaged_emp],
                })
                fig_donut = px.pie(
                    donut_df,
                    names="Status",
                    values="Count",
                    color="Status",
                    color_discrete_map={"Engaged": "#2563EB", "Non-Engaged": "#EF4444"},
                    hole=0.45,
                )
                fig_donut.update_traces(
                    textinfo="percent+value",
                    textposition="inside",
                    insidetextorientation="horizontal",
                    texttemplate="<b>%{value}</b><br>(%{percent:.1%})",
                    insidetextfont=dict(size=14, color="#FFFFFF", family="Plus Jakarta Sans", weight="bold"),
                    marker=dict(line=dict(color="#FFFFFF", width=2)),
                )
                fig_donut.update_layout(
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(family="Plus Jakarta Sans", size=12)),
                    margin=dict(t=10, b=30, l=10, r=10),
                    height=285,
                )
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.info("No data available for the selected filters.")

    with c_right:
        with st.container(border=True):
            st.markdown('<div class="section-title">👥 Role Participation Breakdown</div>', unsafe_allow_html=True)
            leader_count = int(df_filtered["Leader"].sum()) if "Leader" in df_filtered.columns else 0
            sponsor_count = int(df_filtered["Sponsor"].sum()) if "Sponsor" in df_filtered.columns else 0
            member_count = int(df_filtered["Member"].sum()) if "Member" in df_filtered.columns else 0
            fasilitator_count = int(df_filtered["Fasilitator"].sum()) if "Fasilitator" in df_filtered.columns else 0

            leader_unique = int((df_filtered["Leader"] > 0).sum()) if "Leader" in df_filtered.columns else 0
            sponsor_unique = int((df_filtered["Sponsor"] > 0).sum()) if "Sponsor" in df_filtered.columns else 0
            member_unique = int((df_filtered["Member"] > 0).sum()) if "Member" in df_filtered.columns else 0
            fasilitator_unique = int((df_filtered["Fasilitator"] > 0).sum()) if "Fasilitator" in df_filtered.columns else 0

            rcol1, rcol2 = st.columns(2)
            with rcol1:
                render_metric_card("Leader Role", f"{leader_count:,}", f"{(leader_unique/total_emp*100):.1f}% of total" if total_emp > 0 else "0%", "info")
                render_metric_card("Member Role", f"{member_count:,}", f"{(member_unique/total_emp*100):.1f}% of total" if total_emp > 0 else "0%", "info")
            with rcol2:
                render_metric_card("Sponsor Role", f"{sponsor_count:,}", f"{(sponsor_unique/total_emp*100):.1f}% of total" if total_emp > 0 else "0%", "info")
                render_metric_card("Facilitator Role", f"{fasilitator_count:,}", f"{(fasilitator_unique/total_emp*100):.1f}% of total" if total_emp > 0 else "0%", "info")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Row 2: Interactive Single Division Chart
    with st.container(border=True):
        st.markdown('<div class="section-title">🏢 Division Engagement Breakdown</div>', unsafe_allow_html=True)

        chart_col1, chart_col2 = st.columns([1, 1])
        with chart_col1:
            chart_status_view = st.selectbox(
                "Status View",
                options=["All Status", "Show Engaged", "Show Non-Engaged"],
                index=0,
                key="chart_status_view",
            )
        with chart_col2:
            chart_sort_order = st.selectbox(
                "Sort Order",
                options=["Highest to Lowest", "Lowest to Highest"],
                index=0,
                key="chart_sort_order",
            )

        if total_emp > 0 and "Division" in df_filtered.columns:
            div_summary = (
                df_filtered.groupby(["Division", "Engagement_Status"])
                .size()
                .reset_index(name="Count")
            )

            div_totals = df_filtered.groupby("Division").size().reset_index(name="Total")
            div_engaged = df_filtered[df_filtered["Engagement_Status"] == "Engaged"].groupby("Division").size().reset_index(name="Engaged_Count")
            div_non_engaged = df_filtered[df_filtered["Engagement_Status"] == "Non-Engaged"].groupby("Division").size().reset_index(name="NonEngaged_Count")

            merged_div = pd.merge(div_totals, div_engaged, on="Division", how="left").fillna(0)
            merged_div = pd.merge(merged_div, div_non_engaged, on="Division", how="left").fillna(0)

            if chart_status_view == "Show Engaged":
                sort_col = "Engaged_Count"
            elif chart_status_view == "Show Non-Engaged":
                sort_col = "NonEngaged_Count"
            else:
                sort_col = "Total"

            ascending = (chart_sort_order == "Lowest to Highest")
            sorted_divs = merged_div.sort_values(by=sort_col, ascending=ascending)["Division"].tolist()

            div_short_names = {
                "ACCOUNTING OPERATION": "ACC OPS",
                "ACCOUNTS RECEIVABLE & CREDIT MANAGEMENT": "AR & CREDIT",
                "ACCOUNTS PAYABLE": "AP",
                "TREASURY MANAGEMENT": "TREASURY",
                "TAX MANAGEMENT": "TAX",
                "FINANCIAL CONTROL": "FIN CONTROL",
                "GENERAL LEDGER & REPORTING": "GL & REPORTING",
                "FIX ASSET & INVENTORY": "FIXED ASSET",
                "FINANCE OPERATION": "FIN OPS",
                "ACCOUNTING & TAX": "ACC & TAX",
                "FINANCE": "FINANCE",
                "INTERNAL AUDIT": "INT AUDIT",
            }

            if chart_status_view == "Show Engaged":
                plot_data = div_summary[div_summary["Engagement_Status"] == "Engaged"].copy()
                color_map = {"Engaged": "#2563EB"}
            elif chart_status_view == "Show Non-Engaged":
                plot_data = div_summary[div_summary["Engagement_Status"] == "Non-Engaged"].copy()
                color_map = {"Non-Engaged": "#EF4444"}
            else:
                plot_data = div_summary.copy()
                color_map = {"Engaged": "#2563EB", "Non-Engaged": "#EF4444"}

            plot_data["Division_Short"] = plot_data["Division"].map(lambda x: div_short_names.get(x, x))
            sorted_short_divs = [div_short_names.get(d, d) for d in sorted_divs]

            fig_div = px.bar(
                plot_data,
                x="Division_Short",
                y="Count",
                color="Engagement_Status",
                barmode="stack",
                color_discrete_map=color_map,
                category_orders={"Division_Short": sorted_short_divs, "Engagement_Status": ["Non-Engaged", "Engaged"]},
                text="Count",
            )

            fig_div.update_traces(
                textposition="inside",
                insidetextfont=dict(size=12, color="#FFFFFF", family="Plus Jakarta Sans", weight="bold"),
            )

            max_y = merged_div[sort_col].max() if len(merged_div) > 0 else 10
            for d in sorted_divs:
                row_val = merged_div[merged_div["Division"] == d]
                if not row_val.empty:
                    val = int(row_val[sort_col].values[0])
                    short_d = div_short_names.get(d, d)
                    if val > 0:
                        fig_div.add_annotation(
                            x=short_d,
                            y=val,
                            text=f"<b>{val}</b>",
                            showarrow=False,
                            yshift=14,
                            font=dict(family="Plus Jakarta Sans", size=13, color="#0F172A", weight="bold"),
                        )

            fig_div.update_layout(
                yaxis=dict(
                    visible=False,
                    showgrid=False,
                    zeroline=False,
                    range=[0, max_y * 1.25],
                ),
                xaxis=dict(
                    showgrid=False,
                    title=None,
                    tickfont=dict(color="#0F172A", size=11, family="Plus Jakarta Sans", weight="bold"),
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1.0,
                    title=None,
                    font=dict(family="Plus Jakarta Sans", size=12),
                ),
                margin=dict(t=35, b=20, l=10, r=10),
                height=380,
            )
            st.plotly_chart(fig_div, use_container_width=True)
        else:
            st.info("No division data available.")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Row 3: Detail Data Table
    with st.container(border=True):
        st.markdown(f'<div class="section-title">📋 Employee Engagement Records ({len(df_filtered):,} Rows)</div>', unsafe_allow_html=True)

        df_table = df_filtered.copy()
        if "Employee_ID" in df_table.columns:
            df_table["Employee_ID"] = df_table["Employee_ID"].apply(
                lambda x: f"{str(x)[:3]}***" if len(str(x)) > 3 else str(x)
            )

        display_cols = [
            col for col in [
                "Loc_Type", "Employee_ID", "Employee_Name", "Status_PA", "Engagement_Status",
                "Leader", "Sponsor", "Member", "Fasilitator", "Directorate", "Division",
                "Company_Name", "Engagement_Score", "Completion_Date",
            ] if col in df_table.columns
        ]

        st.dataframe(
            df_table[display_cols],
            use_container_width=True,
            height=450,
            column_config={
                "Loc_Type": st.column_config.TextColumn("𝗟𝗼𝗰𝗮𝘁𝗶𝗼𝗻", width="small"),
                "Employee_ID": st.column_config.TextColumn("𝗡𝗜𝗞 / 𝗜𝗗", width="medium"),
                "Employee_Name": st.column_config.TextColumn("𝗘𝗺𝗽𝗹𝗼𝘆𝗲𝗲 𝗡𝗮𝗺𝗲", width="large"),
                "Status_PA": st.column_config.TextColumn("𝗦𝘁𝗮𝘁𝘂𝘀 𝗣𝗔", width="small"),
                "Engagement_Status": st.column_config.TextColumn("𝗦𝘁𝗮𝘁𝘂𝘀", width="medium"),
                "Leader": st.column_config.NumberColumn("𝗟𝗲𝗮𝗱𝗲𝗿", width="small", format="%d"),
                "Sponsor": st.column_config.NumberColumn("𝗦𝗽𝗼𝗻𝘀𝗼𝗿", width="small", format="%d"),
                "Member": st.column_config.NumberColumn("𝗠𝗲𝗺𝗯𝗲𝗿", width="small", format="%d"),
                "Fasilitator": st.column_config.NumberColumn("𝗙𝗮𝘀𝗶𝗹𝗶𝘁𝗮𝘁𝗼𝗿", width="small", format="%d"),
                "Directorate": st.column_config.TextColumn("𝗗𝗶𝗿𝗲𝗰𝘁𝗼𝗿𝗮𝘁𝗲", width="medium"),
                "Division": st.column_config.TextColumn("𝗗𝗶𝘃𝗶𝘀𝗶𝗼𝗻", width="large"),
                "Company_Name": st.column_config.TextColumn("𝗖𝗼𝗺𝗽𝗮𝗻𝘆", width="medium"),
                "Engagement_Score": st.column_config.ProgressColumn(
                    "𝗘𝗻𝗴𝗮𝗴𝗲𝗺𝗲𝗻𝘁 𝗦𝗰𝗼𝗿𝗲",
                    help="Employee Participation Score (0 - 100)",
                    format="%d",
                    min_value=0,
                    max_value=100,
                ),
                "Completion_Date": st.column_config.TextColumn("𝗖𝗼𝗺𝗽𝗹𝗲𝘁𝗶𝗼𝗻 𝗗𝗮𝘁𝗲", width="small"),
            },
            hide_index=True,
        )


# ==============================================================================
# 2. HALAMAN: FASILITATOR CORPORATE
# ==============================================================================
elif selected_page == "Fasilitator Corporate":
    df_fas_raw = load_fasilitator_data()

    if df_fas_raw is None:
        st.warning("⚠️ File data Fasilitator belum ditemukan. Mengunduh data dari Google Drive...")
        perform_drive_sync()
        st.stop()

    sync_time_str = datetime.datetime.fromtimestamp(FASILITATOR_CSV_PATH.stat().st_mtime).strftime("%d %b %Y, %H:%M") if FASILITATOR_CSV_PATH.exists() else "-"

    # Header Banner
    st.markdown(
        f"""
        <div class="main-header">
            <h1>👥 KLIP Corporate Facilitator Performance 2026</h1>
            <p>Corporate Facilitator Activity, Project Submission & Completion Tracking • 2026 Period</p>
            <div class="header-pills">
                <span class="pill">⚡ Last Sync: {sync_time_str}</span>
                <span class="pill">👥 Total Facilitators: {len(df_fas_raw):,} Persons</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Filter Bar
    with st.container(border=True):
        fcol1, fcol2, fcol3 = st.columns([1.5, 1.5, 1])

        with fcol1:
            all_funcs = sorted(df_fas_raw["Function"].dropna().unique().tolist()) if "Function" in df_fas_raw.columns else []
            selected_func = st.selectbox("Function / Department", options=["All Functions"] + all_funcs, index=0)

        with fcol2:
            fas_search = st.text_input("Search Facilitator Name", placeholder="Type facilitator name...")

        with fcol3:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            refresh_clicked = st.button("🔄 Refresh Data", type="primary", use_container_width=True, key="refresh_fas")

    if refresh_clicked:
        perform_drive_sync()

    # Filter Data
    df_fas = df_fas_raw.copy()
    if selected_func != "All Functions":
        df_fas = df_fas[df_fas["Function"] == selected_func]
    if fas_search.strip():
        df_fas = df_fas[df_fas["Nama"].astype(str).str.lower().str.contains(fas_search.strip().lower(), na=False)]

    # Metrics
    tot_facilitators = len(df_fas)
    tot_submitted = int(df_fas["Submitted 2026"].sum()) if "Submitted 2026" in df_fas.columns else 0
    tot_registered = int(df_fas["Registered 2026"].sum()) if "Registered 2026" in df_fas.columns else 0
    tot_finished = int(df_fas["Finished 2026"].sum()) if "Finished 2026" in df_fas.columns else 0
    overall_fin_rate = (tot_finished / tot_submitted * 100) if tot_submitted > 0 else 0.0

    # KPI Cards
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        render_metric_card("Total Facilitators", f"{tot_facilitators:,}", "Active Facilitators", "info")
    with kpi2:
        render_metric_card("Total Submitted (2026)", f"{tot_submitted:,}", "All Project Submissions", "info")
    with kpi3:
        render_metric_card("Registered (2026)", f"{tot_registered:,}", f"{(tot_registered/tot_submitted*100):.1f}% of submitted" if tot_submitted > 0 else "0%", "danger")
    with kpi4:
        render_metric_card("Finished (2026)", f"{tot_finished:,}", f"{(tot_finished/tot_submitted*100):.1f}% of submitted" if tot_submitted > 0 else "0%", "info")
    with kpi5:
        render_metric_card("Overall % Finished", f"{overall_fin_rate:.1f}%", "Completion Metric", "info" if overall_fin_rate >= 50 else "danger")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Chart Facilitator Performance
    with st.container(border=True):
        st.markdown('<div class="section-title">📊 Facilitator Project Progression Comparison (Submitted vs Registered vs Finished)</div>', unsafe_allow_html=True)
        if len(df_fas) > 0:
            df_chart = df_fas.sort_values(by="Submitted 2026", ascending=True).copy()
            
            fig_fas = go.Figure()
            fig_fas.add_trace(go.Bar(
                y=df_chart["Nama"],
                x=df_chart["Submitted 2026"],
                name="Submitted",
                orientation="h",
                marker_color="#2563EB",
                text=df_chart["Submitted 2026"],
                textposition="inside",
                insidetextfont=dict(color="#FFFFFF", weight="bold"),
            ))
            fig_fas.add_trace(go.Bar(
                y=df_chart["Nama"],
                x=df_chart["Registered 2026"],
                name="Registered (Pending)",
                orientation="h",
                marker_color="#EF4444",
                text=df_chart["Registered 2026"],
                textposition="inside",
                insidetextfont=dict(color="#FFFFFF", weight="bold"),
            ))
            fig_fas.add_trace(go.Bar(
                y=df_chart["Nama"],
                x=df_chart["Finished 2026"],
                name="Finished (Done)",
                orientation="h",
                marker_color="#1D4ED8",
                text=df_chart["Finished 2026"],
                textposition="inside",
                insidetextfont=dict(color="#FFFFFF", weight="bold"),
            ))

            fig_fas.update_layout(
                barmode="group",
                xaxis=dict(showgrid=False, title=None, tickfont=dict(family="Plus Jakarta Sans", size=11, color="#0F172A", weight="bold")),
                yaxis=dict(showgrid=False, tickfont=dict(family="Plus Jakarta Sans", size=11, color="#0F172A", weight="bold")),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0, font=dict(family="Plus Jakarta Sans", size=12)),
                margin=dict(t=30, b=20, l=10, r=10),
                height=max(380, len(df_chart) * 28),
            )
            st.plotly_chart(fig_fas, use_container_width=True)
        else:
            st.info("No facilitator records available for the selected filters.")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Table Facilitator Performance
    with st.container(border=True):
        st.markdown(f'<div class="section-title">📋 Facilitator Performance Master Table ({len(df_fas):,} Persons)</div>', unsafe_allow_html=True)
        st.dataframe(
            df_fas[["Nama", "Function", "Submitted 2026", "Registered 2026", "Finished 2026", "%Finished"]],
            use_container_width=True,
            height=450,
            column_config={
                "Nama": st.column_config.TextColumn("𝗙𝗮𝘀𝗶𝗹𝗶𝘁𝗮𝘁𝗼𝗿 𝗡𝗮𝗺𝗲", width="large"),
                "Function": st.column_config.TextColumn("𝗙𝘂𝗻𝗰𝘁𝗶𝗼𝗻 / 𝗗𝗲𝗽𝘁", width="large"),
                "Submitted 2026": st.column_config.NumberColumn("𝗦𝘂𝗯𝗺𝗶𝘁𝘁𝗲𝗱 (𝟮𝟬𝟮𝟲)", width="small", format="%d"),
                "Registered 2026": st.column_config.NumberColumn("𝗥𝗲𝗴𝗶𝘀𝘁𝗲𝗿𝗲𝗱 (𝟮𝟬𝟮𝟲)", width="small", format="%d"),
                "Finished 2026": st.column_config.NumberColumn("𝗙𝗶𝗻𝗶𝘀𝗵𝗲𝗱 (𝟮𝟬𝟮𝟲)", width="small", format="%d"),
                "%Finished": st.column_config.TextColumn("% 𝗙𝗶𝗻𝗶𝘀𝗵𝗲𝗱 𝗥𝗮𝘁𝗲", width="medium"),
            },
            hide_index=True,
        )


# ==============================================================================
# 3. HALAMAN: SUBMISSION 2026
# ==============================================================================
elif selected_page == "Submission 2026":
    df_sub_raw = load_submission_data()

    if df_sub_raw is None:
        st.warning("⚠️ File data Submission belum ditemukan. Mengunduh data dari Google Drive...")
        perform_drive_sync()
        st.stop()

    sync_time_str = datetime.datetime.fromtimestamp(SUBMISSION_CSV_PATH.stat().st_mtime).strftime("%d %b %Y, %H:%M") if SUBMISSION_CSV_PATH.exists() else "-"

    # Header Banner
    st.markdown(
        f"""
        <div class="main-header">
            <h1>📝 KLIP Submission & Project Monitoring 2026</h1>
            <p>Project Pipeline, Stage Progress, Monthly Ingestion & Implementation Monitoring</p>
            <div class="header-pills">
                <span class="pill">⚡ Last Sync: {sync_time_str}</span>
                <span class="pill">📑 Total Projects: {len(df_sub_raw):,} Submissions</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Filter Bar
    with st.container(border=True):
        fcol1, fcol2, fcol3, fcol4 = st.columns([1.2, 1.2, 1.4, 0.9])

        with fcol1:
            all_stages = ["All Stages", "PROPOSAL", "IMPLEMENTATION", "CLOSING", "FINISHED"]
            selected_stage = st.selectbox("KLIP Stage", options=all_stages, index=0)

        with fcol2:
            all_funcs = ["All Functions"] + sorted(df_sub_raw["Function"].dropna().unique().tolist()) if "Function" in df_sub_raw.columns else ["All Functions"]
            selected_func = st.selectbox("Function", options=all_funcs, index=0)

        with fcol3:
            sub_search = st.text_input("Search Title / No.KLIP / Leader / Fasilitator", placeholder="Search project keyword...")

        with fcol4:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            refresh_clicked = st.button("🔄 Refresh Data", type="primary", use_container_width=True, key="refresh_sub")

    if refresh_clicked:
        perform_drive_sync()

    # Filter Data
    df_sub = df_sub_raw.copy()
    if selected_stage != "All Stages":
        df_sub = df_sub[df_sub["Stage"] == selected_stage]
    if selected_func != "All Functions":
        df_sub = df_sub[df_sub["Function"] == selected_func]
    if sub_search.strip():
        kw = sub_search.strip().lower()
        df_sub = df_sub[
            df_sub["Title"].astype(str).str.lower().str.contains(kw, na=False)
            | df_sub["No.KLIP"].astype(str).str.lower().str.contains(kw, na=False)
            | df_sub["Leader_Name"].astype(str).str.lower().str.contains(kw, na=False)
            | df_sub["Fasilitator_Name"].astype(str).str.lower().str.contains(kw, na=False)
        ]

    # Metrics
    tot_sub = len(df_sub)
    proposal_cnt = len(df_sub[df_sub["Stage"] == "PROPOSAL"])
    impl_cnt = len(df_sub[df_sub["Stage"] == "IMPLEMENTATION"])
    closing_cnt = len(df_sub[df_sub["Stage"] == "CLOSING"])
    finished_cnt = len(df_sub[df_sub["Stage"] == "FINISHED"])

    # KPI Cards
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        render_metric_card("Total Submissions", f"{tot_sub:,}", "Active Pipeline", "info")
    with kpi2:
        render_metric_card("Proposal Stage", f"{proposal_cnt:,}", f"{(proposal_cnt/tot_sub*100):.1f}% of total" if tot_sub > 0 else "0%", "danger")
    with kpi3:
        render_metric_card("Implementation", f"{impl_cnt:,}", f"{(impl_cnt/tot_sub*100):.1f}% of total" if tot_sub > 0 else "0%", "danger")
    with kpi4:
        render_metric_card("Closing Stage", f"{closing_cnt:,}", f"{(closing_cnt/tot_sub*100):.1f}% of total" if tot_sub > 0 else "0%", "danger")
    with kpi5:
        render_metric_card("Finished", f"{finished_cnt:,}", f"{(finished_cnt/tot_sub*100):.1f}% completed" if tot_sub > 0 else "0%", "info")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Charts: Side-by-Side
    c1, c2 = st.columns([5, 7])

    with c1:
        with st.container(border=True):
            st.markdown('<div class="section-title">📊 KLIP by Stage Distribution</div>', unsafe_allow_html=True)
            if tot_sub > 0:
                stage_counts = df_sub["Stage"].value_counts().reset_index()
                stage_counts.columns = ["Stage", "Count"]

                stage_colors = {
                    "PROPOSAL": "#FCA5A5",
                    "IMPLEMENTATION": "#F87171",
                    "CLOSING": "#EF4444",
                    "FINISHED": "#2563EB",
                }

                fig_stage = px.pie(
                    stage_counts,
                    names="Stage",
                    values="Count",
                    color="Stage",
                    color_discrete_map=stage_colors,
                    hole=0.45,
                )
                fig_stage.update_traces(
                    textinfo="percent+value",
                    textposition="inside",
                    insidetextorientation="horizontal",
                    texttemplate="<b>%{value}</b><br>(%{percent:.1%})",
                    insidetextfont=dict(size=13, color="#FFFFFF", family="Plus Jakarta Sans", weight="bold"),
                    marker=dict(line=dict(color="#FFFFFF", width=2)),
                )
                fig_stage.update_layout(
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(family="Plus Jakarta Sans", size=12)),
                    margin=dict(t=10, b=30, l=10, r=10),
                    height=300,
                )
                st.plotly_chart(fig_stage, use_container_width=True)
            else:
                st.info("No stage distribution data available.")

    with c2:
        with st.container(border=True):
            st.markdown('<div class="section-title">📅 Submission by Month (Jan – Aug 2026)</div>', unsafe_allow_html=True)
            if tot_sub > 0 and "Month" in df_sub.columns:
                month_order = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
                month_counts = df_sub["Month"].value_counts().reindex([m for m in month_order if m in df_sub["Month"].values]).fillna(0).reset_index()
                month_counts.columns = ["Month", "Count"]

                fig_month = px.bar(
                    month_counts,
                    x="Month",
                    y="Count",
                    text="Count",
                    color_discrete_sequence=["#2563EB"],
                )
                fig_month.update_traces(
                    textposition="inside",
                    insidetextfont=dict(size=12, color="#FFFFFF", family="Plus Jakarta Sans", weight="bold"),
                )

                max_m = month_counts["Count"].max() if len(month_counts) > 0 else 5
                for _, r in month_counts.iterrows():
                    if r["Count"] > 0:
                        fig_month.add_annotation(
                            x=r["Month"],
                            y=r["Count"],
                            text=f"<b>{int(r['Count'])}</b>",
                            showarrow=False,
                            yshift=12,
                            font=dict(family="Plus Jakarta Sans", size=12, color="#0F172A", weight="bold"),
                        )

                fig_month.update_layout(
                    yaxis=dict(visible=False, showgrid=False, zeroline=False, range=[0, max_m * 1.3]),
                    xaxis=dict(showgrid=False, title=None, tickfont=dict(family="Plus Jakarta Sans", size=11, color="#0F172A", weight="bold")),
                    margin=dict(t=30, b=20, l=10, r=10),
                    height=300,
                )
                st.plotly_chart(fig_month, use_container_width=True)
            else:
                st.info("No monthly trend data available.")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Table Submissions
    with st.container(border=True):
        st.markdown(f'<div class="section-title">📋 KLIP Project Submissions Master Table ({len(df_sub):,} Projects)</div>', unsafe_allow_html=True)

        display_sub_cols = [
            c for c in [
                "No.KLIP", "Title", "Leader_Name", "Fasilitator_Name", "Function",
                "Stage", "Status", "Submitted", "Registered", "Finished",
            ] if c in df_sub.columns
        ]

        st.dataframe(
            df_sub[display_sub_cols],
            use_container_width=True,
            height=450,
            column_config={
                "No.KLIP": st.column_config.TextColumn("𝗡𝗼. 𝗞𝗟𝗜𝗣", width="medium"),
                "Title": st.column_config.TextColumn("𝗣𝗿𝗼𝗷𝗲𝗰𝘁 𝗧𝗶𝘁𝗹𝗲", width="large"),
                "Leader_Name": st.column_config.TextColumn("𝗟𝗲𝗮𝗱𝗲𝗿", width="medium"),
                "Fasilitator_Name": st.column_config.TextColumn("𝗙𝗮𝘀𝗶𝗹𝗶𝘁𝗮𝘁𝗼𝗿", width="medium"),
                "Function": st.column_config.TextColumn("𝗙𝘂𝗻𝗰𝘁𝗶𝗼𝗻", width="medium"),
                "Stage": st.column_config.TextColumn("𝗦𝘁𝗮𝗴𝗲", width="small"),
                "Status": st.column_config.TextColumn("𝗦𝘁𝗮𝘁𝘂𝘀", width="medium"),
                "Submitted": st.column_config.TextColumn("𝗦𝘂𝗯𝗺𝗶𝘁𝘁𝗲𝗱", width="small"),
                "Registered": st.column_config.TextColumn("𝗥𝗲𝗴𝗶𝘀𝘁𝗲𝗿𝗲𝗱", width="small"),
                "Finished": st.column_config.TextColumn("𝗙𝗶𝗻𝗶𝘀𝗵𝗲𝗱", width="small"),
            },
            hide_index=True,
        )

# ==============================================================================
# FOOTER
# ==============================================================================
st.markdown(
    """
    <div style="text-align: center; color: #94A3B8; font-size: 0.8rem; margin-top: 35px; padding: 20px 0; border-top: 1px solid #E2E8F0;">
        KLIP Analytics Multi-Page Dashboard © 2026 • Corporate Finance Analytics Engine • Powered by Streamlit & Plotly
    </div>
    """,
    unsafe_allow_html=True,
)
