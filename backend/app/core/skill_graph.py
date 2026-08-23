"""
Skill Graph — NetworkX MultiDiGraph backed by ESCO + course catalog.

Node types:
  skill       — ESCO skill/knowledge concept
  course      — course from catalog
  occupation  — ESCO occupation

Edges:
  skill → skill       (broader/prerequisite from ESCO skill relations)
  course → skill      (teaches, mapped by embedding similarity)
  occupation → skill  (essential/optional from ESCO occupation-skill links)

Exposes:
  shortest_gap_path(known_skills, target_occupation) -> List[str]
  courses_for_skill(skill_id) -> List[str]
"""
from __future__ import annotations
import os
import pickle
import json
import logging
from typing import List, Dict, Optional, Tuple, Set

import networkx as nx
import numpy as np

logger = logging.getLogger(__name__)


class SkillGraph:
    def __init__(self):
        self.G: nx.MultiDiGraph = nx.MultiDiGraph()
        self._skill_labels: Dict[str, str] = {}   # skill_id -> label
        self._course_meta: Dict[str, Dict] = {}   # course_id -> metadata
        self._occ_skills: Dict[str, List[str]] = {}  # occupation -> essential skills

    # ------------------------------------------------------------------ #
    # Build                                                                 #
    # ------------------------------------------------------------------ #

    def build_from_processed(self, processed_dir: str) -> None:
        """Build graph from pre-processed CSV files produced by build_skill_graph.py."""
        import pandas as pd

        skills_path = os.path.join(processed_dir, "skills.csv")
        skill_relations_path = os.path.join(processed_dir, "skill_relations.csv")
        courses_path = os.path.join(processed_dir, "courses.csv")
        course_skills_path = os.path.join(processed_dir, "course_skills.csv")
        occ_path = os.path.join(processed_dir, "occupations.csv")
        occ_skills_path = os.path.join(processed_dir, "occupation_skills.csv")

        logger.info("Building skill graph from %s", processed_dir)

        # Skills
        if os.path.exists(skills_path):
            df = pd.read_csv(skills_path)
            for _, row in df.iterrows():
                sid = str(row["skill_id"])
                label = str(row.get("preferred_label", sid))
                self.G.add_node(sid, node_type="skill", label=label)
                self._skill_labels[sid] = label

        # Skill relations (broader → narrower = prerequisite)
        if os.path.exists(skill_relations_path):
            df = pd.read_csv(skill_relations_path)
            for _, row in df.iterrows():
                src, tgt = str(row["broader_skill"]), str(row["narrower_skill"])
                if self.G.has_node(src) and self.G.has_node(tgt):
                    self.G.add_edge(src, tgt, edge_type="prerequisite")

        # Courses
        if os.path.exists(courses_path):
            df = pd.read_csv(courses_path)
            for _, row in df.iterrows():
                cid = str(row["course_id"])
                meta = row.to_dict()
                self.G.add_node(cid, node_type="course", **{k: str(v) for k, v in meta.items()})
                self._course_meta[cid] = meta

        # Course → skill edges (teaches)
        if os.path.exists(course_skills_path):
            df = pd.read_csv(course_skills_path)
            for _, row in df.iterrows():
                cid, sid = str(row["course_id"]), str(row["skill_id"])
                if self.G.has_node(cid) and self.G.has_node(sid):
                    sim = float(row.get("similarity", 1.0))
                    self.G.add_edge(cid, sid, edge_type="teaches", similarity=sim)

        # Occupations
        if os.path.exists(occ_path):
            df = pd.read_csv(occ_path)
            for _, row in df.iterrows():
                oid = str(row["occupation_id"])
                self.G.add_node(oid, node_type="occupation", label=str(row.get("preferred_label", oid)))

        # Occupation → skill edges
        if os.path.exists(occ_skills_path):
            df = pd.read_csv(occ_skills_path)
            for _, row in df.iterrows():
                oid, sid = str(row["occupation_id"]), str(row["skill_id"])
                rel = str(row.get("relation_type", "essential"))
                if self.G.has_node(oid) and self.G.has_node(sid):
                    self.G.add_edge(oid, sid, edge_type=rel)
                if rel == "essential":
                    self._occ_skills.setdefault(oid, []).append(sid)

        logger.info(
            "Graph built: %d nodes, %d edges",
            self.G.number_of_nodes(),
            self.G.number_of_edges(),
        )

    # ------------------------------------------------------------------ #
    # Persistence                                                           #
    # ------------------------------------------------------------------ #

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(
                {
                    "graph": self.G,
                    "skill_labels": self._skill_labels,
                    "course_meta": self._course_meta,
                    "occ_skills": self._occ_skills,
                },
                f,
            )
        logger.info("Saved skill graph to %s", path)

    def load(self, path: str) -> None:
        if not os.path.exists(path):
            logger.warning("Skill graph not found at %s — using empty graph", path)
            self._build_demo_graph()
            return
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.G = data["graph"]
        self._skill_labels = data["skill_labels"]
        self._course_meta = data["course_meta"]
        self._occ_skills = data["occ_skills"]
        logger.info(
            "Loaded skill graph: %d nodes, %d edges",
            self.G.number_of_nodes(),
            self.G.number_of_edges(),
        )

    # ------------------------------------------------------------------ #
    # Core query API                                                        #
    # ------------------------------------------------------------------ #

    def get_occupation_skills(self, occupation_id: str) -> List[str]:
        """Return essential skill IDs for an occupation."""
        return self._occ_skills.get(occupation_id, [])

    def shortest_gap_path(
        self, known_skills: List[str], target_occupation: str
    ) -> List[str]:
        """
        Return an ordered list of skill IDs from the learner's current frontier
        to the skills required by the target occupation.

        Strategy:
        1. Get essential skills for the occupation.
        2. Gap = required - known.
        3. Topological ordering of the skill subgraph (prerequisite edges only).
        4. Return the gap skills in topological order.
        """
        required = set(self.get_occupation_skills(target_occupation))
        known = set(known_skills)
        gap = required - known
        if not gap:
            return []

        # Build skill-only prerequisite subgraph
        skill_nodes = {n for n, d in self.G.nodes(data=True) if d.get("node_type") == "skill"}
        subgraph_nodes = gap | known
        # include nodes reachable from known to gap via prerequisite edges
        prereq_edges = [
            (u, v)
            for u, v, d in self.G.edges(data=True)
            if d.get("edge_type") == "prerequisite"
            and u in skill_nodes
            and v in skill_nodes
        ]
        sub = nx.DiGraph()
        sub.add_nodes_from(subgraph_nodes)
        for u, v in prereq_edges:
            if u in subgraph_nodes or v in subgraph_nodes:
                sub.add_edge(u, v)

        try:
            topo = list(nx.topological_sort(sub))
        except nx.NetworkXUnfeasible:
            topo = list(gap)

        # Filter to gap skills in topo order
        return [s for s in topo if s in gap]

    def courses_for_skill(self, skill_id: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Return (course_id, similarity) pairs for courses that teach `skill_id`,
        sorted by similarity descending.
        """
        results = []
        for pred in self.G.predecessors(skill_id):
            if self.G.nodes[pred].get("node_type") == "course":
                edge_data = self.G.get_edge_data(pred, skill_id)
                if edge_data:
                    # MultiDiGraph: edge_data is dict of {key: attr_dict}
                    sim = max(
                        v.get("similarity", 1.0)
                        for v in edge_data.values()
                        if v.get("edge_type") == "teaches"
                    ) if any(v.get("edge_type") == "teaches" for v in edge_data.values()) else 0.0
                    results.append((pred, sim))
        results.sort(key=lambda x: -x[1])
        return results[:top_k]

    def get_skill_label(self, skill_id: str) -> str:
        return self._skill_labels.get(skill_id, skill_id)

    def get_course_meta(self, course_id: str) -> Dict:
        return self._course_meta.get(course_id, {})

    def skill_exists(self, skill_id: str) -> bool:
        return self.G.has_node(skill_id) and self.G.nodes[skill_id].get("node_type") == "skill"

    def occupation_exists(self, occ_id: str) -> bool:
        return self.G.has_node(occ_id) and self.G.nodes[occ_id].get("node_type") == "occupation"

    def find_occupation_by_label(self, label: str) -> Optional[str]:
        label_lower = label.lower()
        for n, d in self.G.nodes(data=True):
            if d.get("node_type") == "occupation":
                if label_lower in d.get("label", "").lower():
                    return n
        return None

    def find_skill_by_label(self, label: str) -> Optional[str]:
        label_lower = label.lower()
        for n, d in self.G.nodes(data=True):
            if d.get("node_type") == "skill":
                if label_lower in d.get("label", "").lower():
                    return n
        return None

    # ------------------------------------------------------------------ #
    # Demo graph (fallback when no data files are present)                  #
    # ------------------------------------------------------------------ #

    def _build_demo_graph(self) -> None:
        """Minimal demo graph for development without data files."""
        logger.warning("Using demo skill graph — run data/scripts/ to build the real one")
        skills = {
            "s_python": "Python Programming",
            "s_ml": "Machine Learning",
            "s_stats": "Statistics",
            "s_dl": "Deep Learning",
            "s_data_viz": "Data Visualization",
            "s_sql": "SQL",
            "s_pandas": "Data Manipulation with Pandas",
        }
        for sid, label in skills.items():
            self.G.add_node(sid, node_type="skill", label=label)
            self._skill_labels[sid] = label

        prereqs = [
            ("s_python", "s_pandas"),
            ("s_stats", "s_ml"),
            ("s_python", "s_ml"),
            ("s_ml", "s_dl"),
            ("s_pandas", "s_data_viz"),
        ]
        for src, tgt in prereqs:
            self.G.add_edge(src, tgt, edge_type="prerequisite")

        courses = [
            ("c1", "Python for Everybody", ["s_python"], "beginner", 30, "Coursera"),
            ("c2", "Statistics for Data Science", ["s_stats"], "beginner", 20, "Coursera"),
            ("c3", "Machine Learning Specialization", ["s_ml"], "intermediate", 60, "Coursera"),
            ("c4", "Deep Learning Specialization", ["s_dl"], "advanced", 80, "Coursera"),
            ("c5", "Data Visualization with Python", ["s_data_viz", "s_pandas"], "intermediate", 25, "Coursera"),
            ("c6", "SQL for Data Analysis", ["s_sql"], "beginner", 15, "Udemy"),
            ("c7", "Pandas & Data Wrangling", ["s_pandas"], "intermediate", 20, "Kaggle"),
        ]
        for cid, title, skills_taught, diff, hours, provider in courses:
            self.G.add_node(cid, node_type="course", title=title, difficulty=diff,
                            estimated_hours=hours, provider=provider,
                            description=f"Learn {title} skills.")
            self._course_meta[cid] = {"course_id": cid, "title": title, "difficulty": diff,
                                       "estimated_hours": hours, "provider": provider}
            for sid in skills_taught:
                self.G.add_edge(cid, sid, edge_type="teaches", similarity=0.9)

        occupations = {
            "occ_ds": "Data Scientist",
            "occ_ml_eng": "Machine Learning Engineer",
            "occ_da": "Data Analyst",
        }
        for oid, label in occupations.items():
            self.G.add_node(oid, node_type="occupation", label=label)

        occ_skill_map = {
            "occ_ds": ["s_python", "s_ml", "s_stats", "s_dl", "s_data_viz", "s_sql"],
            "occ_ml_eng": ["s_python", "s_ml", "s_dl", "s_pandas"],
            "occ_da": ["s_python", "s_sql", "s_data_viz", "s_pandas", "s_stats"],
        }
        for oid, sids in occ_skill_map.items():
            self._occ_skills[oid] = sids
            for sid in sids:
                self.G.add_edge(oid, sid, edge_type="essential")
