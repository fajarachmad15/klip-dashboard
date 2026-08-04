"""
Module: fetch_drive_data.py
Deskripsi: Modul pengunduhan 3 file data CSV KLIP Finance langsung dari Google Drive
            menggunakan gdown (Detail Engagement, Fasilitator Corporate, Submission 2026).
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import pandas as pd
import gdown

# Mengatur encoding stdout agar aman di Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ==============================================================================
# KONFIGURASI GOOGLE DRIVE TARGET & PATH PENYIMPANAN
# ==============================================================================
DEFAULT_FOLDER_ID = "1eKbKPKRtTKdnxGephe6cUTWhcSxEUMKj"

# Mapping nama file di Google Drive ke file lokal
SYNC_FILES_MAPPING = {
    "KLIP Engagement_Detail Engagement 2026_Tabel.csv": "klip_engagement_latest.csv",
    "KLIP Submission_Fasilitator Corporate_Tabel.csv": "klip_fasilitator_latest.csv",
    "KLIP Submission_Submission 2026_Tabel.csv": "klip_submission_latest.csv",
}

# Direktori Penyimpanan Lokal
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ENGAGEMENT_CSV_PATH = DATA_DIR / "klip_engagement_latest.csv"
FASILITATOR_CSV_PATH = DATA_DIR / "klip_fasilitator_latest.csv"
SUBMISSION_CSV_PATH = DATA_DIR / "klip_submission_latest.csv"
LATEST_CSV_PATH = DATA_DIR / "klip_finance_latest.csv"  # Compatibility alias
TEMP_DOWNLOAD_DIR = DATA_DIR / "_temp_drive_sync"

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("DriveFetcher")


def ensure_data_dir() -> Path:
    """Memastikan folder data/ tersedia."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def clean_temp_dir():
    """Membersihkan folder sementara pasca download."""
    if TEMP_DOWNLOAD_DIR.exists():
        try:
            shutil.rmtree(TEMP_DOWNLOAD_DIR, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Gagal membersihkan temp folder: {e}")


def find_csv_file_in_dir(directory: Path, target_name: str) -> Optional[Path]:
    """
    Mencari file CSV di dalam direktori hasil download.
    Mendahulukan nama yang sama persis, lalu pencarian substring / fuzzy.
    """
    if not directory.exists():
        return None

    all_files = list(directory.rglob("*"))
    csv_files = [f for f in all_files if f.is_file() and f.suffix.lower() == ".csv"]

    if not csv_files:
        return None

    # 1. Cek kecocokan nama persis (case-insensitive)
    for f in csv_files:
        if f.name.strip().lower() == target_name.strip().lower():
            return f

    # 2. Cek kecocokan kata kunci
    keywords = target_name.lower().replace(".csv", "").split("_")
    for f in csv_files:
        fname = f.name.lower()
        if all(kw.strip() in fname for kw in keywords if kw.strip()):
            return f

    # 3. Fallback partial substring
    target_clean = target_name.lower().replace(".csv", "")
    for f in csv_files:
        if any(part in f.name.lower() for part in target_clean.split() if len(part) > 4):
            return f

    return None


def download_klip_data_from_drive(
    folder_id: str = DEFAULT_FOLDER_ID,
) -> Tuple[bool, str, Dict[str, Path]]:
    """
    Mengunduh 3 file CSV dari Google Drive menggunakan gdown:
    1. Detail Engagement 2026 -> klip_engagement_latest.csv
    2. Fasilitator Corporate -> klip_fasilitator_latest.csv
    3. Submission 2026 -> klip_submission_latest.csv
    
    Returns:
        (success: bool, message: str, synced_paths: Dict[str, Path])
    """
    ensure_data_dir()
    clean_temp_dir()
    TEMP_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("Memulai sinkronisasi 3 file dataset dari Google Drive...")
    logger.info(f"Target Folder ID : {folder_id}")
    logger.info("=" * 60)

    synced_files: Dict[str, Path] = {}
    summary_reports = []

    try:
        # Unduh seluruh folder ke temporary directory
        gdown.download_folder(
            id=folder_id,
            output=str(TEMP_DOWNLOAD_DIR),
            quiet=False,
            use_cookies=False,
        )

        for drive_filename, local_filename in SYNC_FILES_MAPPING.items():
            matched_csv = find_csv_file_in_dir(TEMP_DOWNLOAD_DIR, drive_filename)
            dest_file = DATA_DIR / local_filename

            if matched_csv and matched_csv.exists() and matched_csv.stat().st_size > 0:
                shutil.copy2(matched_csv, dest_file)
                df_check = pd.read_csv(dest_file)
                synced_files[local_filename] = dest_file
                summary_reports.append(f"• {local_filename}: {len(df_check):,} rows, {len(df_check.columns)} cols")
                
                # Copy engagement as finance latest for backward compatibility
                if local_filename == "klip_engagement_latest.csv":
                    shutil.copy2(dest_file, LATEST_CSV_PATH)
            else:
                logger.warning(f"File '{drive_filename}' tidak ditemukan dalam unduhan Google Drive.")

        clean_temp_dir()

        if synced_files:
            msg = "Sinkronisasi Berhasil!\n" + "\n".join(summary_reports)
            logger.info(msg)
            return True, msg, synced_files
        else:
            err_msg = "Tidak ada file CSV yang berhasil disinkronisasi dari Google Drive."
            logger.error(err_msg)
            return False, err_msg, {}

    except gdown.exceptions.DownloadError as de:
        clean_temp_dir()
        de_str = str(de)
        if "401" in de_str or "permission" in de_str.lower() or "anyone with the link" in de_str.lower():
            err_msg = (
                f"Akses Google Drive Ditolak (401 / Permission Denied).\n\n"
                f"Status: Folder Google Drive '{folder_id}' belum diset publik.\n"
                f"Ubah General Access folder ke 'Anyone with the link' (Viewer)."
            )
        else:
            err_msg = f"Gagal mengunduh dari Google Drive: {de_str}"
        
        logger.error(err_msg)
        return False, err_msg, {}

    except Exception as e:
        clean_temp_dir()
        err_msg = f"Terjadi kesalahan saat sinkronisasi data Google Drive: {str(e)}"
        logger.error(err_msg)
        return False, err_msg, {}


def generate_sample_mock_data() -> Dict[str, Path]:
    """
    Membuat sample mock data untuk 3 file CSV jika dalam mode offline/demo.
    """
    ensure_data_dir()
    import random

    # 1. Engagement Mock Data
    companies = ["PT Sumber Energi Nusantara", "PT Cipta Finansial Utama", "PT Daya Solusi Prima"]
    directorates = ["Finance & Accounting", "Treasury & Tax", "Corporate Planning", "Internal Audit"]
    divisions = {
        "Finance & Accounting": ["Financial Accounting", "Management Reporting", "Billing & Collection"],
        "Treasury & Tax": ["Corporate Treasury", "Direct & Indirect Tax", "Cash Flow Control"],
        "Corporate Planning": ["Budgeting & Analysis", "Strategic Investment"],
        "Internal Audit": ["Financial Audit", "Compliance & Risk"],
    }
    first_names = ["Ahmad", "Budi", "Citra", "Dewi", "Eko", "Fajar", "Gita", "Hadi", "Indah", "Joko", "Kartika", "Lestari", "Muhammad", "Nanda", "Oki", "Putri", "Rian", "Siti", "Tri", "Wahyu"]
    last_names = ["Pratama", "Santoso", "Wijaya", "Kusuma", "Saputra", "Utami", "Handayani", "Setiawan", "Hidayat", "Lestari", "Nugroho", "Wulandari", "Firmansyah", "Gunawan", "Susanto"]

    eng_data = []
    nik_counter = 1002001
    for _ in range(425):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        dir_name = random.choice(directorates)
        div_name = random.choice(divisions[dir_name])
        comp_name = random.choice(companies)
        is_engaged = random.choices([True, False], weights=[82, 18])[0]
        status = "Engaged" if is_engaged else "Non-Engaged"
        score = random.randint(75, 100) if is_engaged else random.randint(25, 69)

        leader = random.choice([0, 1]) if is_engaged else 0
        sponsor = random.choice([0, 1]) if is_engaged else 0
        member = random.choice([1, 2, 3]) if is_engaged else 0
        fasilitator = random.choice([0, 1]) if is_engaged else 0

        eng_data.append({
            "Employee_ID": f"FIN-{nik_counter}",
            "Employee_Name": name,
            "Company_Name": comp_name,
            "Directorate": dir_name,
            "Division": div_name,
            "Group_BU_CORP": "CORP-FINANCE",
            "Engagement_Status": status,
            "Engagement_Score": score,
            "Status_PA": random.choice(["KLIP", "NON PA"]),
            "Loc_Type": random.choice(["HO", "Site Office", "Regional Hub"]),
            "Leader": leader,
            "Sponsor": sponsor,
            "Member": member,
            "Fasilitator": fasilitator,
            "Completion_Date": "2026-02-15" if is_engaged else "-",
        })
        nik_counter += 1

    df_eng = pd.DataFrame(eng_data)
    df_eng.to_csv(ENGAGEMENT_CSV_PATH, index=False)
    df_eng.to_csv(LATEST_CSV_PATH, index=False)

    # 2. Fasilitator Mock Data
    fasilitators = [
        {"Nama": "FAJAR ACHMAD", "Function": "CORPORATE FINANCE", "Submitted": 12, "Registered": 10, "Finished": 8},
        {"Nama": "HENDRA WIJAYA", "Function": "ACCOUNTING OPERATION", "Submitted": 9, "Registered": 8, "Finished": 7},
        {"Nama": "SITI NURHALIZA", "Function": "TAX & TREASURY", "Submitted": 14, "Registered": 12, "Finished": 11},
        {"Nama": "BAMBANG PAMUNGKAS", "Function": "FINANCIAL CONTROL", "Submitted": 8, "Registered": 7, "Finished": 6},
        {"Nama": "RINA KARTIKA", "Function": "AR & CREDIT MANAGEMENT", "Submitted": 11, "Registered": 9, "Finished": 8},
        {"Nama": "AGUS SETIAWAN", "Function": "ACCOUNTS PAYABLE", "Submitted": 7, "Registered": 6, "Finished": 5},
        {"Nama": "DEWI ANGGRAENI", "Function": "INTERNAL AUDIT", "Submitted": 10, "Registered": 9, "Finished": 8},
    ]
    for item in fasilitators:
        item["%Finished"] = f"{round((item['Finished'] / item['Submitted']) * 100, 1)}%" if item["Submitted"] > 0 else "0%"
    df_fas = pd.DataFrame(fasilitators)
    df_fas.to_csv(FASILITATOR_CSV_PATH, index=False)

    # 3. Submission Mock Data
    stages = ["PROPOSAL", "IMPLEMENTATION", "CLOSING", "FINISHED"]
    months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus"]
    sub_data = []
    for i in range(1, 65):
        stage = random.choices(stages, weights=[25, 35, 15, 25])[0]
        sub_data.append({
            "No_KLIP": f"KLIP-2026-FIN-{i:03d}",
            "Title": f"Optimization Project Initiative {i} - Finance Excellence",
            "Leader": f"{random.choice(first_names)} {random.choice(last_names)}",
            "Fasilitator": random.choice(["FAJAR ACHMAD", "HENDRA WIJAYA", "SITI NURHALIZA", "BAMBANG PAMUNGKAS", "RINA KARTIKA"]),
            "Function": random.choice(["CORPORATE FINANCE", "ACCOUNTING OPERATION", "TAX & TREASURY", "FINANCIAL CONTROL"]),
            "Stage": stage,
            "Month": random.choice(months),
            "Status": "Active" if stage != "FINISHED" else "Completed",
            "Target_Completion": "2026-08-30",
        })
    df_sub = pd.DataFrame(sub_data)
    df_sub.to_csv(SUBMISSION_CSV_PATH, index=False)

    return {
        "klip_engagement_latest.csv": ENGAGEMENT_CSV_PATH,
        "klip_fasilitator_latest.csv": FASILITATOR_CSV_PATH,
        "klip_submission_latest.csv": SUBMISSION_CSV_PATH,
    }


if __name__ == "__main__":
    print("\n" + "=" * 65)
    print(" KLIP DASHBOARD - GOOGLE DRIVE MULTI-FILE FETCHER")
    print("=" * 65)
    
    success, msg, paths = download_klip_data_from_drive()
    print("\n[HASIL SINKRONISASI]")
    print(f"Status  : {'BERHASIL' if success else 'GAGAL'}")
    print(f"Pesan   :\n{msg}")
    
    if not success and not ENGAGEMENT_CSV_PATH.exists():
        print("\n[INFO] Membuat file sample mock data...")
        paths = generate_sample_mock_data()
        print(f"Sample data siap: {list(paths.keys())}")
    print("=" * 65 + "\n")
