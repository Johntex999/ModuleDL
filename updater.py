import os
import requests
import logging
import re

logging.basicConfig(level=logging.INFO, format="%(message)s")
MODULES_DIR = "./modules"

GITHUB_REPOS = [
    "Pixel-Props/BetterKnownInstalled", "bindhosts/bindhosts", "KOWX712/PlayIntegrityFix",
    "JingMatrix/LSPosed", "sidex15/susfs4ksu-module", "JingMatrix/TEESimulator",
    "Enginex0/TEESimulator-RS", "5ec1cff/TrickyStore", "KOWX712/Tricky-Addon-Update-Target-List",
    "reveny/Android-VBMeta-Fixer", "XiaoTong6666/Sui", "j-hc/zygisk-detach",
    "PerformanC/Treat-Wheel-Zygisk", "frknkrc44/HMA-OSS"
]

def download_github_release(repo_path):
    logging.info(f"--- Fetching GitHub: {repo_path} ---")
    try:
        # Get tag name by redirecting on /releases/latest
        r = requests.get(f"https://github.com/{repo_path}/releases/latest", allow_redirects=True)
        if "/tag/" not in r.url:
            logging.warning(f"Could not find latest tag for {repo_path}")
            return
        tag = r.url.split("/tag/")[-1]
        
        # Get the actual repository path (handles redirects like JingMatrix/LSPosed -> JingMatrix/Vector)
        actual_repo = r.url.split("github.com/")[-1].split("/releases/tag/")[0]
        
        # Get expanded assets page
        assets_url = f"https://github.com/{actual_repo}/releases/expanded_assets/{tag}"
        assets_resp = requests.get(assets_url)
        assets_resp.raise_for_status()
        
        # Find all download links (href starts with /repo/releases/download/tag/...)
        links = re.findall(rf'href="([^"]*/releases/download/{re.escape(tag)}/[^"]*)"', assets_resp.text)
        if not links:
            links = re.findall(r'href="([^"]*/releases/download/[^"]*)"', assets_resp.text)
            
        if not links:
            logging.warning(f"No release assets found for {repo_path}")
            return
            
        # Select the target asset
        # 1. Prefer a link with "release" in the filename (not the full path).
        # 2. Otherwise, prefer a link that doesn't have "debug" in the filename.
        # 3. Otherwise, fall back to the first link.
        release_candidates = [l for l in links if "release" in l.split("/")[-1].lower()]
        non_debug_candidates = [l for l in links if "debug" not in l.split("/")[-1].lower()]
        
        if release_candidates:
            target_link = release_candidates[0]
        elif non_debug_candidates:
            target_link = non_debug_candidates[0]
        else:
            target_link = links[0]
            
        filename = target_link.split("/")[-1]
        download_url = f"https://github.com{target_link}"
        
        out_path = os.path.join(MODULES_DIR, filename)
        with requests.get(download_url, stream=True) as download_r:
            download_r.raise_for_status()
            with open(out_path, 'wb') as f:
                for chunk in download_r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logging.info(f"Saved: {filename}")
    except Exception as e:
        logging.error(f"Error fetching {repo_path}: {e}")

def download_rezygisk():
    logging.info("--- Fetching ReZygisk (via nightly.link) ---")
    try:
        url = "https://nightly.link/PerformanC/ReZygisk/workflows/trusted_ci/main"
        resp = requests.get(url)
        resp.raise_for_status()
        
        # Find hrefs ending with -release.zip
        links = re.findall(r'href="([^"]*-release\.zip)"', resp.text)
        if not links:
            logging.error("Could not find ReZygisk release download link on nightly.link")
            return
        
        download_url = links[0]
        filename = download_url.split("/")[-1]
        out_path = os.path.join(MODULES_DIR, filename)
        
        with requests.get(download_url, stream=True) as download_r:
            download_r.raise_for_status()
            with open(out_path, 'wb') as f:
                for chunk in download_r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logging.info(f"Saved: {filename}")
    except Exception as e:
        logging.error(f"Error downloading ReZygisk: {e}")

if __name__ == "__main__":
    os.makedirs(MODULES_DIR, exist_ok=True)
    
    # Download GitHub Releases
    for repo in GITHUB_REPOS:
        download_github_release(repo)
        
    # Download ReZygisk
    download_rezygisk()
