#!/usr/bin/env python3
"""
sync_releases.py
Syncs official APK releases from upstream GitHub repositories for all iOS-on-Android apps.
Automatically discovers the latest release assets and invokes build_repo.py to update the F-Droid repository.
"""

import os
import sys
import json
import zipfile
import io
import urllib.request
import subprocess

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'repo'))

APPS_UPSTREAM = [
    {
        "packageName": "org.touchhle.android",
        "name": "touchHLE",
        "repo": "touchHLE/touchHLE",
        "asset_pattern": "Android",
        "is_zip": True,
        "zip_entry": "touchHLE.apk"
    },
    {
        "packageName": "com.bluebubbles.messaging",
        "name": "BlueBubbles",
        "repo": "BlueBubblesApp/bluebubbles-app",
        "asset_pattern": "prod-release.apk",
        "is_zip": False
    },
    {
        "packageName": "com.moseoridev.warpshare",
        "name": "WarpShare",
        "repo": "moseoridev/WarpShare",
        "asset_pattern": ".apk",
        "is_zip": False
    },
    {
        "packageName": "de.seemoo.at_tracking_detection",
        "name": "AirGuard",
        "repo": "seemoo-lab/AirGuard",
        "asset_pattern": ".apk",
        "is_zip": False
    },
    {
        "packageName": "com.agupta07505.smartisland",
        "name": "SmartIsland",
        "repo": "agupta07505/SmartIsland",
        "asset_pattern": ".apk",
        "is_zip": False
    },
    {
        "packageName": "com.mccal.folio",
        "name": "Folio Launcher",
        "repo": "McCal-Codes/folio",
        "asset_pattern": ".apk",
        "is_zip": False
    },
    {
        "packageName": "oss.krtirtho.spotube",
        "name": "Spotube",
        "repo": "krtirtho/spotube",
        "asset_pattern": "android-all-arch.apk",
        "is_zip": False
    },
    {
        "packageName": "ml.docilealligator.infinityforreddit",
        "name": "Infinity for Reddit",
        "repo": "Docile-Alligator/Infinity-For-Reddit",
        "asset_pattern": "Infinity+-",
        "is_zip": False
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (IOSonDroid F-Droid Repo Sync)",
    "Accept": "application/vnd.github.v3+json"
}

def get_latest_release(repo_name):
    # Fetch recent releases to find one with assets
    url = f"https://api.github.com/repos/{repo_name}/releases?per_page=5"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            releases = json.loads(resp.read().decode('utf-8'))
            for rel in releases:
                if rel.get("assets"):
                    return rel
    except Exception as e:
        print(f"Error fetching releases for {repo_name}: {e}")
    return None

def sync_app(app_config):
    pkg = app_config["packageName"]
    name = app_config["name"]
    repo = app_config["repo"]
    pattern = app_config["asset_pattern"]
    
    print(f"\nChecking {name} ({repo})...")
    release = get_latest_release(repo)
    if not release:
        print(f"  No releases found for {name}.")
        return False
        
    tag = release.get("tag_name", "unknown")
    print(f"  Latest release: {tag}")
    
    # Find matching asset
    matching_asset = None
    for a in release.get("assets", []):
        if pattern.lower() in a["name"].lower():
            matching_asset = a
            break
            
    if not matching_asset:
        # Fallback to any APK
        for a in release.get("assets", []):
            if a["name"].endswith(".apk"):
                matching_asset = a
                break
                
    if not matching_asset:
        print(f"  No matching APK asset found in release {tag}.")
        return False
        
    asset_name = matching_asset["name"]
    download_url = matching_asset["browser_download_url"]
    size_mb = round(matching_asset["size"] / 1024 / 1024, 2)
    print(f"  Found asset: {asset_name} ({size_mb} MB)")
    
    # Target filename in repo/
    clean_tag = tag.lstrip('v').replace('+', '_').replace('-', '_')
    dest_filename = f"{pkg}_{clean_tag}.apk"
    dest_path = os.path.join(REPO_DIR, dest_filename)
    
    if os.path.exists(dest_path):
        print(f"  Asset already up to date: {dest_filename}")
        return True
        
    print(f"  Downloading from {download_url}...")
    req = urllib.request.Request(download_url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as resp:
        content = resp.read()
        
    if app_config.get("is_zip"):
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            zip_entry = app_config.get("zip_entry", "touchHLE.apk")
            with open(dest_path, "wb") as f:
                f.write(z.read(zip_entry))
    else:
        with open(dest_path, "wb") as f:
            f.write(content)
            
    print(f"  Successfully saved {dest_filename} ({os.path.getsize(dest_path)} bytes)")
    return True

def main():
    print("=== IOSonDroid Upstream Release Sync ===")
    os.makedirs(REPO_DIR, exist_ok=True)
    
    changed = False
    for app in APPS_UPSTREAM:
        try:
            if sync_app(app):
                changed = True
        except Exception as e:
            print(f"  Failed syncing {app['name']}: {e}")
            
    if changed:
        print("\nChanges detected. Running build_repo.py...")
        build_script = os.path.join(os.path.dirname(__file__), "build_repo.py")
        subprocess.run([sys.executable, build_script], check=True)
    else:
        print("\nAll releases are currently up to date.")

if __name__ == "__main__":
    main()
