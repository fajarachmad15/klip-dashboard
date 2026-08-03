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
                <h3 style="margin: 0; font-size: 1.1rem; font-weight: 700; color: #1E293B;">KLIP Dashboard</h3>
                <span style="font-size: 0.75rem; color: #64748B; font-weight: 500;">Google Drive Ingestion Engine</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Status Data & Refresh Section
    st.markdown("### 🔄 Sinkronisasi Data")
    
    # Cek status file lokal
    file_exists = LATEST_CSV_PATH.exists()
    last_mod_time = "-"
    file_size_kb = 0
    if file_exists:
        mtime = os.path.getmtime(LATEST_CSV_PATH)
        last_mod_time = datetime.datetime.fromtimestamp(mtime).strftime("%d-%m-%Y %H:%M:%S")
        file_size_kb = round(os.path.getsize(LATEST_CSV_PATH) / 1024, 1)

    st.markdown(
        f"""
        <div style="background: #F1F5F9; border-radius: 8px; padding: 10px 12px; margin-bottom: 12px; font-size: 0.8rem;">
            <div style="color: #475569;">📁 <b>File:</b> <code>{LATEST_CSV_PATH.name}</code></div>
            <div style="color: #475569; margin-top: 4px;">🕒 <b>Update:</b> {last_mod_time}</div>
            <div style="color: #475569; margin-top: 4px;">📦 <b>Ukuran:</b> {file_size_kb} KB</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    refresh_clicked = st.button("🔄 Refresh Data dari Drive", type="primary", use_container_width=True)

    with st.expander("⚙️ Konfigurasi Google Drive", expanded=False):
        folder_id_input = st.text_input(
            "Folder ID Google Drive",
            value=DEFAULT_FOLDER_ID,
            help="ID Folder Google Drive tempat file CSV disimpan.",
        )
        target_filename_input = st.text_input(
            "Target Nama File CSV",
            value=DEFAULT_TARGET_FILENAME,
            help="Nama file CSV yang akan diekstrak dari folder.",
        )

    st.markdown("---")

    # Filter Section
    st.markdown("### 🔍 Filter Data")
    filter_search = st.text_input("Cari Nama / NIK", placeholder="Ketik nama atau NIK...", help="Pencarian cepat pada kolom NIK dan Nama.")
    status_filter = st.selectbox(
        "Status Engagement",
        options=["Semua Status", "Engaged", "Non-Engaged"],
        index=0,
        help="Filter data berdasarkan status partisipasi engagement."
    )


# ==============================================================================
# LOGIKA SINKRONISASI DRIVE (KICKED BY REFRESH BUTTON)
# ==============================================================================
if refresh_clicked:
    with st.spinner("⏳ Mengunduh dan menyinkronkan data CSV dari Google Drive..."):
        success, message, result_path = download_klip_data_from_drive(
            folder_id=folder_id_input,
            target_filename=target_filename_input,
            dest_path=LATEST_CSV_PATH,
        )

    if success:
        st.cache_data.clear()
        st.toast("✅ Data berhasil diperbarui dari Google Drive!", icon="🎉")
        st.success(f"**Berhasil!** {message}")
        st.rerun()
    else:
        st.error(f"**Sinkronisasi Gagal:**\n\n{message}")
        if not LATEST_CSV_PATH.exists():
            st.info("💡 Klik tombol di bawah untuk membuat data demo simulasi agar dashboard dapat langsung dijelajahi.")
            if st.button("⚡ Buat Data Demo (Simulasi)"):
                generate_sample_mock_data(LATEST_CSV_PATH)
                st.cache_data.clear()
                st.rerun()


# ==============================================================================
# LOAD DATA & VALIDASI
# ==============================================================================
df_raw = load_klip_data()

# Handle jika file belum ada
if df_raw is None or len(df_raw) == 0:
    st.markdown(
        """
        <div class="main-header">
            <h1>📊 KLIP Finance Engagement Dashboard</h1>
            <p>Dashboard Analisis Partisipasi Engagement Karyawan - CORP FINANCE</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.warning("⚠️ **File data belum tersedia di direktori lokal (`./data/klip_finance_latest.csv`).**")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            f"""
            #### 1. Sinkronisasi dari Google Drive
            Klik tombol di sidebar untuk mengunduh dari Folder ID:
            - **Folder ID:** `{DEFAULT_FOLDER_ID}`
            - **Target File:** `{DEFAULT_TARGET_FILENAME}`
            
            *(Pastikan akses folder telah diset menjadi **'Anyone with the link'** pada Google Drive)*
            """
        )
        if st.button("📥 Unduh Sekarang dari Google Drive", type="primary"):
            with st.spinner("Mengunduh..."):
                ok, msg, _ = download_klip_data_from_drive()
                if ok:
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(msg)
    
    with col_b:
        st.markdown(
            """
            #### 2. Mode Simulasi / Data Demo
            Gunakan data tiruan realistis untuk melihat dan menguji visualisasi dashboard secara langsung.
            """
        )
        if st.button("🚀 Buat Data Demo (Simulasi)"):
            generate_sample_mock_data(LATEST_CSV_PATH)
            st.cache_data.clear()
            st.rerun()

    st.stop()


