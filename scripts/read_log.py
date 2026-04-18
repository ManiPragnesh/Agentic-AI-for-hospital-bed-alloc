def scan_log(encoding):
    try:
        with open("uvicorn_debug.log", "r", encoding=encoding, errors="replace") as f:
            content = f.read()
            print(f"--- DUMP ({encoding}) START ---")
            print(content)
            print(f"--- DUMP ({encoding}) END ---")
    except Exception as e:
        print(f"Error reading {encoding}: {e}")

scan_log("utf-16")
scan_log("cp1252")
