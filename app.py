"""
App: app.py
Deskripsi: Dashboard Interaktif Streamlit untuk Analisis KLIP Engagement (CORP-FINANCE)
            Mengambil data CSV otomatis dari Google Drive.
"""

import os
import sys
import datetime
from pathlib import Path
from typing import Optional

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Import modul fetch Google Drive
from fetch_drive_data import (
    DEFAULT_FOLDER_ID,
    DEFAULT_TARGET_FILENAME,
    LATEST_CSV_PATH,
    download_klip_data_from_drive,
    generate_sample_mock_data,
)

# ==============================================================================
# KONFIGURASI HALAMAN STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="KLIP Engagement Dashboard | CORP-FINANCE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
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
        background-color: #DCFCE7;
        color: #15803D;
    }
    .badge-danger {
        background-color: #FEE2E2;
        color: #B91C1C;
    }
    .badge-info {
        background-color: #E0E7FF;
        color: #4338CA;
    }

    /* Header Banner */
    .main-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: #FFFFFF;
        padding: 22px 28px;
        border-radius: 14px;
        margin-bottom: 20px;
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

    /* Berikan ruang scroll bawah masif pada sidebar agar dropdown tidak pernah mentok */
    section[data-testid="stSidebar"] div[data-testid="stSidebarContent"],
    section[data-testid="stSidebar"] .block-container {
        padding-bottom: 400px !important;
    }

    /* Perluas tinggi maksimum menu dropdown/selectbox saat diklik */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    div[data-baseweb="popover"] div[role="listbox"],
    div[data-baseweb="select"] ul,
    div[data-baseweb="popover"] ul,
    ul[data-baseweb="menu"] {
        max-height: 480px !important;
        z-index: 999999 !important;
    }

    /* Optimasi Tampilan Layar HP / Mobile */
    @media (max-width: 768px) {
        /* Paksa st.columns (KPI Cards & Role Cards) menjadi 2 kolom di HP */
        [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
            gap: 0.5rem !important;
        }

        [data-testid="column"] {
            width: calc(50% - 0.5rem) !important;
            flex: 1 1 calc(50% - 0.5rem) !important;
            min-width: calc(50% - 0.5rem) !important;
        }
        
        /* Kurangi padding card agar hemat ruang layar HP */
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
        
        /* Kurangi padding container utama di HP */
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 1rem !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# FUNGSI PEMUATAN & NORMALISASI DATA (CACHED)
# ==============================================================================
@st.cache_data(show_spinner=False)
def load_klip_data(file_path: str = str(LATEST_CSV_PATH)) -> Optional[pd.DataFrame]:
    """
    Membaca dan menormalisasi dataset CSV KLIP Engagement.
    Menggunakan decorator @st.cache_data untuk loading instan.
    """
    csv_file = Path(file_path)
    if not csv_file.exists() or csv_file.stat().st_size == 0:
        return None

    try:
        # Coba beberapa variasi delimiter jika format berbeda
        try:
            df = pd.read_csv(csv_file)
        except Exception:
            df = pd.read_csv(csv_file, sep=";")

        # Standardisasi Nama Kolom secara cerdas tanpa duplikasi target
        col_mapping = {}
        assigned_targets = set()

        for col in df.columns:
            clean = str(col).strip().lower().replace(" ", "_").replace("/", "_").replace(".", "_")
            target = None

            # Prioritas 1: Company / Perusahaan (Dicek sebelum Name)
            if clean in ["company_name", "company", "perusahaan", "pt", "holding"] or ("company" in clean or "perusahaan" in clean):
                target = "Company_Name"
            # Prioritas 2: Employee ID / NIK
            elif clean in ["employee_id", "nik", "id_karyawan", "no_pegawai", "emp_id"] or ("nik" in clean or "id_karyawan" in clean or "emp_id" in clean):
                target = "Employee_ID"
            # Prioritas 3: Employee Name / Nama Karyawan (Cek agar tidak bentrok dengan Company Name)
            elif clean in ["employee_name", "nama_karyawan", "nama_pegawai", "nama", "employee"] or ("employee" in clean and "id" not in clean) or ("nama" in clean and "perusahaan" not in clean):
                target = "Employee_Name"
            # Prioritas 4: Directorate
            elif clean in ["directorate", "direktorat", "dir"] or ("directorate" in clean or "direktorat" in clean):
                target = "Directorate"
            # Prioritas 5: Division
            elif clean in ["division", "divisi", "div"] or ("division" in clean or "divisi" in clean):
                target = "Division"
            # Prioritas 6: Group BU / CORP
            elif any(k in clean for k in ["group_bu", "bu_corp", "group_corp", "bu", "group"]):
                target = "Group_BU_CORP"
            # Prioritas 7: Engagement Status
            elif clean in ["engagement", "status", "engagement_status", "status_engagement", "klip_status", "klip_engagement"] or ("engagement" in clean or "status" in clean):
                target = "Engagement_Status"
            # Prioritas 8: Status PA (Eligible PA)
            elif clean in ["sttspa", "status_pa", "stts_pa", "status pa", "pa_status"]:
                target = "Status_PA"
            # Prioritas 9: Roles (Leader, Sponsor, Member, Fasilitator)
            elif clean in ["leader", "as_leader", "as_a_leader"]:
                target = "Leader"
            elif clean in ["sponsor", "as_sponsor", "as_a_sponsor"]:
                target = "Sponsor"
            elif clean in ["member", "as_member", "as_a_member"]:
                target = "Member"
            elif clean in ["fasilitator", "facilitator", "as_fasilitator", "as_a_fasilitator"]:
                target = "Fasilitator"
            # Prioritas 10: Engagement Score
            elif any(k in clean for k in ["score", "nilai", "skor"]):
                target = "Engagement_Score"
            # Prioritas 11: Location
            elif any(k in clean for k in ["loc", "lokasi", "location"]):
                target = "Loc_Type"
            # Prioritas 12: Completion Date
            elif any(k in clean for k in ["date", "tanggal", "completion"]):
                target = "Completion_Date"

            if target and target not in assigned_targets:
                col_mapping[col] = target
                assigned_targets.add(target)

        df = df.rename(columns=col_mapping)

        # Hapus kolom duplikat jika ada
        df = df.loc[:, ~df.columns.duplicated()].copy()

        # Fallback kolom jika tidak ada di dataset
        if "Employee_ID" not in df.columns:
            df["Employee_ID"] = [f"EMP-{1000 + i}" for i in range(len(df))]
        if "Employee_Name" not in df.columns:
            str_cols = df.select_dtypes(include=["object"]).columns
            df["Employee_Name"] = df[str_cols[0]] if len(str_cols) > 0 else "Karyawan"
        if "Directorate" not in df.columns:
            df["Directorate"] = "FINANCE"
        if "Division" not in df.columns:
            df["Division"] = "General Finance"
        if "Company_Name" not in df.columns:
            df["Company_Name"] = "CORPORATE"
        if "Engagement_Status" not in df.columns:
            df["Engagement_Status"] = "Engaged"

        # Bersihkan dan Normalisasi Nilai Engagement_Status secara presisi
        def normalize_status(val):
            if pd.isna(val):
                return "Non-Engaged"
            s = str(val).strip().lower()
            if s in ["1", "1.0", "true", "engaged", "sudah", "yes", "selesai", "ikut", "completed", "active"]:
                return "Engaged"
            elif s in ["0", "0.0", "false", "non-engaged", "non engaged", "not engaged", "belum", "no", "inactive", "non"]:
                return "Non-Engaged"
            if "non" in s or "not" in s or "belum" in s or "unengaged" in s:
                return "Non-Engaged"
            if "engage" in s:
                return "Engaged"
            return "Non-Engaged"

        # Normalisasi Engagement_Status aman
        if "Engagement_Status" in df.columns:
            s_stat = df["Engagement_Status"]
            if isinstance(s_stat, pd.DataFrame):
                s_stat = s_stat.iloc[:, 0]
            df["Engagement_Status"] = s_stat.apply(normalize_status)

        # Bersihkan spasi string untuk kolom teks penting tanpa menghilangkan data
        for col in ["Employee_ID", "Employee_Name", "Directorate", "Division", "Company_Name", "Loc_Type", "Status_PA"]:
            if col in df.columns:
                s_col = df[col]
                if isinstance(s_col, pd.DataFrame):
                    s_col = s_col.iloc[:, 0]
                df[col] = s_col.fillna("-").astype(str).str.strip()
                df[col] = df[col].replace("", "-").replace("nan", "-").replace("None", "-")

        # Standardisasi Singkatan Nama Divisi untuk visualisasi horizontal
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
        }
        if "Division" in df.columns:
            df["Division_Short"] = df["Division"].apply(
                lambda x: div_short_names.get(str(x).strip().upper(), div_short_names.get(str(x).strip(), str(x).strip()))
            )
        else:
            df["Division_Short"] = "-"

        return df

    except Exception as e:
        st.error(f"Gagal memproses file CSV: {e}")
        return None


