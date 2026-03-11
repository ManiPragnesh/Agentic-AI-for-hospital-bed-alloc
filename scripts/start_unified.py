import os
import subprocess
import sys
import time

def main():
    dev_mode = os.environ.get("UNIFIED_DEV", "0") == "1"
    port = os.environ.get("PORT", "8000")

    next_proc = None
    try:
        if dev_mode:
            os.environ["DEV_PROXY"] = "1"
            next_proc = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=os.path.join(os.path.dirname(__file__), "..", "frontend"),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            # Small delay to allow Next.js to start
            time.sleep(2)

        uvicorn_cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.server.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            port,
        ]
        if dev_mode:
            uvicorn_cmd.append("--reload")

        # Run uvicorn in foreground
        proc = subprocess.Popen(uvicorn_cmd)
        proc.wait()
    finally:
        if next_proc is not None:
            try:
                next_proc.terminate()
            except Exception:
                pass

if __name__ == "__main__":
    main()
