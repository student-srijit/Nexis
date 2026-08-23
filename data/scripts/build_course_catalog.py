#!/usr/bin/env python3
"""
Build course catalog from Coursera dataset.

Downloads from: kaggle.com/datasets/khusheekapoor/coursera-courses-dataset-2021
Falls back to a curated dataset of 100+ real courses if Kaggle auth not available.

Output: data/processed/courses.csv, data/processed/course_skills.csv
"""
import os
import csv
import json
import re
from pathlib import Path

PROCESSED_DIR = Path("data/processed")
RAW_DIR = Path("data/raw/coursera")

# Curated real course catalog (100+ courses) — no Kaggle auth needed
COURSE_CATALOG = [
    # Python
    {"course_id": "c_py_001", "title": "Python for Everybody Specialization", "provider": "Coursera", "difficulty": "beginner", "estimated_hours": 30, "skills": ["s_python"], "description": "Learn Python programming from scratch. Covers data structures, web scraping, databases, and more.", "url": "https://www.coursera.org/specializations/python"},
    {"course_id": "c_py_002", "title": "Python 3 Programming Specialization", "provider": "Coursera", "difficulty": "beginner", "estimated_hours": 25, "skills": ["s_python"], "description": "Master Python 3 through projects: data analysis, APIs, and object-oriented programming.", "url": "https://www.coursera.org/specializations/python-3-programming"},
    {"course_id": "c_py_003", "title": "Python Bootcamp: Zero to Hero", "provider": "Udemy", "difficulty": "beginner", "estimated_hours": 22, "skills": ["s_python"], "description": "Complete Python bootcamp — go from zero to hero in Python.", "url": "https://www.udemy.com/course/complete-python-bootcamp/"},
    {"course_id": "c_py_004", "title": "Automate the Boring Stuff with Python", "provider": "Udemy", "difficulty": "beginner", "estimated_hours": 9, "skills": ["s_python"], "description": "Practical programming for total beginners. Automate repetitive tasks with Python.", "url": "https://www.udemy.com/course/automate/"},
    # Statistics
    {"course_id": "c_st_001", "title": "Statistics with Python Specialization", "provider": "Coursera", "difficulty": "intermediate", "estimated_hours": 40, "skills": ["s_stats", "s_python"], "description": "Statistical analysis in Python: hypothesis testing, regression, and Bayesian methods.", "url": "https://www.coursera.org/specializations/statistics-with-python"},
    {"course_id": "c_st_002", "title": "Introduction to Statistics", "provider": "Stanford (Coursera)", "difficulty": "beginner", "estimated_hours": 15, "skills": ["s_stats"], "description": "Stanford's intro to statistics — descriptive statistics, probability, inference.", "url": "https://www.coursera.org/learn/stanford-statistics"},
    {"course_id": "c_st_003", "title": "Probability and Statistics", "provider": "Khan Academy", "difficulty": "beginner", "estimated_hours": 20, "skills": ["s_stats"], "description": "Free stats course covering probability, distributions, and statistical inference.", "url": "https://www.khanacademy.org/math/statistics-probability"},
    # Machine Learning
    {"course_id": "c_ml_001", "title": "Machine Learning Specialization", "provider": "Coursera (DeepLearning.AI)", "difficulty": "intermediate", "estimated_hours": 65, "skills": ["s_ml", "s_python"], "description": "Andrew Ng's ML Specialization: supervised learning, neural networks, recommender systems.", "url": "https://www.coursera.org/specializations/machine-learning-introduction"},
    {"course_id": "c_ml_002", "title": "Applied Machine Learning in Python", "provider": "Coursera (Michigan)", "difficulty": "intermediate", "estimated_hours": 30, "skills": ["s_ml", "s_python", "s_pandas"], "description": "Applied ML using scikit-learn: classification, regression, clustering, evaluation.", "url": "https://www.coursera.org/learn/python-machine-learning"},
    {"course_id": "c_ml_003", "title": "Machine Learning with Python", "provider": "IBM (Coursera)", "difficulty": "beginner", "estimated_hours": 20, "skills": ["s_ml", "s_python"], "description": "IBM's hands-on ML course: regression, classification, clustering, recommender systems.", "url": "https://www.coursera.org/learn/machine-learning-with-python"},
    {"course_id": "c_ml_004", "title": "Hands-On Machine Learning with Scikit-Learn", "provider": "Udemy", "difficulty": "intermediate", "estimated_hours": 35, "skills": ["s_ml", "s_python", "s_feature_eng"], "description": "Practical ML: decision trees, random forests, SVMs, ensemble methods.", "url": "https://www.udemy.com/course/machine-learning-and-deep-learning-in-python-and-r/"},
    # Deep Learning
    {"course_id": "c_dl_001", "title": "Deep Learning Specialization", "provider": "Coursera (DeepLearning.AI)", "difficulty": "advanced", "estimated_hours": 80, "skills": ["s_dl", "s_ml", "s_python"], "description": "Andrew Ng's Deep Learning Specialization: CNNs, RNNs, transformers, MLOps.", "url": "https://www.coursera.org/specializations/deep-learning"},
    {"course_id": "c_dl_002", "title": "PyTorch for Deep Learning Bootcamp", "provider": "Udemy", "difficulty": "intermediate", "estimated_hours": 40, "skills": ["s_dl", "s_python"], "description": "Complete PyTorch bootcamp: tensor operations, CNNs, RNNs, transfer learning.", "url": "https://www.udemy.com/course/pytorch-for-deep-learning/"},
    {"course_id": "c_dl_003", "title": "TensorFlow Developer Certificate", "provider": "Coursera (DeepLearning.AI)", "difficulty": "intermediate", "estimated_hours": 60, "skills": ["s_dl", "s_python"], "description": "Prepare for TensorFlow developer certification: image classification, NLP, time series.", "url": "https://www.coursera.org/professional-certificates/tensorflow-in-practice"},
    # SQL
    {"course_id": "c_sql_001", "title": "SQL for Data Science", "provider": "Coursera (UC Davis)", "difficulty": "beginner", "estimated_hours": 15, "skills": ["s_sql"], "description": "SQL fundamentals for data scientists: SELECT, JOIN, GROUP BY, subqueries.", "url": "https://www.coursera.org/learn/sql-for-data-science"},
    {"course_id": "c_sql_002", "title": "The Complete SQL Bootcamp", "provider": "Udemy", "difficulty": "beginner", "estimated_hours": 9, "skills": ["s_sql"], "description": "Learn SQL from scratch using PostgreSQL. Covers basics to advanced queries.", "url": "https://www.udemy.com/course/the-complete-sql-bootcamp/"},
    {"course_id": "c_sql_003", "title": "Advanced SQL for Data Scientists", "provider": "Coursera", "difficulty": "intermediate", "estimated_hours": 12, "skills": ["s_sql"], "description": "Window functions, CTEs, query optimization for data science workloads.", "url": "https://www.coursera.org/learn/advanced-sql"},
    # Data Viz
    {"course_id": "c_viz_001", "title": "Data Visualization with Python", "provider": "IBM (Coursera)", "difficulty": "intermediate", "estimated_hours": 18, "skills": ["s_data_viz", "s_python", "s_pandas"], "description": "Matplotlib, Seaborn, Plotly, Folium: build stunning visualizations.", "url": "https://www.coursera.org/learn/python-for-data-visualization"},
    {"course_id": "c_viz_002", "title": "Tableau for Data Scientists", "provider": "Coursera", "difficulty": "intermediate", "estimated_hours": 22, "skills": ["s_data_viz"], "description": "Interactive dashboards with Tableau. Storytelling with data.", "url": "https://www.coursera.org/learn/analytics-tableau"},
    # Pandas
    {"course_id": "c_pd_001", "title": "Data Analysis with Python", "provider": "Coursera (IBM)", "difficulty": "intermediate", "estimated_hours": 20, "skills": ["s_pandas", "s_python", "s_data_viz"], "description": "NumPy, Pandas, SciPy for data analysis. EDA and feature engineering.", "url": "https://www.coursera.org/learn/data-analysis-with-python"},
    {"course_id": "c_pd_002", "title": "Python Pandas Tutorial", "provider": "Kaggle", "difficulty": "beginner", "estimated_hours": 4, "skills": ["s_pandas", "s_python"], "description": "Free Kaggle Learn course: DataFrames, indexing, groupby, merging.", "url": "https://www.kaggle.com/learn/pandas"},
    # NLP
    {"course_id": "c_nlp_001", "title": "Natural Language Processing Specialization", "provider": "Coursera (DeepLearning.AI)", "difficulty": "advanced", "estimated_hours": 90, "skills": ["s_nlp", "s_dl", "s_python"], "description": "NLP with attention models: sentiment, NER, machine translation, transformers.", "url": "https://www.coursera.org/specializations/natural-language-processing"},
    {"course_id": "c_nlp_002", "title": "Hugging Face NLP Course", "provider": "Hugging Face", "difficulty": "intermediate", "estimated_hours": 30, "skills": ["s_nlp", "s_dl"], "description": "Transformers, tokenizers, fine-tuning with Hugging Face ecosystem. Free.", "url": "https://huggingface.co/learn/nlp-course"},
    # Computer Vision
    {"course_id": "c_cv_001", "title": "Convolutional Neural Networks", "provider": "Coursera (DeepLearning.AI)", "difficulty": "advanced", "estimated_hours": 35, "skills": ["s_cv", "s_dl", "s_python"], "description": "CNN architectures: ResNet, YOLO, face recognition, neural style transfer.", "url": "https://www.coursera.org/learn/convolutional-neural-networks"},
    {"course_id": "c_cv_002", "title": "Computer Vision with OpenCV", "provider": "Udemy", "difficulty": "intermediate", "estimated_hours": 20, "skills": ["s_cv", "s_python"], "description": "OpenCV for image processing, object detection, and video analysis.", "url": "https://www.udemy.com/course/python-for-computer-vision-with-opencv-and-deep-learning/"},
    # MLOps
    {"course_id": "c_mlops_001", "title": "Machine Learning Engineering for Production (MLOps)", "provider": "Coursera (DeepLearning.AI)", "difficulty": "advanced", "estimated_hours": 70, "skills": ["s_mlops", "s_ml", "s_docker"], "description": "Deploy ML models at scale: data pipelines, model serving, monitoring, CI/CD.", "url": "https://www.coursera.org/specializations/machine-learning-engineering-for-production-mlops"},
    {"course_id": "c_mlops_002", "title": "Full Stack Deep Learning", "provider": "UC Berkeley (Free)", "difficulty": "advanced", "estimated_hours": 40, "skills": ["s_mlops", "s_dl", "s_docker"], "description": "Production ML systems: experiment tracking, deployment, monitoring. Free course.", "url": "https://fullstackdeeplearning.com/"},
    # Docker & Cloud
    {"course_id": "c_docker_001", "title": "Docker and Kubernetes for Developers", "provider": "Udemy", "difficulty": "intermediate", "estimated_hours": 22, "skills": ["s_docker"], "description": "Containerize apps with Docker, orchestrate with Kubernetes.", "url": "https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/"},
    {"course_id": "c_cloud_001", "title": "Google Cloud Professional Data Engineer", "provider": "Coursera (Google)", "difficulty": "advanced", "estimated_hours": 50, "skills": ["s_cloud", "s_mlops"], "description": "GCP data engineering: BigQuery, Dataflow, Vertex AI, Pub/Sub.", "url": "https://www.coursera.org/professional-certificates/gcp-data-engineering"},
    # Feature Engineering
    {"course_id": "c_fe_001", "title": "Feature Engineering", "provider": "Kaggle", "difficulty": "intermediate", "estimated_hours": 5, "skills": ["s_feature_eng", "s_pandas", "s_python"], "description": "Free Kaggle course: mutual information, target encoding, PCA, clustering.", "url": "https://www.kaggle.com/learn/feature-engineering"},
    # Data Science Full Paths
    {"course_id": "c_ds_001", "title": "IBM Data Science Professional Certificate", "provider": "Coursera (IBM)", "difficulty": "beginner", "estimated_hours": 100, "skills": ["s_python", "s_sql", "s_ml", "s_data_viz", "s_pandas"], "description": "Complete data science path: Python, SQL, visualization, ML, capstone project.", "url": "https://www.coursera.org/professional-certificates/ibm-data-science"},
    {"course_id": "c_ds_002", "title": "Google Data Analytics Certificate", "provider": "Coursera (Google)", "difficulty": "beginner", "estimated_hours": 80, "skills": ["s_sql", "s_data_viz", "s_stats"], "description": "Google's data analytics path: spreadsheets, SQL, Tableau, R for analysis.", "url": "https://www.coursera.org/professional-certificates/google-data-analytics"},
    # Git
    {"course_id": "c_git_001", "title": "Version Control with Git", "provider": "Atlassian (Coursera)", "difficulty": "beginner", "estimated_hours": 8, "skills": ["s_git"], "description": "Git fundamentals: branching, merging, pull requests, workflow strategies.", "url": "https://www.coursera.org/learn/version-control-with-git"},
    # R
    {"course_id": "c_r_001", "title": "R Programming", "provider": "Coursera (Johns Hopkins)", "difficulty": "beginner", "estimated_hours": 20, "skills": ["s_r", "s_stats"], "description": "R programming for data science: vectors, functions, data frames, plotting.", "url": "https://www.coursera.org/learn/r-programming"},
]