# ==============================================================================
# SIDEBAR CONTROLS & FILTER
# ==============================================================================
with st.sidebar:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
            <div style="background: #2563EB; color: white; border-radius: 8px; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; font-weight: bold;">
                📊
            </div>
            <div>
                <h3 style="margin: 0; font-size: 1.1rem; font-weight: 700; color: #1E293B;">KLIP Analytics</h3>
                <span style="font-size: 0.75rem; color: #64748B; font-weight: 500;">Google Drive Ingestion Engine</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Status Data & Refresh Section
    st.markdown("### 🔄 Data Synchronization")
    
    # Check local file status
    file_exists = LATEST_CSV_PATH.exists()
    last_mod_time = "-"
    if file_exists:
        mtime = os.path.getmtime(LATEST_CSV_PATH)
        last_mod_time = datetime.datetime.fromtimestamp(mtime).strftime("%d-%m-%Y %H:%M:%S")

    st.markdown(
        f"""
        <div style="background: #F1F5F9; border-radius: 8px; padding: 10px 12px; margin-bottom: 12px; font-size: 0.8rem;">
            <div style="color: #475569;">🕒 <b>Last Update:</b> {last_mod_time}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    refresh_clicked = st.button("🔄 Refresh Data from Drive", type="primary", use_container_width=True)

    with st.expander("⚙️ Google Drive Configuration", expanded=False):
        folder_id_input = st.text_input(
            "Google Drive Folder ID",
            value=DEFAULT_FOLDER_ID,
            help="Google Drive Folder ID where CSV files are hosted.",
        )
        target_filename_input = st.text_input(
            "Target CSV Filename",
            value=DEFAULT_TARGET_FILENAME,
            help="CSV target filename to ingest from the folder.",
        )

    st.markdown("---")

    # Load data for dynamic filter populating
    df_raw = load_klip_data()

    # Filter Section
    st.markdown("### 🔍 Filter Data")

    # 1. Division Filter (Positioned first with ample room to open upward/downward)
    if df_raw is not None and len(df_raw) > 0 and "Division" in df_raw.columns:
        all_divisions = sorted([d for d in df_raw["Division"].dropna().unique().tolist() if str(d).strip() not in ["-", ""]])
        division_options = ["All Division"] + all_divisions
    else:
        division_options = ["All Division"]

    selected_division = st.selectbox(
        "Division",
        options=division_options,
        index=0,
        help="Filter records by a specific division or select 'All Division' to view everything.",
    )

    # 2. Engagement Status Filter
    status_filter = st.selectbox(
        "Engagement Status",
        options=["All Status", "Engaged", "Non-Engaged"],
        index=0,
        help="Filter records by engagement participation status."
    )

    # 3. Search Filter
    filter_search = st.text_input(
        "Search Name / ID",
        placeholder="Type employee name or ID...",
        help="Quick search across Employee Name and ID."
    )

    # Spacer at bottom of sidebar to prevent any dropdown clipping
    st.markdown("<div style='height: 350px;'></div>", unsafe_allow_html=True)


# ==============================================================================
# GOOGLE DRIVE SYNC LOGIC (TRIGGERED BY REFRESH BUTTON)
# ==============================================================================
if refresh_clicked:
    with st.spinner("⏳ Downloading and synchronizing CSV from Google Drive..."):
        success, message, result_path = download_klip_data_from_drive(
            folder_id=folder_id_input,
            target_filename=target_filename_input,
            dest_path=LATEST_CSV_PATH,
        )

    if success:
        st.cache_data.clear()
        st.toast("✅ Data successfully synced from Google Drive!", icon="🎉")
        st.success(f"**Success!** {message}")
        st.rerun()
    else:
        st.error(f"**Sync Failed:**\n\n{message}")
        if not LATEST_CSV_PATH.exists():
            st.info("💡 Click below to generate simulated demo data for immediate exploration.")
            if st.button("⚡ Generate Demo Data"):
                generate_sample_mock_data(LATEST_CSV_PATH)
                st.cache_data.clear()
                st.rerun()


# ==============================================================================
# DATA VALIDATION & FILTERING
# ==============================================================================
# Handle missing data file
if df_raw is None or len(df_raw) == 0:
    st.markdown(
        """
        <div class="main-header">
            <h1>📊 KLIP Finance Engagement Dashboard</h1>
            <p>Real-Time Corporate Finance Employee Engagement Monitoring</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.warning("⚠️ **Data file is not available locally (`./data/klip_finance_latest.csv`).**")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            f"""
            #### 1. Sync from Google Drive
            Click button in sidebar to download from Folder ID:
            - **Folder ID:** `{DEFAULT_FOLDER_ID}`
            - **Target File:** `{DEFAULT_TARGET_FILENAME}`
            
            *(Ensure folder access is set to **'Anyone with the link'** on Google Drive)*
            """
        )
        if st.button("📥 Download Now from Google Drive", type="primary"):
            with st.spinner("Downloading..."):
                ok, msg, _ = download_klip_data_from_drive()
                if ok:
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(msg)
    
    with col_b:
        st.markdown(
            """
            #### 2. Simulation / Demo Data Mode
            Use realistic mock dataset to test visualizations instantly.
            """
        )
        if st.button("🚀 Generate Demo Data"):
            generate_sample_mock_data(LATEST_CSV_PATH)
            st.cache_data.clear()
            st.rerun()

    st.stop()