# ==============================================================================
# DYNAMIC FILTERING
# ==============================================================================
with st.sidebar:
    all_directorates = sorted([d for d in df_raw["Directorate"].dropna().unique().tolist() if str(d).strip() != "-"])
    selected_dirs = st.multiselect("Direktorat", options=all_directorates, default=all_directorates)

    # Filter Divisi berdasarkan Direktorat terpilih
    if selected_dirs and len(selected_dirs) < len(all_directorates):
        div_source = df_raw[df_raw["Directorate"].isin(selected_dirs)]
    else:
        div_source = df_raw

    all_div_options = sorted([d for d in div_source["Division"].dropna().unique().tolist() if str(d).strip() != "-"])
    selected_divs = st.multiselect("Divisi", options=all_div_options, default=all_div_options)

    # Filter Perusahaan
    all_company_options = sorted([d for d in df_raw["Company_Name"].dropna().unique().tolist() if str(d).strip() != "-"])
    selected_companies = st.multiselect("Perusahaan (Company)", options=all_company_options, default=all_company_options)

# Terapkan Filter ke DataFrame secara aman
df_filtered = df_raw.copy()

if selected_dirs and len(selected_dirs) < len(all_directorates):
    df_filtered = df_filtered[df_filtered["Directorate"].isin(selected_dirs)]

if selected_divs and len(selected_divs) < len(all_div_options):
    df_filtered = df_filtered[df_filtered["Division"].isin(selected_divs)]

if selected_companies and len(selected_companies) < len(all_company_options):
    df_filtered = df_filtered[df_filtered["Company_Name"].isin(selected_companies)]

