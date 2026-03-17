import os
import subprocess
import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
MODULES_DIR = "./modules"

# Define tasks: ReZygisk uses 'search', TreatWheel does not.
TELEGRAM_TASKS = [
    {
        "name": "TreatWheel/BetterKnown",
        "id": "-1002851992672",
        "limit": 2,
        "search": None
    },
    {
        "name": "ReZygisk",
        "id": "-1002786581440",
        "limit": 15,        # Higher limit to ensure we find a release in CI history
        "search": "release" # This ensures we only get the FIRST 'release' zip
    }
]

GITHUB_REPOS = [
    "Pixel-Props/BetterKnownInstalled", "bindhosts/bindhosts", "KOWX712/PlayIntegrityFix",
    "JingMatrix/LSPosed", "sidex15/susfs4ksu-module", "JingMatrix/TEESimulator",
    "5ec1cff/TrickyStore", "KOWX712/Tricky-Addon-Update-Target-List",
    "reveny/Android-VBMeta-Fixer", "XiaoTong6666/Sui", "j-hc/zygisk-detach"
]

def run_telegram_download(task):
    logging.info(f"--- Fetching Telegram: {task['name']} ---")
    cmd = ["venv/bin/python3", "main.py", task['id'], "--limit", str(task['limit']), "--format", "zip", "--output", MODULES_DIR]
    if task['search']:
        cmd.extend(["--search", task['search']])
    subprocess.run(cmd)

def download_github_release(repo_path):
    logging.info(f"--- Fetching GitHub: {repo_path} ---")
    try:
        data = requests.get(f"https://api.github.com/repos/{repo_path}/releases/latest").json()
        assets = data.get("assets", [])
        if not assets: return

        target = None
        if any(x in repo_path for x in ["LSPosed", "TEESimulator", "Sui"]):
            target = next((a for a in assets if "release" in a["name"].lower()), assets[0])
        else:
            target = assets[0]

        out_path = os.path.join(MODULES_DIR, target["name"])
        with requests.get(target["browser_download_url"], stream=True) as r:
            with open(out_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
        logging.info(f"Saved: {target['name']}")
    except Exception as e: logging.error(f"Error {repo_path}: {e}")

if __name__ == "__main__":
    os.makedirs(MODULES_DIR, exist_ok=True)
    for task in TELEGRAM_TASKS: run_telegram_download(task)
    for repo in GITHUB_REPOS: download_github_release(repo)
