#!/usr/bin/env python3
"""
Download OULAD dataset from UCI ML Repository.
OULAD: Open University Learning Analytics Dataset
CC-BY 4.0 — freely downloadable

Files downloaded:
  studentAssessment.csv — quiz/assessment responses per student
  assessments.csv       — assessment metadata
  courses.csv           — 22 OU courses
  studentInfo.csv       — student demographics
  studentRegistration.csv
  vle.csv, studentVle.csv (VLE interaction logs — large, ~500MB)

Usage: python data/scripts/download_oulad.py
"""
import os
import zipfile
import urllib.request
from pathlib import Path
from tqdm import tqdm

RAW_DIR = Path("data/raw/oulad")

# Official OULAD download from OU (requires no auth)
OULAD_URL = "https://analyse.kmi.open.ac.uk/open_dataset/download"
# Fallback: subset from GitHub (key files only, smaller)
FALLBACK_BASE = "https://raw.githubusercontent.com/mirkobunse/ecml22/main/data/oulad"
KEY_FILES = [
    "studentAssessment.csv",
    "assessments.csv",
    "courses.csv",
    "studentInfo.csv",
    "studentRegistration.csv",
]


class TqdmUpTo(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download_file(url: str, dest: Path, desc: str = ""):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        print(f"  OK Already exists: {dest.name}")
        return True
    print(f"  >> {desc or dest.name} from {url[:60]}...")
    try:
        with TqdmUpTo(unit="B", unit_scale=True, miniters=1, desc=dest.name[:30]) as t:
            urllib.request.urlretrieve(url, dest, reporthook=t.update_to)
        return True
    except Exception as e:
        print(f"  FAIL Failed: {e}")
        return False


def download_oulad():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("Downloading OULAD dataset")
    print("=" * 60)

    # Try official zip first
    zip_path = RAW_DIR / "anonymisedData.zip"
    success = download_file(OULAD_URL, zip_path, "OULAD (official)")

    if success and zip_path.exists():
        print("Extracting...")
        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(RAW_DIR)
            print(f"OK Extracted to {RAW_DIR}")
            return
        except Exception as e:
            print(f"Extraction failed: {e}")

    # Fallback: download key CSV files individually
    print("\nFalling back to individual CSV download...")
    for fname in KEY_FILES:
        url = f"{FALLBACK_BASE}/{fname}"
        download_file(url, RAW_DIR / fname, fname)

    # Verify
    found = [f for f in KEY_FILES if (RAW_DIR / f).exists()]
    print(f"\nOK Downloaded {len(found)}/{len(KEY_FILES)} OULAD files to {RAW_DIR}")
    if "studentAssessment.csv" not in [f for f in found]:
        print("WARN studentAssessment.csv missing — training will use synthetic data")


if __name__ == "__main__":
    download_oulad()
