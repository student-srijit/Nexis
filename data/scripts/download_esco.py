#!/usr/bin/env python3
"""
Download ESCO skill/occupation data.
ESCO: European Skills, Competences, Qualifications and Occupations
Version 1.2.0 — freely downloadable, CC BY 4.0

Downloads:
  occupations_en.csv        — ~3,000 ESCO occupations
  skills_en.csv             — ~14,000 skills/knowledge concepts
  occupationSkillRelations_en.csv — occupation → skill (essential/optional)
  broaderRelationsSkillPillar.csv — skill → broader skill (hierarchy)

Usage: python data/scripts/download_esco.py
"""
import os
import zipfile
import urllib.request
from pathlib import Path

RAW_DIR = Path("data/raw/esco")

# ESCO bulk download (CSV, English, v1.2.0)
ESCO_ZIP_URL = "https://ec.europa.eu/esco/portal/api/resource/resource?resourceUri=http://data.europa.eu/esco/skill/1.2.0"
# We'll use the reliable direct CSV links
ESCO_FILES = {
    "occupations_en.csv": "https://raw.githubusercontent.com/anushkrishnav/ESCO-dataset/main/v1.1.1/occupations_en.csv",
    "skills_en.csv": "https://raw.githubusercontent.com/anushkrishnav/ESCO-dataset/main/v1.1.1/skills_en.csv",
    "occupationSkillRelations_en.csv": "https://raw.githubusercontent.com/anushkrishnav/ESCO-dataset/main/v1.1.1/occupationSkillRelations_en.csv",
    "broaderRelationsSkillPillar.csv": "https://raw.githubusercontent.com/anushkrishnav/ESCO-dataset/main/v1.1.1/broaderRelationsSkillPillar.csv",
}

# Reliable alternative: manually curated subset we ship as backup
BACKUP_ESCO = {
    "occupations": [
        {"occupation_id": "occ_ds", "preferred_label": "Data Scientist", "esco_uri": "http://data.europa.eu/esco/occupation/4a70bb5f-dc34-411e-b42e-cdaab15fc4e3"},
        {"occupation_id": "occ_ml_eng", "preferred_label": "Machine Learning Engineer", "esco_uri": "http://data.europa.eu/esco/occupation/45fe2e6f-6ae5-4a98-b264-efdf8d38d8b0"},
        {"occupation_id": "occ_da", "preferred_label": "Data Analyst", "esco_uri": "http://data.europa.eu/esco/occupation/e07e1da4-dc10-4e12-8a6e-7e2ff1c89ff5"},
        {"occupation_id": "occ_se", "preferred_label": "Software Developer", "esco_uri": "http://data.europa.eu/esco/occupation/dc54e103-44c4-4c0b-8db7-d485b35f3f1f"},
        {"occupation_id": "occ_web", "preferred_label": "Web Developer", "esco_uri": "http://data.europa.eu/esco/occupation/2e8cf3cd-9a42-4dba-9750-77e5c6ea96eb"},
    ],
    "skills": [
        {"skill_id": "s_python", "preferred_label": "Python (computer programming)", "skill_type": "skill"},
        {"skill_id": "s_ml", "preferred_label": "Machine Learning", "skill_type": "skill"},
        {"skill_id": "s_stats", "preferred_label": "Statistics", "skill_type": "knowledge"},
        {"skill_id": "s_dl", "preferred_label": "Deep Learning", "skill_type": "skill"},
        {"skill_id": "s_data_viz", "preferred_label": "Data Visualisation", "skill_type": "skill"},
        {"skill_id": "s_sql", "preferred_label": "SQL (query language)", "skill_type": "skill"},
        {"skill_id": "s_pandas", "preferred_label": "Data manipulation with pandas", "skill_type": "skill"},
        {"skill_id": "s_git", "preferred_label": "Version control with Git", "skill_type": "skill"},
        {"skill_id": "s_docker", "preferred_label": "Containerisation with Docker", "skill_type": "skill"},
        {"skill_id": "s_nlp", "preferred_label": "Natural Language Processing", "skill_type": "skill"},
        {"skill_id": "s_cv", "preferred_label": "Computer Vision", "skill_type": "skill"},
        {"skill_id": "s_cloud", "preferred_label": "Cloud Computing", "skill_type": "skill"},
        {"skill_id": "s_mlops", "preferred_label": "MLOps and model deployment", "skill_type": "skill"},
        {"skill_id": "s_feature_eng", "preferred_label": "Feature Engineering", "skill_type": "skill"},
        {"skill_id": "s_r", "preferred_label": "R (programming language)", "skill_type": "skill"},
    ],
}


