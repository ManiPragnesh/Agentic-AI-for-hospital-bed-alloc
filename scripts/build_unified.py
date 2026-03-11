import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND = os.path.join(ROOT, "frontend")

def run(cmd, cwd=None):
    print(">", " ".join(cmd))
    subprocess.check_call(cmd, cwd=cwd or ROOT)

def main():
    # Install frontend deps and build + export static site
    run(["npm", "install"], cwd=FRONTEND)
    run(["npm", "run", "build"], cwd=FRONTEND)
    # next export is automatic with output: 'export' in next config during build
    print("Build finished. Static files at frontend/out")

    # Optionally, verify index exists
    out_dir = os.path.join(FRONTEND, "out")
    index_html = os.path.join(out_dir, "index.html")
    if not os.path.isfile(index_html):
        print("Warning: index.html not found in frontend/out. Check Next export settings.", file=sys.stderr)

if __name__ == "__main__":
    main()
