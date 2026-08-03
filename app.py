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

    /* Modern Card Styling */
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(248,250,252,0.95));
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 20px 22px;
        box-shadow: 0 4px 14px -2px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px -3px rgba(0, 0, 0, 0.08);
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.1;
        margin-bottom: 6px;
    }
    .metric-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 3px 8px;
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
        padding: 24px 30px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
    }
    .main-header h1 {
        font-size: 1.75rem;
        font-weight: 800;
        margin: 0 0 6px 0;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .main-header p {
        font-size: 0.95rem;
        color: #94A3B8;
        margin: 0;
    }
    .header-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 14px;
    }
    .pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.8rem;
        font-weight: 500;
        background: rgba(255, 255, 255, 0.1);
        padding: 4px 12px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        color: #E2E8F0;
    }

    /* Filter Box */
    .filter-section {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 20px;
    }

    /* Plotly Chart Card Container */
    .chart-container {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        margin-bottom: 20px;
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

        # Standardisasi Nama Kolom (Case-insensitive mapping)
        col_mapping = {}
        for col in df.columns:
            clean = col.strip().lower().replace(" ", "_").replace("/", "_").replace(".", "_")
            if any(k in clean for k in ["employee_id", "nik", "id_karyawan", "no_pegawai"]):
                col_mapping[col] = "Employee_ID"
            elif any(k in clean for k in ["employee_name", "nama_karyawan", "nama", "employee"]):
                col_mapping[col] = "Employee_Name"
            elif any(k in clean for k in ["company", "perusahaan", "pt"]):
                col_mapping[col] = "Company_Name"
            elif any(k in clean for k in ["directorate", "direktorat", "dir"]):
                col_mapping[col] = "Directorate"
            elif any(k in clean for k in ["division", "divisi", "div"]):
                col_mapping[col] = "Division"
            elif any(k in clean for k in ["group_bu", "bu_corp", "bu", "group"]):
                col_mapping[col] = "Group_BU_CORP"
            elif any(k in clean for k in ["status_engagement", "engagement_status", "klip_status", "status", "engagement"]):
                col_mapping[col] = "Engagement_Status"
            elif any(k in clean for k in ["score", "nilai", "skor"]):
                col_mapping[col] = "Engagement_Score"
            elif any(k in clean for k in ["loc", "lokasi", "location"]):
                col_mapping[col] = "Loc_Type"
            elif any(k in clean for k in ["date", "tanggal", "completion"]):
                col_mapping[col] = "Completion_Date"

        df = df.rename(columns=col_mapping)

        # Fallback kolom jika tidak ada
        if "Employee_ID" not in df.columns:
            df["Employee_ID"] = [f"EMP-{1000 + i}" for i in range(len(df))]
        if "Employee_Name" not in df.columns:
            # Cari kolom string pertama
            str_cols = df.select_dtypes(include=["object"]).columns
            df["Employee_Name"] = df[str_cols[0]] if len(str_cols) > 0 else "Karyawan"
        if "Directorate" not in df.columns:
            df["Directorate"] = "CORP FINANCE"
        if "Division" not in df.columns:
            df["Division"] = "General Finance"
        if "Company_Name" not in df.columns:
            df["Company_Name"] = "Holding"
        if "Engagement_Status" not in df.columns:
            # Cek jika ada kolom boolean/angka
            df["Engagement_Status"] = "Engaged"

        # Bersihkan dan Normalisasi Nilai Engagement_Status
        def normalize_status(val):
            if pd.isna(val):
                return "Non-Engaged"
            s = str(val).strip().lower()
            if s in ["1", "true", "engaged", "sudah", "yes", "selesai", "ikut", "completed", "active"]:
                return "Engaged"
            return "Non-Engaged"

        df["Engagement_Status"] = df["Engagement_Status"].apply(normalize_status)

        # Bersihkan string strings
        for col in ["Employee_Name", "Directorate", "Division", "Company_Name"]:
            if col in df.columns:
                df[col] = df[col].fillna("Unknown").astype(str).str.strip()

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
            <div style="background: #3B82F6; color: white; border-radius: 8px; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; font-weight: bold;">
                📊
            </div>
            <div>
                <h3 style="margin: 0; font-size: 1.15rem; font-weight: 700; color: #1E293B;">KLIP Dashboard</h3>
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

    # Placeholder untuk filter dinamis setelah load dataframe
    filter_search = st.text_input("Cari Nama / NIK", placeholder="Ketik nama atau NIK...", help="Pencarian cepat pada kolom NIK dan Nama.")
    status_filter = st.selectbox("Status Engagement", ["Semua Status", "Engaged", "Non-Engaged"])


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
    all_directorates = sorted(df_raw["Directorate"].dropna().unique().tolist())
    selected_dirs = st.multiselect("Direktorat", options=all_directorates, default=all_directorates)

    # Filter Divisi berdasarkan Direktorat terpilih
    div_options = sorted(
        df_raw[df_raw["Directorate"].isin(selected_dirs)]["Division"].dropna().unique().tolist()
    )
    selected_divs = st.multiselect("Divisi", options=div_options, default=div_options)

    # Filter Perusahaan
    company_options = sorted(df_raw["Company_Name"].dropna().unique().tolist())
    selected_companies = st.multiselect("Perusahaan (Company)", options=company_options, default=company_options)

# Terapkan Filter ke DataFrame
df_filtered = df_raw.copy()

if selected_dirs:
    df_filtered = df_filtered[df_filtered["Directorate"].isin(selected_dirs)]

if selected_divs:
    df_filtered = df_filtered[df_filtered["Division"].isin(selected_divs)]

if selected_companies:
    df_filtered = df_filtered[df_filtered["Company_Name"].isin(selected_companies)]

if status_filter != "Semua Status":
    df_filtered = df_filtered[df_filtered["Engagement_Status"] == status_filter]

if filter_search.strip():
    kw = filter_search.strip().lower()
    df_filtered = df_filtered[
        df_filtered["Employee_Name"].str.lower().str.contains(kw, na=False)
        | df_filtered["Employee_ID"].str.lower().str.contains(kw, na=False)
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
engaged_count = (df_filtered["Engagement_Status"] == "Engaged").sum()
non_engaged_count = (df_filtered["Engagement_Status"] == "Non-Engaged").sum()
engagement_rate = (engaged_count / total_filtered * 100) if total_filtered > 0 else 0
non_engagement_rate = (non_engaged_count / total_filtered * 100) if total_filtered > 0 else 0
total_dirs_count = df_filtered["Directorate"].nunique()
total_divs_count = df_filtered["Division"].nunique()

mcol1, mcol2, mcol3, mcol4 = st.columns(4)

with mcol1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">Total Karyawan (Filtered)</div>
            <div class="metric-value">{total_filtered:,}</div>
            <div>
                <span class="metric-badge badge-info">Dari total {total_all:,} data</span>
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
            <div class="metric-value" style="color: #4F46E5;">{total_divs_count} <span style="font-size: 1.1rem; font-weight: 500; color: #64748B;">Divisi</span></div>
            <div>
                <span class="metric-badge badge-info">🏢 {total_dirs_count} Direktorat</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)


# ==============================================================================
# VISUALISASI INTERAKTIF (PLOTLY)
# ==============================================================================
if total_filtered > 0:
    # ROW 1: Donut Chart & Directorate Bar Chart
    row1_col1, row1_col2 = st.columns([1, 1.4])

    with row1_col1:
        st.markdown("#### 🎯 Distribusi Status Engagement")
        status_counts = df_filtered["Engagement_Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        
        # Color mapping: Green for Engaged, Red for Non-Engaged
        color_map = {"Engaged": "#10B981", "Non-Engaged": "#EF4444"}
        
        fig_donut = px.pie(
            status_counts,
            names="Status",
            values="Count",
            hole=0.55,
            color="Status",
            color_discrete_map=color_map,
        )
        fig_donut.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hoverinfo="label+value+percent",
            marker=dict(line=dict(color="#FFFFFF", width=2)),
        )
        fig_donut.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=320,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
            annotations=[
                dict(
                    text=f"<b>{engagement_rate:.1f}%</b><br><span style='font-size:11px;color:#64748B;'>Engaged</span>",
                    x=0.5,
                    y=0.5,
                    font_size=18,
                    showarrow=False,
                )
            ],
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with row1_col2:
        st.markdown("#### 🏢 Engagement per Direktorat")
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
            labels={"Count": "Jumlah Karyawan", "Directorate": "Direktorat", "Engagement_Status": "Status"},
        )
        fig_dir.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=320,
            xaxis=dict(gridcolor="#F1F5F9"),
            yaxis=dict(autorange="reversed"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_dir, use_container_width=True)

    # ROW 2: Division & Company Breakdown
    row2_col1, row2_col2 = st.columns([1.5, 1])

    with row2_col1:
        st.markdown("#### 📈 Distribusi Engagement per Divisi (Top 12)")
        div_grouped = (
            df_filtered.groupby(["Division", "Engagement_Status"])
            .size()
            .reset_index(name="Count")
        )
        # Urutkan berdasarkan total per divisi
        top_divs = (
            df_filtered["Division"]
            .value_counts()
            .head(12)
            .index.tolist()
        )
        div_grouped_filtered = div_grouped[div_grouped["Division"].isin(top_divs)]

        fig_div = px.bar(
            div_grouped_filtered,
            x="Division",
            y="Count",
            color="Engagement_Status",
            barmode="group",
            color_discrete_map=color_map,
            labels={"Count": "Jumlah Karyawan", "Division": "Divisi", "Engagement_Status": "Status"},
        )
        fig_div.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=340,
            xaxis=dict(tickangle=-30, gridcolor="#F1F5F9"),
            yaxis=dict(gridcolor="#F1F5F9"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_div, use_container_width=True)

    with row2_col2:
        st.markdown("#### 🏢 Distribusi per Perusahaan (Company)")
        comp_grouped = (
            df_filtered.groupby(["Company_Name", "Engagement_Status"])
            .size()
            .reset_index(name="Count")
        )
        fig_comp = px.bar(
            comp_grouped,
            x="Company_Name",
            y="Count",
            color="Engagement_Status",
            barmode="stack",
            color_discrete_map=color_map,
            labels={"Count": "Jumlah Karyawan", "Company_Name": "Perusahaan", "Engagement_Status": "Status"},
        )
        fig_comp.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=340,
            xaxis=dict(tickangle=-20, gridcolor="#F1F5F9"),
            yaxis=dict(gridcolor="#F1F5F9"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_comp, use_container_width=True)