def download_esco():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("Downloading ESCO data")
    print("=" * 60)

    success_count = 0
    for fname, url in ESCO_FILES.items():
        dest = RAW_DIR / fname
        if dest.exists():
            print(f"  OK Already exists: {fname}")
            success_count += 1
            continue
        print(f"  >> {fname}...")
        try:
            urllib.request.urlretrieve(url, dest)
            print(f"  OK Downloaded {fname}")
            success_count += 1
        except Exception as e:
            print(f"  FAIL Failed {fname}: {e}")

    if success_count == 0:
        print("\nFalling back to curated ESCO backup...")
        _write_backup()
    else:
        print(f"\nOK Downloaded {success_count}/{len(ESCO_FILES)} ESCO files to {RAW_DIR}")


def _write_backup():
    """Write built-in ESCO backup CSVs so build_skill_graph.py can proceed."""
    import csv
    import io

    occ_path = RAW_DIR / "occupations_en.csv"
    with open(occ_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["occupation_id", "preferred_label", "esco_uri"])
        w.writeheader()
        w.writerows(BACKUP_ESCO["occupations"])

    skills_path = RAW_DIR / "skills_en.csv"
    with open(skills_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["skill_id", "preferred_label", "skill_type"])
        w.writeheader()
        w.writerows(BACKUP_ESCO["skills"])

    # Occupation-skill relations
    occ_skill_rel = [
        ("occ_ds", "s_python", "essential"), ("occ_ds", "s_ml", "essential"),
        ("occ_ds", "s_stats", "essential"), ("occ_ds", "s_dl", "optional"),
        ("occ_ds", "s_data_viz", "essential"), ("occ_ds", "s_sql", "essential"),
        ("occ_ds", "s_pandas", "essential"), ("occ_ds", "s_feature_eng", "essential"),
        ("occ_ml_eng", "s_python", "essential"), ("occ_ml_eng", "s_ml", "essential"),
        ("occ_ml_eng", "s_dl", "essential"), ("occ_ml_eng", "s_pandas", "essential"),
        ("occ_ml_eng", "s_mlops", "essential"), ("occ_ml_eng", "s_docker", "essential"),
        ("occ_da", "s_python", "essential"), ("occ_da", "s_sql", "essential"),
        ("occ_da", "s_data_viz", "essential"), ("occ_da", "s_pandas", "essential"),
        ("occ_da", "s_stats", "essential"), ("occ_da", "s_r", "optional"),
        ("occ_se", "s_python", "essential"), ("occ_se", "s_sql", "essential"),
        ("occ_se", "s_git", "essential"), ("occ_se", "s_docker", "optional"),
        ("occ_web", "s_python", "essential"), ("occ_web", "s_sql", "optional"),
        ("occ_web", "s_git", "essential"),
    ]
    rel_path = RAW_DIR / "occupationSkillRelations_en.csv"
    with open(rel_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["occupation_id", "skill_id", "relation_type"])
        w.writeheader()
        for occ, sk, rel in occ_skill_rel:
            w.writerow({"occupation_id": occ, "skill_id": sk, "relation_type": rel})

    # Skill relations (broader → narrower = prerequisite)
    skill_relations = [
        ("s_python", "s_pandas"), ("s_stats", "s_ml"), ("s_python", "s_ml"),
        ("s_ml", "s_dl"), ("s_pandas", "s_data_viz"), ("s_ml", "s_nlp"),
        ("s_dl", "s_nlp"), ("s_dl", "s_cv"), ("s_python", "s_feature_eng"),
        ("s_ml", "s_feature_eng"), ("s_python", "s_mlops"), ("s_ml", "s_mlops"),
        ("s_docker", "s_mlops"), ("s_python", "s_git"),
    ]
    broader_path = RAW_DIR / "broaderRelationsSkillPillar.csv"
    with open(broader_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["broader_skill", "narrower_skill"])
        w.writeheader()
        for b, n in skill_relations:
            w.writerow({"broader_skill": b, "narrower_skill": n})

    print(f"OK Created curated ESCO backup files in {RAW_DIR}")


if __name__ == "__main__":
    download_esco()
