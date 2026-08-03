"""
Module: fetch_drive_data.py
Deskripsi: Modul pengunduhan file data CSV KLIP Finance langsung dari Google Drive
            menggunakan gdown tanpa memerlukan login manual atau browser scraping.
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from typing import Tuple, Optional
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
# KONFIGURASI GOOGLE DRIVE TARGET
# ==============================================================================
# Folder Google Drive Target
DEFAULT_FOLDER_ID = "1eKbKPKRtTKdnxGephe6cUTWhcSxEUMKj"
DEFAULT_TARGET_FILENAME = "KLIP Engagement_Detail Engagement 2026_Tabel.csv"

# Direktori Penyimpanan Lokal
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LATEST_CSV_PATH = DATA_DIR / "klip_finance_latest.csv"
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

    # 2. Cek kecocokan kata kunci 'Detail Engagement' atau 'KLIP'
    for f in csv_files:
        fname = f.name.lower()
        if "detail engagement" in fname or "klip engagement" in fname:
            return f

    # 3. Fallback ke file CSV pertama yang ditemukan
    return csv_files[0]


def download_klip_data_from_drive(
    folder_id: str = DEFAULT_FOLDER_ID,
    target_filename: str = DEFAULT_TARGET_FILENAME,
    dest_path: Path = LATEST_CSV_PATH,
    file_id: Optional[str] = None,
) -> Tuple[bool, str, Optional[Path]]:
    """
    Mengunduh file CSV dari Google Drive menggunakan gdown.
    Mendukung pengunduhan dari Folder ID maupun File ID langsung.
    
    Returns:
        (success: bool, message: str, file_path: Optional[Path])
    """
    ensure_data_dir()
    clean_temp_dir()
    TEMP_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("Memulai sinkronisasi data dari Google Drive...")
    logger.info(f"Target Folder ID : {folder_id}")
    logger.info(f"Target Filename  : {target_filename}")
    logger.info(f"Output File      : {dest_path}")
    logger.info("=" * 60)

    try:
        # Jika file_id spesifik diberikan, unduh langsung file tersebut
        if file_id:
            output_str = str(dest_path)
            res = gdown.download(id=file_id, output=output_str, quiet=False, use_cookies=False)
            if res and dest_path.exists() and dest_path.stat().st_size > 0:
                df_check = pd.read_csv(dest_path)
                msg = f"Sinkronisasi Berhasil! File '{dest_path.name}' diperbarui ({len(df_check):,} baris)."
                logger.info(msg)
                return True, msg, dest_path
            else:
                return False, "File gagal diunduh atau file kosong.", None

        # Unduh seluruh folder ke temporary directory
        gdown.download_folder(
            id=folder_id,
            output=str(TEMP_DOWNLOAD_DIR),
            quiet=False,
            use_cookies=False,
        )

        # Cari file CSV target di dalam hasil unduhan
        matched_csv = find_csv_file_in_dir(TEMP_DOWNLOAD_DIR, target_filename)

        if not matched_csv or not matched_csv.exists() or matched_csv.stat().st_size == 0:
            clean_temp_dir()
            err_msg = (
                f"Folder Google Drive berhasil diakses, namun file CSV target "
                f"'{target_filename}' tidak ditemukan di dalam folder tersebut."
            )
            logger.error(err_msg)
            return False, err_msg, None

        # Salin file CSV target ke path tujuan utama
        shutil.copy2(matched_csv, dest_path)
        clean_temp_dir()

        # Validasi pembacaan file dengan pandas
        df_check = pd.read_csv(dest_path)
        success_msg = (
            f"Sinkronisasi Berhasil! File '{dest_path.name}' berhasil diperbarui "
            f"({len(df_check):,} baris, {len(df_check.columns)} kolom)."
        )
        logger.info(success_msg)
        return True, success_msg, dest_path

    except gdown.exceptions.DownloadError as de:
        clean_temp_dir()
        de_str = str(de)
        if "401" in de_str or "permission" in de_str.lower() or "anyone with the link" in de_str.lower():
            err_msg = (
                f"Akses Google Drive Ditolak (401 / Permission Denied).\n\n"
                f"Status: Folder Google Drive '{folder_id}' belum diset menjadi publik.\n\n"
                f"Langkah Penyelesaian:\n"
                f"1. Buka Google Drive: https://drive.google.com/drive/folders/{folder_id}\n"
                f"2. Klik kanan pada folder -> 'Share' / 'Bagikan'\n"
                f"3. Di bagian 'General Access', ubah dari 'Restricted' menjadi 'Anyone with the link' (Siapa saja yang memiliki link) -> Role 'Viewer'\n"
                f"4. Klik 'Done' / 'Selesai' lalu klik tombol 'Refresh Data dari Drive' kembali."
            )
        else:
            err_msg = f"Gagal mengunduh dari Google Drive: {de_str}"
        
        logger.error(err_msg)
        return False, err_msg, None

    except Exception as e:
        clean_temp_dir()
        err_msg = f"Terjadi kesalahan saat sinkronisasi data Google Drive: {str(e)}"
        logger.error(err_msg)
        return False, err_msg, None


def generate_sample_mock_data(dest_path: Path = LATEST_CSV_PATH) -> Path:
    """
    Membuat sample data CSV realistis untuk fallback/demo jika file Drive belum diset publik.
    """
    ensure_data_dir()
    import random

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

    data = []
    nik_counter = 1002001

    for _ in range(450):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        dir_name = random.choice(directorates)
        div_name = random.choice(divisions[dir_name])
        comp_name = random.choice(companies)
        
        # ~80% engaged rate
        is_engaged = random.choices([True, False], weights=[82, 18])[0]
        status = "Engaged" if is_engaged else "Non-Engaged"
        score = random.randint(75, 100) if is_engaged else random.randint(25, 69)

        data.append({
            "Employee_ID": f"FIN-{nik_counter}",
            "Employee_Name": name,
            "Company_Name": comp_name,
            "Directorate": dir_name,
            "Division": div_name,
            "Group_BU_CORP": "CORP-FINANCE",
            "Engagement_Status": status,
            "Engagement_Score": score,
            "Loc_Type": random.choice(["Head Office", "Regional Hub", "Site Office"]),
            "Completion_Date": "2026-02-15" if is_engaged else "-",
        })
        nik_counter += 1

    df_sample = pd.DataFrame(data)
    df_sample.to_csv(dest_path, index=False)
    logger.info(f"Sample mock data dibuat: {dest_path} ({len(df_sample)} records)")
    return dest_path


if __name__ == "__main__":
    print("\n" + "=" * 65)
    print(" KLIP DASHBOARD - GOOGLE DRIVE DATA FETCHER")
    print("=" * 65)
    
    success, msg, path = download_klip_data_from_drive()
    print("\n[HASIL SINKRONISASI]")
    print(f"Status  : {'BERHASIL' if success else 'GAGAL'}")
    print(f"Pesan   :\n{msg}")
    
    if not success and not LATEST_CSV_PATH.exists():
        print("\n[INFO] Membuat file sample mock data agar dashboard tetap dapat dijalankan...")
        mock_path = generate_sample_mock_data()
        print(f"Sample data siap di: {mock_path}")
    print("=" * 65 + "\n")
