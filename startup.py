import os
import subprocess
import requests

meilisearch_running = False
MEILI_DIR = ""
MEILI_FILE = ""
MEILI_KEY = ""

print("Running Startup")

try:
    requests.get("http://localhost:7700")
    print("Meilisearch is already running")
    meilisearch_running = True

except requests.exceptions.ConnectionError:
    print("Meilisearch is not running")
    print("Starting Meilisearch")
    command = f'start cmd /k "{os.path.join(MEILI_DIR, MEILI_FILE)} --master-key={MEILI_KEY}"'
    subprocess.Popen(command, shell=True, cwd=MEILI_DIR)

try:
    print("Update database.db? y/n? (Will delete all data in database)")
    if input() == "y":
        os.remove("database/sqlite/database.db")
        print("Deleted database.db")
        print("Updated database.db")
except PermissionError:
    print("database.db is in use. Please close the script or program that uses the database and run this script again.")
    exit(1)