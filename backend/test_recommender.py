import os
import time

def test_load():
    print("Testing Recommender...")
    from app.core.recommender import Recommender
    rec = Recommender()
    recommender_dir = os.getenv("RECOMMENDER_DIR", "data/processed/recommender")
    
    catalog_path = os.path.join(recommender_dir, "catalog.json")
    embeddings_path = os.path.join(recommender_dir, "course_embeddings.npy")
    course_ids_path = os.path.join(recommender_dir, "course_ids.json")
    ranker_path = os.path.join(recommender_dir, "ranker.pkl")
    skill_emb_path = os.path.join(recommender_dir, "skill_embeddings.pkl")

    print("Loading encoder...")
    rec._load_encoder()
    print("Encoder loaded.")

    print("Loading catalog...")
    import json
    if os.path.exists(catalog_path):
        with open(catalog_path) as f:
            rec._course_catalog = json.load(f)
    print("Catalog loaded.")

    print("Loading embeddings...")
    import numpy as np
    if os.path.exists(course_ids_path):
        with open(course_ids_path) as f:
            rec._course_ids = json.load(f)
    if os.path.exists(embeddings_path) and rec._course_ids:
        rec._course_embeddings = np.load(embeddings_path)
        print("Building faiss index...")
        rec._build_faiss_index()
    print("Embeddings loaded.")

    print("Loading ranker...")
    import pickle
    if os.path.exists(ranker_path):
        with open(ranker_path, "rb") as f:
            rec._ranker = pickle.load(f)
    print("Ranker loaded.")

    print("Loading skill embs...")
    if os.path.exists(skill_emb_path):
        with open(skill_emb_path, "rb") as f:
            rec._skill_embeddings = pickle.load(f)
    print("Done!")

if __name__ == "__main__":
    test_load()
