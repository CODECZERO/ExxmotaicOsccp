import requests
import json
import time
import subprocess

p = subprocess.Popen(["./venv/bin/python", "run_services.py"])
time.sleep(5)

try:
    r = requests.get("http://127.0.0.1:5050/api/dashboard")
    print(r.status_code, json.dumps(r.json(), indent=2))
    
    r2 = requests.get("http://127.0.0.1:5050/api/live/snapshot")
    print(r2.status_code, json.dumps(r2.json(), indent=2))
finally:
    p.terminate()