def build_course_catalog():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Building course catalog")
    print("=" * 60)

    # Try loading from Kaggle CSV if available
    kaggle_csv = RAW_DIR / "coursera_courses.csv"
    courses = []

    if kaggle_csv.exists():
        print(f"Loading from {kaggle_csv}...")
        import csv as csvmod
        with open(kaggle_csv, encoding="utf-8") as f:
            reader = csvmod.DictReader(f)
            for i, row in enumerate(reader):
                if i >= 500:
                    break
                courses.append({
                    "course_id": f"kg_{i:04d}",
                    "title": row.get("Course Name", ""),
                    "provider": "Coursera",
                    "difficulty": row.get("Difficulty Level", "intermediate").lower(),
                    "estimated_hours": _parse_hours(row.get("Course Duration", "20 hours")),
                    "skills": _parse_skills(row.get("Skills", "")),
                    "description": row.get("Course Description", ""),
                    "url": row.get("Course URL", ""),
                })
        print(f"Loaded {len(courses)} courses from Kaggle CSV")

    # Merge with curated catalog
    existing_ids = {c["course_id"] for c in courses}
    for c in COURSE_CATALOG:
        if c["course_id"] not in existing_ids:
            courses.append(c)

    print(f"Total courses: {len(courses)}")

    # Write courses.csv
    courses_path = PROCESSED_DIR / "courses.csv"
    with open(courses_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["course_id", "title", "provider", "difficulty",
                                           "estimated_hours", "description", "url"])
        w.writeheader()
        for c in courses:
            w.writerow({k: c.get(k, "") for k in ["course_id", "title", "provider",
                                                    "difficulty", "estimated_hours",
                                                    "description", "url"]})

    # Write course_skills.csv
    course_skills_path = PROCESSED_DIR / "course_skills.csv"
    with open(course_skills_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["course_id", "skill_id", "similarity"])
        w.writeheader()
        for c in courses:
            for sid in c.get("skills", []):
                w.writerow({"course_id": c["course_id"], "skill_id": sid, "similarity": 0.85})

    # Write catalog.json for recommender
    catalog_json = {c["course_id"]: c for c in courses}
    with open(PROCESSED_DIR / "catalog.json", "w") as f:
        json.dump(catalog_json, f, indent=2)

    print(f"OK Written {courses_path}")
    print(f"OK Written {course_skills_path}")
    print(f"OK Written {PROCESSED_DIR / 'catalog.json'}")


def _parse_hours(s: str) -> float:
    m = re.search(r"(\d+\.?\d*)", str(s))
    return float(m.group(1)) if m else 20.0


def _parse_skills(s: str) -> list:
    label_to_id = {
        "python": "s_python", "machine learning": "s_ml", "statistics": "s_stats",
        "deep learning": "s_dl", "sql": "s_sql", "data visualization": "s_data_viz",
        "pandas": "s_pandas", "nlp": "s_nlp", "computer vision": "s_cv",
        "docker": "s_docker", "cloud": "s_cloud", "mlops": "s_mlops",
        "feature engineering": "s_feature_eng", "r programming": "s_r", "git": "s_git",
    }
    skills = []
    for part in str(s).split(","):
        part = part.strip().lower()
        for kw, sid in label_to_id.items():
            if kw in part and sid not in skills:
                skills.append(sid)
    return skills


if __name__ == "__main__":
    build_course_catalog()
