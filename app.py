import os
import time
import threading
import subprocess
from flask import Flask, jsonify

# Read global settings from env
TIMETREE_EMAIL = os.getenv("TIMETREE_EMAIL")
TIMETREE_PASSWORD = os.getenv("TIMETREE_PASSWORD")
SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL_MINUTES", "15"))

OUTPUT_DIR = "/app/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = Flask(__name__)


def get_all_units():
    """
    Parse all env variables that look like:
    UNIT_NAME=TIMETREE_ID|GOOGLE_CALENDAR_ID
    """
    units = []
    for key, value in os.environ.items():
        # Skip base/system vars
        if key in ["TIMETREE_EMAIL", "TIMETREE_PASSWORD", "SYNC_INTERVAL_MINUTES", "PORT", "OUTPUT_FILE"]:
            continue

        if "|" in value:
            timetree_id, google_id = value.split("|", 1)
            units.append({
                "name": key,
                "timetree_id": timetree_id.strip(),
                "google_id": google_id.strip(),
            })

    return units


def sync_one_unit(unit):
    """
    Run timetree-exporter for a single unit and write an .ics file.
    """
    print(f"=== Syncing {unit['name']} ===")
    print(f"  TimeTree ID: {unit['timetree_id']}")
    print(f"  Google Cal:  {unit['google_id']}")

    output_file = os.path.join(OUTPUT_DIR, f"{unit['name']}.ics")

    # timetree-exporter uses TIMETREE_EMAIL and TIMETREE_PASSWORD from env
    env = os.environ.copy()
    if TIMETREE_EMAIL:
        env["TIMETREE_EMAIL"] = TIMETREE_EMAIL
    if TIMETREE_PASSWORD:
        env["TIMETREE_PASSWORD"] = TIMETREE_PASSWORD

    cmd = [
        "timetree-exporter",
        "-e", TIMETREE_EMAIL,                # email (optional, but nice)
        "-c", unit["timetree_id"],           # calendar code
        "-o", output_file,                   # where to save the ICS
    ]

    print("  Running:", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    print("  --- STDOUT ---")
    print(result.stdout)
    print("  --- STDERR ---")
    print(result.stderr)
    print(f"  => ICS written to {output_file}")
    print("=== Done ===\n")


def sync_loop():
    """
    Background loop: every SYNC_INTERVAL minutes, export all units.
    """
    while True:
        units = get_all_units()
        print("Units found:", units)

        if not units:
            print("No units found in env. Sleeping...")
        else:
            for unit in units:
                try:
                    sync_one_unit(unit)
                except Exception as e:
                    print(f"Error syncing {unit['name']}: {e}")

        print(f"Sleeping {SYNC_INTERVAL} minutes...\n")
        time.sleep(SYNC_INTERVAL * 60)


@app.route("/")
def index():
    """
    Simple status endpoint to check container + env parsing.
    """
    return jsonify({
        "status": "running",
        "sync_interval_minutes": SYNC_INTERVAL,
        "units": get_all_units(),
    })


if __name__ == "__main__":
    print("Starting timetree-sync service...")
    print(f"TIMETREE_EMAIL set: {bool(TIMETREE_EMAIL)}")
    print(f"SYNC_INTERVAL_MINUTES: {SYNC_INTERVAL}")
    print("Output dir:", OUTPUT_DIR)

    # Start background sync thread
    threading.Thread(target=sync_loop, daemon=True).start()

    # Start Flask
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