# Apply filters safely
df_filtered = df_raw.copy()

if selected_division and selected_division != "All Division":
    df_filtered = df_filtered[df_filtered["Division"] == selected_division]

if status_filter and status_filter != "All Status":
    df_filtered = df_filtered[df_filtered["Engagement_Status"] == status_filter]

if filter_search.strip():
    kw = filter_search.strip().lower()
    df_filtered = df_filtered[
        df_filtered["Employee_Name"].astype(str).str.lower().str.contains(kw, na=False)
        | df_filtered["Employee_ID"].astype(str).str.lower().str.contains(kw, na=False)
    ]


# ==============================================================================
# TOP HEADER BANNER
# ==============================================================================
total_all = len(df_raw)
total_filtered = len(df_filtered)

st.markdown(
    f"""
    <div class="main-header">
        <h1>📊 KLIP Finance Engagement Dashboard 2026</h1>
        <p>Real-Time Corporate Finance Employee Engagement Monitoring via Google Drive Ingestion</p>
        <div class="header-pills">
            <span class="pill">🕒 <b>Last Sync:</b> {last_mod_time}</span>
            <span class="pill">👥 <b>Total Dataset:</b> {total_all:,} Employees</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# KPI METRICS CARDS
# ==============================================================================
engaged_count = int((df_filtered["Engagement_Status"] == "Engaged").sum())
non_engaged_count = int((df_filtered["Engagement_Status"] == "Non-Engaged").sum())
engagement_rate = (engaged_count / total_filtered * 100) if total_filtered > 0 else 0
non_engagement_rate = (non_engaged_count / total_filtered * 100) if total_filtered > 0 else 0
total_dirs_count = df_filtered["Directorate"].nunique()
total_divs_count = df_filtered["Division"].nunique()

mcol1, mcol2, mcol3, mcol4 = st.columns(4)

with mcol1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">TOTAL EMPLOYEES</div>
            <div class="metric-value">{total_filtered:,}</div>
            <div>
                <span class="metric-badge badge-info">From {total_all:,} total records</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with mcol2:
    st.markdown(
        f"""
        <div class="metric-card" style="border-left: 4px solid #10B981;">
            <div class="metric-title">ENGAGED</div>
            <div class="metric-value" style="color: #059669;">{engaged_count:,}</div>
            <div>
                <span class="metric-badge badge-success">✓ {engagement_rate:.1f}% Participation</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with mcol3:
    st.markdown(
        f"""
        <div class="metric-card" style="border-left: 4px solid #EF4444;">
            <div class="metric-title">NON-ENGAGED</div>
            <div class="metric-value" style="color: #DC2626;">{non_engaged_count:,}</div>
            <div>
                <span class="metric-badge badge-danger">✕ {non_engagement_rate:.1f}% Pending</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with mcol4:
    st.markdown(
        f"""
        <div class="metric-card" style="border-left: 4px solid #6366F1;">
            <div class="metric-title">ORGANIZATION COVERAGE</div>
            <div class="metric-value" style="color: #4F46E5;">{total_divs_count} <span style="font-size: 1rem; font-weight: 500; color: #64748B;">Divisions</span></div>
            <div>
                <span class="metric-badge badge-info">🏢 {total_dirs_count} Directorate</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Role Breakdown Badges (if available in CSV)
role_cols = [c for c in ["Leader", "Sponsor", "Member", "Fasilitator"] if c in df_filtered.columns]
if role_cols:
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    rcol1, rcol2, rcol3, rcol4 = st.columns(4)
    with rcol1:
        leader_cnt = int(pd.to_numeric(df_filtered["Leader"], errors="coerce").fillna(0).sum()) if "Leader" in df_filtered.columns else 0
        st.markdown(
            f"""
            <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 10px; padding: 10px 14px; text-align: center;">
                <span style="font-size: 0.75rem; color: #1E40AF; font-weight: 600; text-transform: uppercase;">👑 AS A LEADER</span>
                <div style="font-size: 1.35rem; font-weight: 800; color: #1D4ED8; margin-top: 2px;">{leader_cnt}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with rcol2:
        sponsor_cnt = int(pd.to_numeric(df_filtered["Sponsor"], errors="coerce").fillna(0).sum()) if "Sponsor" in df_filtered.columns else 0
        st.markdown(
            f"""
            <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 10px; padding: 10px 14px; text-align: center;">
                <span style="font-size: 0.75rem; color: #166534; font-weight: 600; text-transform: uppercase;">⭐ AS A SPONSOR</span>
                <div style="font-size: 1.35rem; font-weight: 800; color: #15803D; margin-top: 2px;">{sponsor_cnt}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with rcol3:
        member_cnt = int(pd.to_numeric(df_filtered["Member"], errors="coerce").fillna(0).sum()) if "Member" in df_filtered.columns else 0
        st.markdown(
            f"""
            <div style="background: #FAF5FF; border: 1px solid #E9D5FF; border-radius: 10px; padding: 10px 14px; text-align: center;">
                <span style="font-size: 0.75rem; color: #6B21A8; font-weight: 600; text-transform: uppercase;">👥 AS A MEMBER</span>
                <div style="font-size: 1.35rem; font-weight: 800; color: #7E22CE; margin-top: 2px;">{member_cnt}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with rcol4:
        fasil_cnt = int(pd.to_numeric(df_filtered["Fasilitator"], errors="coerce").fillna(0).sum()) if "Fasilitator" in df_filtered.columns else 0
        st.markdown(
            f"""
            <div style="background: #FFF7ED; border: 1px solid #FED7AA; border-radius: 10px; padding: 10px 14px; text-align: center;">
                <span style="font-size: 0.75rem; color: #9A3412; font-weight: 600; text-transform: uppercase;">🎯 AS A FASILITATOR</span>
                <div style="font-size: 1.35rem; font-weight: 800; color: #C2410C; margin-top: 2px;">{fasil_cnt}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)


# ==============================================================================
# VISUALIZATION (EXECUTIVE DASHBOARD) - INTERACTIVE & HIGH CONTRAST
# ==============================================================================
color_map = {"Engaged": "#10B981", "Non-Engaged": "#EF4444"}

if total_filtered > 0:
    # Color Legend Indicator Badge
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding: 4px 2px;">
            <div style="font-size: 1.1rem; font-weight: 700; color: #0F172A;">📊 Visual Engagement Overview</div>
            <div style="font-size: 0.85rem; font-weight: 600; background: #FFFFFF; padding: 6px 14px; border-radius: 20px; border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <span style="color: #10B981; margin-right: 16px;">● <b>Engaged</b> (Completed)</span>
                <span style="color: #EF4444;">● <b>Non-Engaged</b> (Pending)</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ROW 1: Donut Chart & Directorate Overview
    row1_col1, row1_col2 = st.columns([1, 1.3])

    with row1_col1:
        with st.container(border=True):
            st.markdown('<div class="section-title">🎯 Overall Participation Rate</div>', unsafe_allow_html=True)
            status_counts = df_filtered["Engagement_Status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            
            fig_donut = px.pie(
                status_counts,
                names="Status",
                values="Count",
                hole=0.60,
                color="Status",
                color_discrete_map=color_map,
            )
            fig_donut.update_traces(
                textposition="inside",
                textinfo="percent+label",
                textfont=dict(color="#FFFFFF", size=12, family="Plus Jakarta Sans, sans-serif"),
                hoverinfo="label+value+percent",
                marker=dict(line=dict(color="#FFFFFF", width=2.5)),
            )
            fig_donut.update_layout(
                margin=dict(t=20, b=20, l=10, r=10),
                height=340,
                showlegend=False,
                annotations=[
                    dict(
                        text=f"<b style='font-size:22px;color:#0F172A;'>{engagement_rate:.1f}%</b><br><span style='font-size:12px;color:#64748B;font-weight:600;'>Participation</span>",
                        x=0.5,
                        y=0.5,
                        showarrow=False,
                    )
                ],
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_donut, use_container_width=True)

    with row1_col2:
        with st.container(border=True):
            st.markdown('<div class="section-title">🏢 Participation by Directorate</div>', unsafe_allow_html=True)
            dir_grouped = (
                df_filtered.groupby(["Directorate", "Engagement_Status"])
                .size()
                .reset_index(name="Count")
            )
            
            fig_dir = px.bar(
                dir_grouped,
                y="Directorate",
                x="Count",
                color="Engagement_Status",
                orientation="h",
                barmode="stack",
                color_discrete_map=color_map,
                text="Count",
                labels={"Count": "Employees", "Directorate": "Directorate", "Engagement_Status": "Status"},
            )
            fig_dir.update_traces(
                textposition="inside",
                textfont=dict(color="#FFFFFF", size=11, family="Plus Jakarta Sans, sans-serif"),
            )
            fig_dir.update_layout(
                margin=dict(t=20, b=40, l=20, r=20),
                height=340,
                showlegend=False,
                xaxis=dict(
                    gridcolor="#E2E8F0",
                    tickfont=dict(color="#1E293B", size=11, family="Plus Jakarta Sans, sans-serif"),
                    title=dict(text="Number of Employees", font=dict(color="#0F172A", size=12)),
                ),
                yaxis=dict(
                    autorange="reversed",
                    tickfont=dict(color="#1E293B", size=11, family="Plus Jakarta Sans, sans-serif"),
                    title=None,
                ),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_dir, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ROW 2: SINGLE MAIN INTERACTIVE DIVISION CHART (FULL WIDTH)
    with st.container(border=True):
        st.markdown('<div class="section-title">📈 Division Engagement Breakdown</div>', unsafe_allow_html=True)
        
        # Interactive Controls
        ctrl_col1, ctrl_col2, _ = st.columns([1.5, 1.5, 3])
        with ctrl_col1:
            div_status_view = st.selectbox(
                "Status View",
                options=["All Status", "Show Engaged", "Show Non-Engaged"],
                index=0,
                key="div_status_view",
                help="Select which status category to display on the chart."
            )
        with ctrl_col2:
            div_sort_order = st.selectbox(
                "Sort Order",
                options=["Highest to Lowest", "Lowest to Highest"],
                index=0,
                key="div_sort_order",
                help="Sort divisions by employee volume."
            )

        ascending_sort = (div_sort_order == "Lowest to Highest")

        if div_status_view == "Show Engaged":
            div_data = df_filtered[df_filtered["Engagement_Status"] == "Engaged"]
            if len(div_data) > 0:
                div_grouped = div_data.groupby(["Division", "Division_Short"]).size().reset_index(name="Count")
                div_grouped["Engagement_Status"] = "Engaged"
                div_grouped = div_grouped.sort_values(by="Count", ascending=ascending_sort)
                div_order = div_grouped["Division_Short"].tolist()

                fig_div = px.bar(
                    div_grouped,
                    x="Division_Short",
                    y="Count",
                    color="Engagement_Status",
                    color_discrete_map=color_map,
                    text="Count",
                    category_orders={"Division_Short": div_order},
                    hover_name="Division",
                    labels={"Count": "Employees", "Division_Short": "Division", "Engagement_Status": "Status"},
                )
                fig_div.update_traces(
                    textposition="outside",
                    textfont=dict(color="#059669", size=11, family="Plus Jakarta Sans, sans-serif"),
                    cliponaxis=False,
                )
                max_val = div_grouped["Count"].max() if len(div_grouped) > 0 else 10
                fig_div.update_yaxes(range=[0, max_val * 1.18])
            else:
                fig_div = None

        elif div_status_view == "Show Non-Engaged":
            div_data = df_filtered[df_filtered["Engagement_Status"] == "Non-Engaged"]
            if len(div_data) > 0:
                div_grouped = div_data.groupby(["Division", "Division_Short"]).size().reset_index(name="Count")
                div_grouped["Engagement_Status"] = "Non-Engaged"
                div_grouped = div_grouped.sort_values(by="Count", ascending=ascending_sort)
                div_order = div_grouped["Division_Short"].tolist()

                fig_div = px.bar(
                    div_grouped,
                    x="Division_Short",
                    y="Count",
                    color="Engagement_Status",
                    color_discrete_map=color_map,
                    text="Count",
                    category_orders={"Division_Short": div_order},
                    hover_name="Division",
                    labels={"Count": "Employees", "Division_Short": "Division", "Engagement_Status": "Status"},
                )
                fig_div.update_traces(
                    textposition="outside",
                    textfont=dict(color="#DC2626", size=11, family="Plus Jakarta Sans, sans-serif"),
                    cliponaxis=False,
                )
                max_val = div_grouped["Count"].max() if len(div_grouped) > 0 else 10
                fig_div.update_yaxes(range=[0, max_val * 1.18])
            else:
                fig_div = None

        else:  # "All Status"
            # Calculate total volume per division for sorting & top total labels
            div_totals = df_filtered.groupby(["Division", "Division_Short"]).size().reset_index(name="Total")
            div_totals = div_totals.sort_values(by="Total", ascending=ascending_sort)
            div_order = div_totals["Division_Short"].tolist()

            div_grouped = (
                df_filtered.groupby(["Division", "Division_Short", "Engagement_Status"])
                .size()
                .reset_index(name="Count")
            )

            fig_div = px.bar(
                div_grouped,
                x="Division_Short",
                y="Count",
                color="Engagement_Status",
                barmode="stack",
                color_discrete_map=color_map,
                text="Count",
                category_orders={"Division_Short": div_order},
                hover_name="Division",
                labels={"Count": "Employees", "Division_Short": "Division", "Engagement_Status": "Status"},
            )
            fig_div.update_traces(
                textposition="inside",
                textfont=dict(color="#FFFFFF", size=10, family="Plus Jakarta Sans, sans-serif"),
            )

            # Add total count annotations directly above each stacked bar
            max_val = div_totals["Total"].max() if len(div_totals) > 0 else 10
            for _, row in div_totals.iterrows():
                fig_div.add_annotation(
                    x=row["Division_Short"],
                    y=row["Total"],
                    text=f"<b>{row['Total']}</b>",
                    showarrow=False,
                    yshift=10,
                    font=dict(color="#1E293B", size=11, family="Plus Jakarta Sans, sans-serif"),
                )
            fig_div.update_yaxes(range=[0, max_val * 1.18])

        if fig_div is not None:
            fig_div.update_layout(
                margin=dict(t=35, b=40, l=40, r=20),
                height=420,
                showlegend=False,
                xaxis=dict(
                    tickangle=0,
                    gridcolor="#E2E8F0",
                    tickfont=dict(color="#1E293B", size=10, family="Plus Jakarta Sans, sans-serif"),
                    title=None,
                ),
                yaxis=dict(
                    gridcolor="#E2E8F0",
                    tickfont=dict(color="#1E293B", size=11, family="Plus Jakarta Sans, sans-serif"),
                    title=dict(text="Number of Employees", font=dict(color="#0F172A", size=12)),
                ),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_div, use_container_width=True)
        else:
            st.info("ℹ️ No records found matching the selected status view.")

else:
    st.info("ℹ️ No records match the current filter criteria. Try adjusting the sidebar filters.")


# ==============================================================================
# INTERACTIVE DATA TABLE (EXECUTIVE ACTION VIEW)
# ==============================================================================
st.markdown("---")

table_col1, table_col2, table_col3 = st.columns([1.8, 2.2, 1])

with table_col1:
    st.markdown('<div class="section-title" style="margin-bottom:0;">📋 Employee Engagement Details</div>', unsafe_allow_html=True)

with table_col2:
    table_filter_view = st.radio(
        "Table Status Filter",
        options=["All", "Show Engaged", "Show Non-Engaged"],
        index=0,
        horizontal=True,
        label_visibility="collapsed",
        key="table_status_filter_radio",
        help="Filter table records by engagement status.",
    )

# Filter table based on selected status view
if table_filter_view == "Show Engaged":
    df_table = df_filtered[df_filtered["Engagement_Status"] == "Engaged"]
elif table_filter_view == "Show Non-Engaged":
    df_table = df_filtered[df_filtered["Engagement_Status"] == "Non-Engaged"]
else:
    df_table = df_filtered

with table_col3:
    export_prefix = "engaged_" if table_filter_view == "Show Engaged" else ("non_engaged_" if table_filter_view == "Show Non-Engaged" else "")
    csv_data = df_table.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export Data (CSV)",
        data=csv_data,
        file_name=f"klip_finance_{export_prefix}export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

if table_filter_view == "Show Engaged":
    st.caption(f"Showing **{len(df_table):,}** records *(🟢 Filter: Engaged)* from total **{len(df_raw):,}** employees.")
elif table_filter_view == "Show Non-Engaged":
    st.caption(f"Showing **{len(df_table):,}** records *(🔴 Filter: Non-Engaged)* from total **{len(df_raw):,}** employees.")
else:
    st.caption(f"Showing **{len(df_table):,}** records from total **{len(df_raw):,}** employees.")

display_cols = [
    col for col in [
        "Loc_Type",
        "Employee_ID",
        "Employee_Name",
        "Status_PA",
        "Engagement_Status",
        "Leader",
        "Sponsor",
        "Member",
        "Fasilitator",
        "Directorate",
        "Division",
        "Company_Name",
        "Engagement_Score",
        "Completion_Date",
    ]
    if col in df_table.columns
]

st.dataframe(
    df_table[display_cols],
    use_container_width=True,
    height=450,
    column_config={
        "Loc_Type": st.column_config.TextColumn("Location", width="small"),
        "Employee_ID": st.column_config.TextColumn("NIK / ID", width="medium"),
        "Employee_Name": st.column_config.TextColumn("Employee Name", width="large"),
        "Status_PA": st.column_config.TextColumn("Status PA", width="small"),
        "Engagement_Status": st.column_config.TextColumn("Status", width="medium"),
        "Leader": st.column_config.NumberColumn("Leader", width="small", format="%d"),
        "Sponsor": st.column_config.NumberColumn("Sponsor", width="small", format="%d"),
        "Member": st.column_config.NumberColumn("Member", width="small", format="%d"),
        "Fasilitator": st.column_config.NumberColumn("Fasilitator", width="small", format="%d"),
        "Directorate": st.column_config.TextColumn("Directorate", width="medium"),
        "Division": st.column_config.TextColumn("Division", width="large"),
        "Company_Name": st.column_config.TextColumn("Company", width="medium"),
        "Engagement_Score": st.column_config.ProgressColumn(
            "Engagement Score",
            help="Employee Participation Score (0 - 100)",
            format="%d",
            min_value=0,
            max_value=100,
        ),
        "Completion_Date": st.column_config.TextColumn("Completion Date", width="small"),
    },
    hide_index=True,
)

# Footer
st.markdown(
    """
    <div style="text-align: center; color: #94A3B8; font-size: 0.8rem; margin-top: 40px; padding: 20px 0; border-top: 1px solid #E2E8F0;">
        KLIP Engagement Dashboard © 2026 • Corporate Finance Analytics Engine • Powered by Streamlit & Plotly
    </div>
    """,
    unsafe_allow_html=True,
)
