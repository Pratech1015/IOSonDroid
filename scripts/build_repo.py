#!/usr/bin/env python3
"""
build_repo.py
Comprehensive F-Droid Repository Builder and Signer for IOSonDroid.

Generates:
- repo/index-v1.json (F-Droid Index v1 specification)
- repo/index-v2.json (F-Droid Index v2 specification)
- repo/index.xml     (F-Droid legacy XML index)
- repo/index.jar     (Cryptographically signed JAR index)
- repo/index-v1.jar  (Cryptographically signed JAR index v1)
- assets/catalog.json (Static web catalog for index.html frontend)
"""

import os
import sys
import glob
import json
import time
import zipfile
import hashlib
import struct
import subprocess
import xml.etree.ElementTree as ET
import yaml
from cryptography import x509
from cryptography.hazmat.backends import default_backend

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'repo'))
METADATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'metadata'))
KEYSTORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'keystore'))
ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets'))

KEYSTORE_PATH = os.path.join(KEYSTORE_DIR, 'repokey.p12')
KEYSTORE_PASS = 'iosondroid-repo-key'
KEY_ALIAS = 'iosondroid'

REPO_BASE_URL = 'https://pratech1015.github.io/IOSonDroid/repo'
REPO_NAME = 'IOSonDroid'
REPO_DESCRIPTION = 'F-Droid repository for iOS-exclusive apps and Apple ecosystem experiences built for Android.'

# Known versions mapping for official releases
VERSION_MAPPINGS = {
    "org.touchhle.android": {30: "0.3.0", 20: "0.2.2"},
    "com.moseoridev.warpshare": {204: "2.0.4", 200: "2.0.0"},
    "de.seemoo.at_tracking_detection": {88: "3.1.3", 87: "3.1.2"},
    "com.agupta07505.smartisland": {70: "7.0.0", 60: "6.0.0"},
    "com.mccal.folio": {68: "0.6.8", 60: "0.6.0"},
    "com.bluebubbles.messaging": {92: "2.1.2", 93: "2.1.3"},
    "oss.krtirtho.spotube": {512: "5.1.2"},
    "ml.docilealligator.infinityforreddit": {833: "8.3.3"},
    "io.iosondroid.calculator": {10: "1.0.0"},
    "io.iosondroid.notes": {10: "1.0.0"},
    "io.iosondroid.controlcenter": {10: "1.0.0"},
    "de.seemoo.openhaystack": {53: "0.5.3"}
}

def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def extract_apk_signer(apk_path):
    """Extract SHA-256 fingerprint of the signing certificate from APK META-INF."""
    try:
        with zipfile.ZipFile(apk_path, 'r') as z:
            for name in z.namelist():
                if name.startswith('META-INF/') and (name.endswith('.RSA') or name.endswith('.DSA') or name.endswith('.EC')):
                    cert_data = z.read(name)
                    try:
                        cert = x509.load_der_x509_certificate(cert_data, default_backend())
                        return cert.fingerprint(hashlib.sha256()).hex().lower()
                    except Exception:
                        return hashlib.sha256(cert_data).hexdigest().lower()
    except Exception:
        pass
    return hashlib.sha256(b"iosondroid-default-signer").hexdigest().lower()

def extract_apk_info(apk_path, known_packages):
    """Extract package name, version, and SDK info from APK file and name."""
    filename = os.path.basename(apk_path)
    file_size = os.path.getsize(apk_path)
    file_sha256 = get_file_sha256(apk_path)
    signer_hash = extract_apk_signer(apk_path)
    
    pkg_name = None
    version_code = 1
    
    # 1. Match against known packages
    for kp in known_packages:
        if filename.startswith(kp):
            pkg_name = kp
            suffix = filename[len(kp):].replace('.apk', '').lstrip('_')
            if suffix.isdigit():
                version_code = int(suffix)
            break
            
    if not pkg_name:
        parts = filename.replace('.apk', '').rsplit('_', 1)
        pkg_name = parts[0]
        if len(parts) > 1 and parts[1].isdigit():
            version_code = int(parts[1])
            
    # Resolve versionName
    version_name = VERSION_MAPPINGS.get(pkg_name, {}).get(version_code)
    if not version_name:
        if version_code >= 100:
            version_name = f"{version_code // 100}.{(version_code % 100) // 10}.{version_code % 10}"
        elif version_code >= 10:
            version_name = f"{version_code // 10}.{version_code % 10}"
        else:
            version_name = f"1.0.{version_code}"
            
    return {
        "packageName": pkg_name,
        "versionCode": version_code,
        "versionName": version_name,
        "apkName": filename,
        "hash": file_sha256,
        "hashType": "sha256",
        "size": file_size,
        "minSdkVersion": 21,
        "targetSdkVersion": 34,
        "signer": signer_hash,
        "added": int(time.time() * 1000)
    }

