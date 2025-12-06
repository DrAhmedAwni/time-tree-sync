import os
import time
import threading
import subprocess
from flask import Flask, send_file, abort

OUTPUT_FILE = os.getenv("OUTPUT_FILE", "timetree.ics")
SYNC_INTERVAL_MINUTES = int(os.getenv("SYNC_INTERVAL_MINUTES", "15"))
CAL_CODE = os.getenv("TIMETREE_CAL_CODE")

def run_exporter():
    if not CAL_CODE:
        print("TIMETREE_CAL_CODE not set")
        return

    print("Running TimeTree exporter...")
    cmd = [
        "timetree-exporter",
        "-c", CAL_CODE,
        "-o", OUTPUT_FILE,
    ]
    # Email & password come from env:
    # TIMETREE_EMAIL and TIMETREE_PASSWORD (used by timetree-exporter)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("Exporter failed:", result.stderr)
    else:
        print("Exporter finished successfully")

def sync_loop():
    while True:
        try:
            run_exporter()
        except Exception as e:
            print("Error in sync_loop:", e)
        time.sleep(SYNC_INTERVAL_MINUTES * 60)

app = Flask(__name__)

@app.route("/calendar.ics")
def calendar():
    if not os.path.exists(OUTPUT_FILE):
        return abort(404, description="ICS file not generated yet")
    return send_file(OUTPUT_FILE, mimetype="text/calendar")

if __name__ == "__main__":
    # Run once on start so Google doesn't get 404
    run_exporter()

    # Background sync every X minutes
    threading.Thread(target=sync_loop, daemon=True).start()

    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
