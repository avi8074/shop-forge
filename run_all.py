"""
Run All Services - Single Unified Web Application
Integrates:
- ShopForge e-Commerce Store & SQLite Catalog
- AI Multi-Modal Product Intelligence (Gemini / OpenRouter / CV & OCR)
- Cloudinary Media Pipeline (Uploads, Background Removal, Smart Crop)
- VisualDraft Single-Page Web Application
"""

import subprocess
import sys
import os
import shutil
import time

def ensure_frontend_built(workspace: str):
    dist_dir = os.path.join(workspace, "dist")
    visualdraft_dir = os.path.join(workspace, "visualdraft (2)")
    vd_dist = os.path.join(visualdraft_dir, "dist")

    if not os.path.exists(dist_dir) or not os.path.exists(os.path.join(dist_dir, "index.html")):
        print("[Build] Compiling VisualDraft frontend for single web delivery...")
        try:
            subprocess.run("npm run build", cwd=visualdraft_dir, shell=True, check=True)
            if os.path.exists(vd_dist):
                if os.path.exists(dist_dir):
                    shutil.rmtree(dist_dir)
                shutil.copytree(vd_dist, dist_dir)
                print("[Build] Frontend successfully compiled and synced to root dist.")
        except Exception as e:
            print(f"[Warning] Failed to compile frontend automatically: {e}")

def main():
    workspace = os.path.dirname(os.path.abspath(__file__))
    media_dir = os.path.join(workspace, "media-pipeline")

    ensure_frontend_built(workspace)

    print("==================================================================")
    print("  🚀 UNIFIED SHOPFORGE & AI PRODUCT INTELLIGENCE WEB PLATFORM")
    print("==================================================================")
    print("  ⭐ Main Single Web UI:   http://localhost:8000")
    print("  📚 API Interactive Docs: http://localhost:8000/docs")
    print("  🏥 Health Diagnostics:   http://localhost:8000/health")
    print("==================================================================")

    # 1. Start Media Pipeline (Node.js) if node modules exist
    node_proc = None
    if os.path.exists(os.path.join(media_dir, "node_modules")):
        print("Starting Cloudinary Media Pipeline service on port 5001...")
        node_cmd = "npm start"
        try:
            node_proc = subprocess.Popen(node_cmd, cwd=media_dir, shell=True)
        except Exception as e:
            print(f"[Notice] Media pipeline process skipped: {e}")

    # 2. Start FastAPI Unified Backend (Python)
    print("Starting Unified FastAPI Server on http://localhost:8000 ...")
    fastapi_cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
    py_proc = subprocess.Popen(fastapi_cmd, cwd=workspace)

    try:
        while True:
            time.sleep(1)
            if py_proc.poll() is not None:
                print(f"[Warning] FastAPI Backend stopped with exit code {py_proc.returncode}")
                break
    except KeyboardInterrupt:
        print("\nShutting down unified platform...")
        if node_proc:
            node_proc.terminate()
        py_proc.terminate()
        print("Done.")

if __name__ == "__main__":
    main()