def load_all_metadata():
    metadata = {}
    for f in sorted(glob.glob(os.path.join(METADATA_DIR, '*.yml'))):
        with open(f, 'r', encoding='utf-8') as yf:
            data = yaml.safe_load(yf)
            pkg = data.get('packageName')
            if pkg:
                metadata[pkg] = data
    return metadata

def get_repo_fingerprint():
    fp_path = os.path.join(KEYSTORE_DIR, 'fingerprint.txt')
    if os.path.exists(fp_path):
        with open(fp_path, 'r') as f:
            return f.read().strip()
    return ""

def build_index_v1(apps_dict, packages_dict, fingerprint, timestamp):
    apps_list = []
    for pkg, meta in apps_dict.items():
        pkgs = packages_dict.get(pkg, [])
        suggested_vc = pkgs[0]['versionCode'] if pkgs else 1
        apps_list.append({
            "packageName": pkg,
            "name": meta.get("Name", pkg),
            "summary": meta.get("Summary", ""),
            "description": f"<p>{meta.get('Description', '').replace(chr(10), '<br/>')}</p>",
            "icon": f"{pkg}.png",
            "license": meta.get("License", "Unknown"),
            "authorName": meta.get("AuthorName", ""),
            "webSite": meta.get("WebSite", ""),
            "sourceCode": meta.get("SourceCode", ""),
            "issueTracker": meta.get("IssueTracker", ""),
            "changelog": meta.get("Changelog", ""),
            "categories": meta.get("Categories", ["Tools"]),
            "suggestedVersionCode": suggested_vc,
            "added": timestamp - 86400000,
            "lastUpdated": timestamp
        })
        
    return {
        "repo": {
            "name": REPO_NAME,
            "description": REPO_DESCRIPTION,
            "icon": "icon.png",
            "address": REPO_BASE_URL,
            "timestamp": timestamp,
            "version": 20002,
            "fingerprint": fingerprint
        },
        "requests": {
            "install": [],
            "uninstall": []
        },
        "apps": apps_list,
        "packages": packages_dict
    }

def build_index_v2(apps_dict, packages_dict, timestamp):
    packages_v2 = {}
    for pkg, meta in apps_dict.items():
        icon_name = f"{pkg}.png"
        icon_path = os.path.join(REPO_DIR, 'icons', icon_name)
        icon_sha = get_file_sha256(icon_path) if os.path.exists(icon_path) else ""
        icon_size = os.path.getsize(icon_path) if os.path.exists(icon_path) else 0
        
        versions_v2 = {}
        for p in packages_dict.get(pkg, []):
            versions_v2[p['hash']] = {
                "added": p.get("added", timestamp),
                "file": {
                    "name": f"/{p['apkName']}",
                    "sha256": p['hash'],
                    "size": p['size']
                },
                "manifest": {
                    "versionName": p['versionName'],
                    "versionCode": p['versionCode'],
                    "minSdkVersion": p['minSdkVersion'],
                    "targetSdkVersion": p['targetSdkVersion'],
                    "signer": {
                        "sha256": [p['signer']]
                    }
                }
            }
            
        packages_v2[pkg] = {
            "metadata": {
                "name": {"en-US": meta.get("Name", pkg)},
                "summary": {"en-US": meta.get("Summary", "")},
                "description": {"en-US": meta.get("Description", "")},
                "categories": meta.get("Categories", ["Tools"]),
                "license": meta.get("License", "Unknown"),
                "webSite": meta.get("WebSite", ""),
                "sourceCode": meta.get("SourceCode", ""),
                "issueTracker": meta.get("IssueTracker", ""),
                "icon": {
                    "en-US": {
                        "name": f"/icons/{icon_name}",
                        "sha256": icon_sha,
                        "size": icon_size
                    }
                }
            },
            "versions": versions_v2
        }
        
    return {
        "repo": {
            "name": {"en-US": REPO_NAME},
            "description": {"en-US": REPO_DESCRIPTION},
            "icon": {
                "en-US": {
                    "name": "/icon.png",
                    "sha256": get_file_sha256(os.path.join(REPO_DIR, 'icon.png')) if os.path.exists(os.path.join(REPO_DIR, 'icon.png')) else "",
                    "size": os.path.getsize(os.path.join(REPO_DIR, 'icon.png')) if os.path.exists(os.path.join(REPO_DIR, 'icon.png')) else 0
                }
            },
            "address": REPO_BASE_URL,
            "timestamp": timestamp
        },
        "packages": packages_v2
    }

