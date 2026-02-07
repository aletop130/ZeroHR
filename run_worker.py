"""
ZeroHR Worker Entry Point
Run with: python run_worker.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from backend.main import celery_app
    import subprocess
    
    subprocess.run([
        "celery", "-A", "backend.main.celery_app", "worker",
        "--loglevel=info", "--concurrency=7", "--pool=threads"
    ])