if status_filter and status_filter != "Semua Status":
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
        <p>Monitoring Partisipasi & Analisis Engagement Karyawan Corporate Finance secara Real-Time via Google Drive Sync</p>
        <div class="header-pills">
            <span class="pill">🟢 <b>Data Source:</b> Google Drive Ingestion</span>
            <span class="pill">📂 <b>File:</b> {LATEST_CSV_PATH.name}</span>
            <span class="pill">🕒 <b>Last Sync:</b> {last_mod_time}</span>
            <span class="pill">👥 <b>Dataset Size:</b> {total_all:,} Karyawan</span>
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
            <div class="metric-title">Total Karyawan</div>
            <div class="metric-value">{total_filtered:,}</div>
            <div>
                <span class="metric-badge badge-info">Dari {total_all:,} data total</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with mcol2:
    st.markdown(
        f"""
        <div class="metric-card" style="border-left: 4px solid #10B981;">
            <div class="metric-title">Karyawan Engaged</div>
            <div class="metric-value" style="color: #059669;">{engaged_count:,}</div>
            <div>
                <span class="metric-badge badge-success">✓ {engagement_rate:.1f}% Partisipasi</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with mcol3:
    st.markdown(
        f"""
        <div class="metric-card" style="border-left: 4px solid #EF4444;">
            <div class="metric-title">Karyawan Non-Engaged</div>
            <div class="metric-value" style="color: #DC2626;">{non_engaged_count:,}</div>
            <div>
                <span class="metric-badge badge-danger">✕ {non_engagement_rate:.1f}% Belum Ikut</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with mcol4:
    st.markdown(
        f"""
        <div class="metric-card" style="border-left: 4px solid #6366F1;">
            <div class="metric-title">Cakupan Organisasi</div>
            <div class="metric-value" style="color: #4F46E5;">{total_divs_count} <span style="font-size: 1rem; font-weight: 500; color: #64748B;">Divisi</span></div>
            <div>
                <span class="metric-badge badge-info">🏢 {total_dirs_count} Direktorat</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Role Breakdown (jika kolom role tersedia di dataset)
role_cols = [c for c in ["Leader", "Sponsor", "Member", "Fasilitator"] if c in df_filtered.columns]
if role_cols:
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    rcol1, rcol2, rcol3, rcol4 = st.columns(4)
    with rcol1:
        leader_cnt = int(pd.to_numeric(df_filtered["Leader"], errors="coerce").fillna(0).sum()) if "Leader" in df_filtered.columns else 0
        st.markdown(
            f"""
            <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 10px; padding: 10px 14px; text-align: center;">
                <span style="font-size: 0.75rem; color: #1E40AF; font-weight: 600; text-transform: uppercase;">👑 As a Leader</span>
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
                <span style="font-size: 0.75rem; color: #166534; font-weight: 600; text-transform: uppercase;">⭐ As a Sponsor</span>
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
                <span style="font-size: 0.75rem; color: #6B21A8; font-weight: 600; text-transform: uppercase;">👥 As a Member</span>
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
                <span style="font-size: 0.75rem; color: #9A3412; font-weight: 600; text-transform: uppercase;">🎯 As a Fasilitator</span>
                <div style="font-size: 1.35rem; font-weight: 800; color: #C2410C; margin-top: 2px;">{fasil_cnt}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)


# ==============================================================================
# VISUALISASI INTERAKTIF (EXECUTIVE DASHBOARD) - BEBAS OVERLAPPING & HIGH CONTRAST
# ==============================================================================
color_map = {"Engaged": "#10B981", "Non-Engaged": "#EF4444"}

if total_filtered > 0:
    # Header Keterangan Warna (No Clutter)
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding: 4px 2px;">
            <div style="font-size: 1.1rem; font-weight: 700; color: #0F172A;">📊 Analisis Visual Partisipasi</div>
            <div style="font-size: 0.85rem; font-weight: 600; background: #FFFFFF; padding: 6px 14px; border-radius: 20px; border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <span style="color: #10B981; margin-right: 16px;">● <b>Engaged</b> (Ikut Serta)</span>
                <span style="color: #EF4444;">● <b>Non-Engaged</b> (Belum Partisipasi)</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ROW 1: Donut Chart & Directorate / Overall Overview
    row1_col1, row1_col2 = st.columns([1, 1.3])

    with row1_col1:
        with st.container(border=True):
            st.markdown('<div class="section-title">🎯 Rasio Partisipasi Keseluruhan</div>', unsafe_allow_html=True)
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
                        text=f"<b style='font-size:22px;color:#0F172A;'>{engagement_rate:.1f}%</b><br><span style='font-size:12px;color:#64748B;font-weight:600;'>Partisipasi</span>",
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
            st.markdown('<div class="section-title">🏢 Partisipasi per Direktorat</div>', unsafe_allow_html=True)
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
                labels={"Count": "Jumlah Karyawan", "Directorate": "Direktorat", "Engagement_Status": "Status"},
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
                    title=dict(text="Jumlah Karyawan", font=dict(color="#0F172A", size=12)),
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

    # ROW 2: Division Breakdown & Top 5 Divisi Butuh Perhatian
    row2_col1, row2_col2 = st.columns([1.5, 1.1])

    with row2_col1:
        with st.container(border=True):
            st.markdown('<div class="section-title">📈 Distribusi Engagement per Divisi</div>', unsafe_allow_html=True)
            div_grouped = (
                df_filtered.groupby(["Division", "Engagement_Status"])
                .size()
                .reset_index(name="Count")
            )
            top_divs = (
                df_filtered["Division"]
                .value_counts()
                .head(10)
                .index.tolist()
            )
            div_grouped_filtered = div_grouped[div_grouped["Division"].isin(top_divs)]

            fig_div = px.bar(
                div_grouped_filtered,
                x="Division",
                y="Count",
                color="Engagement_Status",
                barmode="stack",
                color_discrete_map=color_map,
                text="Count",
                labels={"Count": "Jumlah Karyawan", "Division": "Divisi", "Engagement_Status": "Status"},
            )
            fig_div.update_traces(
                textposition="inside",
                textfont=dict(color="#FFFFFF", size=10, family="Plus Jakarta Sans, sans-serif"),
            )
            fig_div.update_layout(
                margin=dict(t=30, b=80, l=40, r=20),
                height=380,
                showlegend=False,
                xaxis=dict(
                    tickangle=-25,
                    gridcolor="#E2E8F0",
                    tickfont=dict(color="#1E293B", size=11, family="Plus Jakarta Sans, sans-serif"),
                    title=None,
                ),
                yaxis=dict(
                    gridcolor="#E2E8F0",
                    tickfont=dict(color="#1E293B", size=11, family="Plus Jakarta Sans, sans-serif"),
                    title=dict(text="Jumlah Karyawan", font=dict(color="#0F172A", size=12)),
                ),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_div, use_container_width=True)

    with row2_col2:
        with st.container(border=True):
            st.markdown('<div class="section-title" style="color:#DC2626;">⚠️ Top Divisi Belum Partisipasi</div>', unsafe_allow_html=True)
            
            # Hitung non-engaged per divisi
            non_eng_df = df_filtered[df_filtered["Engagement_Status"] == "Non-Engaged"]
            if len(non_eng_df) > 0:
                top_non_eng = (
                    non_eng_df["Division"]
                    .value_counts()
                    .reset_index()
                )
                top_non_eng.columns = ["Division", "Non_Engaged_Count"]
                top_non_eng = top_non_eng.head(5)

                fig_attention = px.bar(
                    top_non_eng,
                    y="Division",
                    x="Non_Engaged_Count",
                    orientation="h",
                    color_discrete_sequence=["#EF4444"],
                    text="Non_Engaged_Count",
                    labels={"Non_Engaged_Count": "Belum Partisipasi", "Division": "Divisi"},
                )
                fig_attention.update_traces(
                    textposition="outside",
                    textfont=dict(color="#991B1B", size=11, family="Plus Jakarta Sans, sans-serif"),
                    cliponaxis=False,
                )
                fig_attention.update_layout(
                    margin=dict(t=30, b=40, l=20, r=40),
                    height=380,
                    showlegend=False,
                    xaxis=dict(
                        gridcolor="#E2E8F0",
                        tickfont=dict(color="#1E293B", size=11, family="Plus Jakarta Sans, sans-serif"),
                        title=dict(text="Jumlah Belum Ikut", font=dict(color="#0F172A", size=12)),
                    ),
                    yaxis=dict(
                        autorange="reversed",
                        tickfont=dict(color="#1E293B", size=11, family="Plus Jakarta Sans, sans-serif"),
                        title=None,
                    ),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_attention, use_container_width=True)
            else:
                st.success("🎉 Luar biasa! Seluruh karyawan pada filter saat ini telah berstatus **Engaged** (100% Partisipasi).")

else:
    st.info("ℹ️ Tidak ada data yang cocok dengan kriteria filter saat ini. Coba sesuaikan filter di sidebar.")


# ==============================================================================
# INTERACTIVE DATA TABLE (EXECUTIVE ACTION VIEW)
# ==============================================================================
st.markdown("---")

table_col1, table_col2, table_col3 = st.columns([2.2, 1.8, 1])

with table_col1:
    st.markdown('<div class="section-title" style="margin-bottom:0;">📋 Detail Data Karyawan</div>', unsafe_allow_html=True)

with table_col2:
    only_non_engaged = st.checkbox(
        "🔴 **Tampilkan Hanya Non-Engaged**",
        value=False,
        help="Filter instan untuk menampilkan daftar seluruh karyawan yang belum berpartisipasi.",
    )

# Filter tabel berdasarkan toggle Non-Engaged
df_table = df_filtered[df_filtered["Engagement_Status"] == "Non-Engaged"] if only_non_engaged else df_filtered

with table_col3:
    csv_data = df_table.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Unduh Data (CSV)",
        data=csv_data,
        file_name=f"klip_finance_{'non_engaged_' if only_non_engaged else ''}export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.caption(
    f"Menampilkan **{len(df_table):,}** baris data"
    + (" *(⚠️ Filter: Hanya Karyawan Non-Engaged)*" if only_non_engaged else f" dari total **{len(df_raw):,}** karyawan.")
)

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
        "Loc_Type": st.column_config.TextColumn("Lokasi (Loc)", width="small"),
        "Employee_ID": st.column_config.TextColumn("NIK / ID", width="medium"),
        "Employee_Name": st.column_config.TextColumn("Nama Karyawan", width="large"),
        "Status_PA": st.column_config.TextColumn("Status PA", width="small"),
        "Engagement_Status": st.column_config.TextColumn("Status", width="medium"),
        "Leader": st.column_config.NumberColumn("Leader", width="small", format="%d"),
        "Sponsor": st.column_config.NumberColumn("Sponsor", width="small", format="%d"),
        "Member": st.column_config.NumberColumn("Member", width="small", format="%d"),
        "Fasilitator": st.column_config.NumberColumn("Fasilitator", width="small", format="%d"),
        "Directorate": st.column_config.TextColumn("Direktorat", width="medium"),
        "Division": st.column_config.TextColumn("Divisi", width="large"),
        "Company_Name": st.column_config.TextColumn("Perusahaan", width="medium"),
        "Engagement_Score": st.column_config.ProgressColumn(
            "Engagement Score",
            help="Skor Partisipasi Karyawan (0 - 100)",
            format="%d",
            min_value=0,
            max_value=100,
        ),
        "Completion_Date": st.column_config.TextColumn("Tgl Selesai", width="small"),
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