def build_index_xml(apps_dict, packages_dict, fingerprint, timestamp):
    root = ET.Element("fdroid")
    repo_el = ET.SubElement(root, "repo", {
        "icon": "icon.png",
        "name": REPO_NAME,
        "pubkey": fingerprint,
        "timestamp": str(timestamp),
        "url": REPO_BASE_URL,
        "version": "21"
    })
    desc_el = ET.SubElement(repo_el, "description")
    desc_el.text = REPO_DESCRIPTION
    
    date_str = time.strftime('%Y-%m-%d', time.gmtime(timestamp / 1000))
    
    for pkg, meta in apps_dict.items():
        pkgs = packages_dict.get(pkg, [])
        app_el = ET.SubElement(root, "application", {"id": pkg})
        
        ET.SubElement(app_el, "id").text = pkg
        ET.SubElement(app_el, "added").text = date_str
        ET.SubElement(app_el, "lastupdated").text = date_str
        ET.SubElement(app_el, "name").text = meta.get("Name", pkg)
        ET.SubElement(app_el, "summary").text = meta.get("Summary", "")
        ET.SubElement(app_el, "icon").text = f"{pkg}.png"
        ET.SubElement(app_el, "desc").text = meta.get("Description", "")
        ET.SubElement(app_el, "license").text = meta.get("License", "Unknown")
        cats = meta.get("Categories", ["Tools"])
        ET.SubElement(app_el, "category").text = cats[0] if cats else "Tools"
        ET.SubElement(app_el, "categories").text = ",".join(cats)
        ET.SubElement(app_el, "web").text = meta.get("WebSite", "")
        ET.SubElement(app_el, "source").text = meta.get("SourceCode", "")
        ET.SubElement(app_el, "tracker").text = meta.get("IssueTracker", "")
        
        if pkgs:
            latest = pkgs[0]
            ET.SubElement(app_el, "marketversion").text = latest['versionName']
            ET.SubElement(app_el, "marketvercode").text = str(latest['versionCode'])
            
            for p in pkgs:
                pkg_el = ET.SubElement(app_el, "package")
                ET.SubElement(pkg_el, "version").text = p['versionName']
                ET.SubElement(pkg_el, "versioncode").text = str(p['versionCode'])
                ET.SubElement(pkg_el, "size").text = str(p['size'])
                hash_el = ET.SubElement(pkg_el, "hash", {"type": "sha256"})
                hash_el.text = p['hash']
                ET.SubElement(pkg_el, "sig").text = p['signer']
                ET.SubElement(pkg_el, "apkname").text = p['apkName']
                ET.SubElement(pkg_el, "sdkver").text = str(p['minSdkVersion'])
                ET.SubElement(pkg_el, "targetsdkver").text = str(p['targetSdkVersion'])
                ET.SubElement(pkg_el, "added").text = date_str
                
    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return xml_bytes

def sign_jar(jar_path):
    cmd = [
        "jarsigner",
        "-keystore", KEYSTORE_PATH,
        "-storepass", KEYSTORE_PASS,
        "-keypass", KEYSTORE_PASS,
        jar_path,
        KEY_ALIAS
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"Warning: jarsigner failed for {jar_path}: {res.stderr}")
    else:
        print(f"Signed {os.path.basename(jar_path)} successfully")