else:
    st.info("ℹ️ Tidak ada data yang cocok dengan kriteria filter saat ini. Coba sesuaikan filter di sidebar.")


# ==============================================================================
# INTERACTIVE DATA TABLE
# ==============================================================================
st.markdown("---")
st.markdown("### 📋 Detail Data Karyawan")

table_col1, table_col2 = st.columns([3, 1])
with table_col1:
    st.caption(f"Menampilkan **{len(df_filtered):,}** dari total **{len(df_raw):,}** baris data.")
with table_col2:
    # Tombol Download CSV Hasil Filter
    csv_data = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Unduh Data (CSV)",
        data=csv_data,
        file_name=f"klip_finance_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

# Konfigurasi Tampilan Kolom DataFrame
display_cols = [
    col for col in [
        "Employee_ID",
        "Employee_Name",
        "Engagement_Status",
        "Directorate",
        "Division",
        "Company_Name",
        "Loc_Type",
        "Engagement_Score",
        "Completion_Date",
    ]
    if col in df_filtered.columns
]

st.dataframe(
    df_filtered[display_cols],
    use_container_width=True,
    height=450,
    column_config={
        "Employee_ID": st.column_config.TextColumn("NIK / ID", width="medium"),
        "Employee_Name": st.column_config.TextColumn("Nama Karyawan", width="large"),
        "Engagement_Status": st.column_config.TextColumn("Status", width="medium"),
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
        "Loc_Type": st.column_config.TextColumn("Lokasi", width="small"),
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
