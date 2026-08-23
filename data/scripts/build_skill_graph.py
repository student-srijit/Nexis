#!/usr/bin/env python3
"""
Build NetworkX skill graph from ESCO + course catalog.

Reads:
  data/raw/esco/occupations_en.csv
  data/raw/esco/skills_en.csv
  data/raw/esco/occupationSkillRelations_en.csv
  data/raw/esco/broaderRelationsSkillPillar.csv
  data/processed/courses.csv
  data/processed/course_skills.csv

Outputs:
  data/processed/skill_graph.pkl  — NetworkX MultiDiGraph pickle
  data/processed/skills.csv
  data/processed/skill_relations.csv
  data/processed/occupations.csv
  data/processed/occupation_skills.csv

Usage: python data/scripts/build_skill_graph.py
"""
import sys
import os
import csv
import pickle
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

RAW_ESCO = Path("data/raw/esco")
PROCESSED = Path("data/processed")


def build_skill_graph():
    PROCESSED.mkdir(parents=True, exist_ok=True)

    # --- 1. Load ESCO skills ---
    skills = {}
    skills_csv = RAW_ESCO / "skills_en.csv"
    if skills_csv.exists():
        with open(skills_csv, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                sid = row.get("skill_id") or row.get("conceptUri", "")
                label = row.get("preferred_label") or row.get("preferredLabel", "")
                if sid and label:
                    # Normalize URI to short ID if needed
                    if sid.startswith("http"):
                        sid = "esco_" + sid.split("/")[-1][:20]
                    skills[sid] = label
        logger.info("Loaded %d skills from ESCO", len(skills))
    else:
        logger.warning("No ESCO skills file found")

    # --- 2. Load ESCO occupations ---
    occupations = {}
    occ_csv = RAW_ESCO / "occupations_en.csv"
    if occ_csv.exists():
        with open(occ_csv, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                oid = row.get("occupation_id") or row.get("conceptUri", "")
                label = row.get("preferred_label") or row.get("preferredLabel", "")
                if oid and label:
                    if oid.startswith("http"):
                        oid = "esco_occ_" + oid.split("/")[-1][:20]
                    occupations[oid] = label
        logger.info("Loaded %d occupations from ESCO", len(occupations))

    # --- 3. Skill relations (broader → narrower) ---
    skill_relations = []
    broader_csv = RAW_ESCO / "broaderRelationsSkillPillar.csv"
    if broader_csv.exists():
        with open(broader_csv, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                broader = row.get("broader_skill") or row.get("broaderUri", "")
                narrower = row.get("narrower_skill") or row.get("conceptUri", "")
                if broader.startswith("http"):
                    broader = "esco_" + broader.split("/")[-1][:20]
                if narrower.startswith("http"):
                    narrower = "esco_" + narrower.split("/")[-1][:20]
                if broader in skills and narrower in skills:
                    skill_relations.append((broader, narrower))
        logger.info("Loaded %d skill relations", len(skill_relations))

    # --- 4. Occupation-skill relations ---
    occ_skill_rels = []
    occ_skill_csv = RAW_ESCO / "occupationSkillRelations_en.csv"
    if occ_skill_csv.exists():
        with open(occ_skill_csv, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                oid = row.get("occupation_id") or row.get("occupationUri", "")
                sid = row.get("skill_id") or row.get("skillUri", "")
                rel = row.get("relation_type") or row.get("relationType", "essential")
                if oid.startswith("http"):
                    oid = "esco_occ_" + oid.split("/")[-1][:20]
                if sid.startswith("http"):
                    sid = "esco_" + sid.split("/")[-1][:20]
                if (oid in occupations or oid.startswith("occ_")) and (sid in skills or sid.startswith("s_")):
                    occ_skill_rels.append((oid, sid, rel))
        logger.info("Loaded %d occupation-skill relations", len(occ_skill_rels))

    # --- 5. Write processed CSVs (for SkillGraph.build_from_processed) ---
    # skills.csv
    with open(PROCESSED / "skills.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["skill_id", "preferred_label"])
        w.writeheader()
        for sid, label in skills.items():
            w.writerow({"skill_id": sid, "preferred_label": label})

    # skill_relations.csv
    with open(PROCESSED / "skill_relations.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["broader_skill", "narrower_skill"])
        w.writeheader()
        for broader, narrower in skill_relations:
            w.writerow({"broader_skill": broader, "narrower_skill": narrower})

    # occupations.csv
    with open(PROCESSED / "occupations.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["occupation_id", "preferred_label"])
        w.writeheader()
        for oid, label in occupations.items():
            w.writerow({"occupation_id": oid, "preferred_label": label})

    # occupation_skills.csv
    with open(PROCESSED / "occupation_skills.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["occupation_id", "skill_id", "relation_type"])
        w.writeheader()
        for oid, sid, rel in occ_skill_rels:
            w.writerow({"occupation_id": oid, "skill_id": sid, "relation_type": rel})

    logger.info("Written processed ESCO CSVs to %s", PROCESSED)

    # --- 6. Build and save the graph ---
    from app.core.skill_graph import SkillGraph
    sg = SkillGraph()
    sg.build_from_processed(str(PROCESSED))
    sg.save(str(PROCESSED / "skill_graph.pkl"))

    logger.info("OK Skill graph saved: %d nodes, %d edges",
                sg.G.number_of_nodes(), sg.G.number_of_edges())
    return sg


if __name__ == "__main__":
    os.chdir(Path(__file__).parent.parent.parent)
    build_skill_graph()