def main():
    print("=== IOSonDroid F-Droid Repository Builder ===")
    timestamp = int(time.time() * 1000)
    fingerprint = get_repo_fingerprint()
    print(f"Repository Fingerprint: {fingerprint}")
    
    metadata = load_all_metadata()
    print(f"Loaded metadata for {len(metadata)} apps.")
    
    # Scan APKs in repo/
    apk_files = sorted(glob.glob(os.path.join(REPO_DIR, '*.apk')))
    print(f"Found {len(apk_files)} APK files in {REPO_DIR}.")
    
    packages_dict = {}
    for apk_path in apk_files:
        info = extract_apk_info(apk_path, metadata.keys())
        pkg = info['packageName']
        if pkg not in packages_dict:
            packages_dict[pkg] = []
        packages_dict[pkg].append(info)
        print(f"  Processed APK: {info['apkName']} -> {pkg} (v{info['versionName']} #{info['versionCode']})")
        
    for pkg in packages_dict:
        packages_dict[pkg].sort(key=lambda x: x['versionCode'], reverse=True)
        
    # Generate index-v1.json
    index_v1 = build_index_v1(metadata, packages_dict, fingerprint, timestamp)
    index_v1_path = os.path.join(REPO_DIR, 'index-v1.json')
    with open(index_v1_path, 'w', encoding='utf-8') as f:
        json.dump(index_v1, f, indent=2, ensure_ascii=False)
    print(f"Wrote {index_v1_path}")
    
    # Generate index-v2.json
    index_v2 = build_index_v2(metadata, packages_dict, timestamp)
    index_v2_path = os.path.join(REPO_DIR, 'index-v2.json')
    with open(index_v2_path, 'w', encoding='utf-8') as f:
        json.dump(index_v2, f, indent=2, ensure_ascii=False)
    print(f"Wrote {index_v2_path}")
    
    # Generate index.xml
    xml_data = build_index_xml(metadata, packages_dict, fingerprint, timestamp)
    index_xml_path = os.path.join(REPO_DIR, 'index.xml')
    with open(index_xml_path, 'wb') as f:
        f.write(xml_data)
    print(f"Wrote {index_xml_path}")
    
    # Pack & sign index.jar
    index_jar_path = os.path.join(REPO_DIR, 'index.jar')
    with zipfile.ZipFile(index_jar_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.write(index_xml_path, 'index.xml')
    sign_jar(index_jar_path)
    
    # Pack & sign index-v1.jar
    index_v1_jar_path = os.path.join(REPO_DIR, 'index-v1.jar')
    with zipfile.ZipFile(index_v1_jar_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.write(index_v1_path, 'index-v1.json')
    sign_jar(index_v1_jar_path)
    
    # Generate static web catalog.json for frontend
    os.makedirs(ASSETS_DIR, exist_ok=True)
    catalog = []
    for pkg, meta in metadata.items():
        pkgs = packages_dict.get(pkg, [])
        apk_info = pkgs[0] if pkgs else None
        
        default_version = VERSION_MAPPINGS.get(pkg, {}).get(list(VERSION_MAPPINGS.get(pkg, {}).keys())[0], "1.0.0") if VERSION_MAPPINGS.get(pkg) else "1.0.0"
        default_vc = list(VERSION_MAPPINGS.get(pkg, {}).keys())[0] if VERSION_MAPPINGS.get(pkg) else 1
        
        catalog.append({
            "packageName": pkg,
            "name": meta.get("Name", pkg),
            "summary": meta.get("Summary", ""),
            "description": meta.get("Description", ""),
            "icon": f"repo/icons/{pkg}.png",
            "categories": meta.get("Categories", ["Tools"]),
            "license": meta.get("License", "Unknown"),
            "authorName": meta.get("AuthorName", ""),
            "webSite": meta.get("WebSite", ""),
            "sourceCode": meta.get("SourceCode", ""),
            "issueTracker": meta.get("IssueTracker", ""),
            "hasApk": apk_info is not None,
            "apkName": apk_info['apkName'] if apk_info else None,
            "apkSize": apk_info['size'] if apk_info else None,
            "versionName": apk_info['versionName'] if apk_info else default_version,
            "versionCode": apk_info['versionCode'] if apk_info else default_vc,
            "sha256": apk_info['hash'] if apk_info else None
        })
        
    catalog_path = os.path.join(ASSETS_DIR, 'catalog.json')
    with open(catalog_path, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"Wrote frontend catalog: {catalog_path}")
    print("=== Build Complete! ===")

if __name__ == '__main__':
    main()
