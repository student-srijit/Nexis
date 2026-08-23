#!/usr/bin/env python3
"""
setup.py — One-shot setup script for Nexis.
Run this first to download data and train all models.

Usage: python setup.py
"""
import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent
os.chdir(ROOT)

def run(cmd, **kwargs):
    print(f"\n{'='*60}")
    print(f"▶ {cmd}")
    print('='*60)
    result = subprocess.run(cmd, shell=True, **kwargs)
    if result.returncode != 0:
        print(f"⚠ Command exited with code {result.returncode}")
    return result.returncode == 0

def main():
    print("🚀 Nexis Setup")
    print("="*60)

    # 1. Create .env if not exists
    env_path = ROOT / ".env"
    if not env_path.exists():
        env_path.write_text("OPENROUTER_API_KEY=\n# Get a free key at: https://openrouter.ai/\n")
        print("✓ Created .env (add your OPENROUTER_API_KEY for AI explanations)")

    # 2. Install Python deps
    print("\n📦 Installing Python dependencies…")
    run(f"{sys.executable} -m pip install -r backend/requirements.txt --quiet")

    # 3. Download data
    print("\n📥 Downloading ESCO data…")
    run(f"{sys.executable} data/scripts/download_esco.py")

    print("\n📥 Building course catalog…")
    run(f"{sys.executable} data/scripts/build_course_catalog.py")

    print("\n📥 Attempting OULAD download (may fall back to synthetic)…")
    run(f"{sys.executable} data/scripts/download_oulad.py")

    # 4. Build skill graph
    print("\n🕸 Building skill graph…")
    sys.path.insert(0, str(ROOT / "backend"))
    run(f"{sys.executable} data/scripts/build_skill_graph.py")

    # 5. Train ML models
    print("\n🧠 Training BKT mastery model…")
    run(f"{sys.executable} ml/knowledge_tracing/train_bkt.py")

    print("\n📊 Building embeddings & training LightGBM ranker…")
    run(f"{sys.executable} ml/embeddings/build_index.py")

    print("\n" + "="*60)
    print("✅ Setup complete!")
    print("="*60)
    print("\nTo start the app:")
    print("  Option A (direct):  cd backend && uvicorn app.main:app --reload")
    print("                      cd frontend && npm install && npm run dev")
    print("  Option B (Docker):  docker-compose up --build")
    print("\nFrontend: http://localhost:5173")
    print("Backend:  http://localhost:8000")
    print("API docs: http://localhost:8000/docs")
    print("\n💡 Add OPENROUTER_API_KEY to .env for AI explanations (free tier)")

if __name__ == "__main__":
    main()


