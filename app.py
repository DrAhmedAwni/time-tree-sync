import os
import time
import threading
import subprocess
from flask import Flask, jsonify

TIMETREE_EMAIL = os.getenv("TIMETREE_EMAIL")
TIMETREE_PASSWORD = os.getenv("TIMETREE_PASSWORD")
SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL_MINUTES", "15"))

app = Flask(__name__)

def get_all_units():
    units = []
    for key, value in os.environ.items():
        # Skip system / base variables
        if key in ["TIMETREE_EMAIL", "TIMETREE_PASSWORD", "SYNC_INTERVAL_MINUTES", "PORT"]:
            continue
        
        if "|" in value:
            timetree_id, google_id = value.split("|")
            units.append({
                "name": key,
                "timetree_id": timetree_id.strip(),
                "google_id": google_id.strip()
            })

    return units


def sync_one_unit(unit):
    print(f"Syncing {unit['name']} → TimeTree:{unit['timetree_id']} → Google:{unit['google_id']}")

    cmd = [
        "timetree-exporter",
        "-e", TIMETREE_EMAIL,
        "-p", TIMETREE_PASSWORD,
        "-c", unit["timetree_id"],
        "--google-calendar", unit["google_id"]
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)


def sync_loop():
    while True:
        units = get_all_units()
        print("Units found:", units)

        for unit in units:
            sync_one_unit(unit)

        time.sleep(SYNC_INTERVAL * 60)


@app.route("/")
def index():
    return jsonify({"status": "running", "units": get_all_units()})


if __name__ == "__main__":
    threading.Thread(target=sync_loop, daemon=True).start()
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
