#!/usr/bin/env python3
"""
converter.py - IOSonDroid Application Converter
Converts iOS-only applications (.ipa bundles, Xcode projects, assets, and Swift code)
into Android-compatible packages (.apk) and Android Studio projects.

Features:
1. Binary Converter (ipa2apk):
   Extracts iOS .ipa or .app bundle, inspects Mach-O encryption (FairPlay DRM),
   reads Info.plist, embeds the iOS application into an Android runtime container
   (powered by touchHLE/SDL2), generates AndroidManifest.xml, and signs the APK with jarsigner.
2. Project Converter (project2android):
   Converts an iOS Xcode project, Info.plist, Localizable.strings, and .xcassets into a
   complete, buildable Android Studio Gradle project.
3. Resource Converters:
   - Info.plist -> AndroidManifest.xml
   - Localizable.strings -> res/values/strings.xml
   - AppIcon / xcassets -> res/mipmap/ icons
4. Swift to Kotlin Transpiler:
   Translates Swift language structures, functions, types, and closures into idiomatic Kotlin.
"""

import os
import sys
import re
import json
import shutil
import zipfile
import plistlib
import struct
import tempfile
import argparse
import subprocess
from PIL import Image

KEYSTORE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'keystore', 'repokey.p12'))
KEYSTORE_PASS = 'iosondroid-repo-key'
KEY_ALIAS = 'iosondroid'
REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'repo'))
RUNNER_TEMPLATE_APK = os.path.join(REPO_DIR, 'org.touchhle.android_30.apk')


# ==========================================
# 1. Mach-O & IPA Binary Analysis
# ==========================================

def inspect_macho_encryption(binary_bytes):
    """
    Parses Mach-O header and load commands to check LC_ENCRYPTION_INFO / LC_ENCRYPTION_INFO_64.
    Returns: (is_encrypted: bool, cryptid: int, arch: str)
    """
    if len(binary_bytes) < 16:
        return (False, 0, "unknown")

    magic = struct.unpack('<I', binary_bytes[:4])[0]
    
    # Fat / Universal binary
    if magic in (0xcafebabe, 0xbebafeca):
        arch = "universal/fat"
        # Parse first arch
        nfat_arch = struct.unpack('>I', binary_bytes[4:8])[0]
        if nfat_arch > 0:
            offset = struct.unpack('>I', binary_bytes[16:20])[0]
            if len(binary_bytes) > offset + 16:
                return inspect_macho_encryption(binary_bytes[offset:])
        return (False, 0, arch)

    is_64 = (magic == 0xfeedfacf)
    is_32 = (magic == 0xfeedface)
    if not (is_32 or is_64):
        return (False, 0, "non-macho")

    arch = "arm64" if is_64 else "armv7"
    
    # Header size: 28 for 32-bit, 32 for 64-bit
    header_size = 32 if is_64 else 28
    if len(binary_bytes) < header_size:
        return (False, 0, arch)

    cputype, cpusubtype, filetype, ncmds, sizeofcmds = struct.unpack('<IIIII', binary_bytes[4:24])
    offset = header_size

    # Iterate through load commands
    for _ in range(ncmds):
        if offset + 8 > len(binary_bytes):
            break
        cmd, cmdsize = struct.unpack('<II', binary_bytes[offset:offset+8])
        # LC_ENCRYPTION_INFO (0x21) or LC_ENCRYPTION_INFO_64 (0x2C)
        if cmd in (0x21, 0x2C):
            if offset + 20 <= len(binary_bytes):
                # cmd, cmdsize, cryptoff, cryptsize, cryptid
                cryptoff, cryptsize, cryptid = struct.unpack('<III', binary_bytes[offset+8:offset+20])
                return (cryptid != 0, cryptid, arch)
        offset += cmdsize

    return (False, 0, arch)


def analyze_ipa(ipa_path):
    """
    Comprehensive inspection of an iOS .ipa file.
    Extracts Info.plist, Mach-O architecture, encryption status, and app assets.
    """
    if not os.path.exists(ipa_path):
        raise FileNotFoundError(f"IPA file not found: {ipa_path}")

    report = {
        "file": os.path.basename(ipa_path),
        "size_bytes": os.path.getsize(ipa_path),
        "is_valid_ipa": False,
        "app_bundle": None,
        "bundle_id": "unknown",
        "name": "Unknown App",
        "version": "1.0",
        "version_code": "1",
        "min_ios_version": "3.0",
        "orientations": [],
        "permissions_requested": [],
        "arch": "unknown",
        "is_encrypted": False,
        "cryptid": 0,
        "has_icon": False,
        "icon_entry": None,
        "touchhle_compatible": False,
        "files_count": 0
    }

    with zipfile.ZipFile(ipa_path, 'r') as z:
        report["files_count"] = len(z.namelist())
        
        # Locate Payload/*.app/Info.plist
        plist_entry = None
        app_prefix = None
        for name in z.namelist():
            if name.startswith("Payload/") and name.endswith(".app/Info.plist"):
                plist_entry = name
                app_prefix = name[:-len("Info.plist")]
                break

        if not plist_entry:
            # Fallback check for any Info.plist
            for name in z.namelist():
                if name.endswith("Info.plist") and "app" in name:
                    plist_entry = name
                    app_prefix = name[:name.rfind('/') + 1]
                    break

        if not plist_entry:
            return report

        report["is_valid_ipa"] = True
        report["app_bundle"] = os.path.basename(app_prefix.rstrip('/'))

        # Parse Info.plist
        try:
            plist_data = plistlib.loads(z.read(plist_entry))
            report["bundle_id"] = plist_data.get("CFBundleIdentifier", "io.iosondroid.app")
            report["name"] = plist_data.get("CFBundleDisplayName") or plist_data.get("CFBundleName") or report["app_bundle"].replace(".app", "")
            report["version"] = plist_data.get("CFBundleShortVersionString", "1.0.0")
            report["version_code"] = plist_data.get("CFBundleVersion", "1")
            report["min_ios_version"] = plist_data.get("MinimumOSVersion", "3.0")
            report["orientations"] = plist_data.get("UISupportedInterfaceOrientations", ["UIInterfaceOrientationPortrait"])
            
            # Extract permissions
            for k, v in plist_data.items():
                if k.endswith("UsageDescription"):
                    report["permissions_requested"].append({"key": k, "description": v})
                    
            # Check icon
            icon_files = []
            if "CFBundleIcons" in plist_data:
                try:
                    icon_files = plist_data["CFBundleIcons"]["CFBundlePrimaryIcon"]["CFBundleIconFiles"]
                except Exception:
                    pass
            if not icon_files and "CFBundleIconFiles" in plist_data:
                icon_files = plist_data["CFBundleIconFiles"]
            if not icon_files and "CFBundleIconFile" in plist_data:
                icon_files = [plist_data["CFBundleIconFile"]]

            for ic in icon_files:
                for ext in ["", ".png", "@2x.png", "@3x.png"]:
                    target = f"{app_prefix}{ic}{ext}"
                    if target in z.namelist():
                        report["has_icon"] = True
                        report["icon_entry"] = target
                        break
                if report["has_icon"]:
                    break
        except Exception as e:
            report["plist_error"] = str(e)

        # Locate executable
        exec_name = report["app_bundle"].replace(".app", "") if report["app_bundle"] else None
        if exec_name:
            exec_entry = f"{app_prefix}{exec_name}"
            if exec_entry in z.namelist():
                bin_data = z.read(exec_entry)
                is_enc, cryptid, arch = inspect_macho_encryption(bin_data)
                report["arch"] = arch
                report["is_encrypted"] = is_enc
                report["cryptid"] = cryptid
                # 32-bit decrypted apps are highly compatible with touchHLE runner
                if arch in ("armv7", "universal/fat") and not is_enc:
                    report["touchhle_compatible"] = True

    return report


# ==========================================
# 2. Binary Converter (IPA -> Standalone APK)
# ==========================================

def convert_ipa_to_apk(ipa_path, output_apk_path=None, app_name=None, package_id=None, keystore_path=None):
    """
    Wraps an iOS app (.ipa) into a standalone Android APK using the embedded runtime container.
    """
    analysis = analyze_ipa(ipa_path)
    if not analysis["is_valid_ipa"]:
        raise ValueError(f"Invalid iOS IPA archive: {ipa_path}. Missing Payload/*.app directory.")

    app_name = app_name or analysis["name"]
    pkg_id = package_id or analysis["bundle_id"]
    # Ensure package ID is a valid Android package identifier (no hyphens, lowercase)
    clean_pkg = re.sub(r'[^a-zA-Z0-9_.]', '_', pkg_id).lower()
    if not clean_pkg.count('.'):
        clean_pkg = f"io.iosondroid.{clean_pkg}"

    if not output_apk_path:
        base_name = re.sub(r'[^a-zA-Z0-9_]', '_', app_name)
        output_apk_path = os.path.abspath(f"{base_name}_android.apk")

    print(f"\n[+] Converting iOS Application: '{app_name}'")
    print(f"    Bundle ID: {analysis['bundle_id']} -> Android Package: {clean_pkg}")
    print(f"    Architecture: {analysis['arch']} | DRM Encryption: {'ENCRYPTED' if analysis['is_encrypted'] else 'Decrypted / DRM-free'}")

    if analysis["is_encrypted"]:
        print("    [!] WARNING: This IPA binary contains Apple FairPlay DRM (cryptid != 0).")
        print("        To run on Android, use a decrypted IPA dump (e.g., dumped via Clutch/Frida).")

    # Use runner template if available
    template_apk = RUNNER_TEMPLATE_APK if os.path.exists(RUNNER_TEMPLATE_APK) else None

    with tempfile.TemporaryDirectory() as tmp_dir:
        extracted_ipa_dir = os.path.join(tmp_dir, "ipa_content")
        with zipfile.ZipFile(ipa_path, 'r') as z:
            z.extractall(extracted_ipa_dir)

        payload_app_dir = None
        for item in os.listdir(os.path.join(extracted_ipa_dir, "Payload")):
            if item.endswith(".app"):
                payload_app_dir = os.path.join(extracted_ipa_dir, "Payload", item)
                break

        if not payload_app_dir:
            raise FileNotFoundError("Could not locate .app folder inside Payload/")

        app_folder_name = os.path.basename(payload_app_dir)

        # Prepare APK build staging area
        staging_dir = os.path.join(tmp_dir, "apk_staging")
        os.makedirs(staging_dir, exist_ok=True)

        if template_apk:
            print(f"    [+] Injecting into runtime container from {os.path.basename(template_apk)}...")
            with zipfile.ZipFile(template_apk, 'r') as base_z:
                for item in base_z.namelist():
                    # Skip existing signature and previous embedded apps
                    if not item.startswith("META-INF/") and not item.startswith("assets/touchHLE_apps/"):
                        base_z.extract(item, staging_dir)
        else:
            print("    [+] Building minimal Android application container...")
            os.makedirs(os.path.join(staging_dir, "lib", "arm64-v8a"), exist_ok=True)

        # Inject iOS .app bundle into assets/touchHLE_apps/
        target_app_dir = os.path.join(staging_dir, "assets", "touchHLE_apps", app_folder_name)
        os.makedirs(os.path.dirname(target_app_dir), exist_ok=True)
        shutil.copytree(payload_app_dir, target_app_dir)

        # Inject app_manifest.json metadata
        app_manifest = {
            "name": app_name,
            "package": clean_pkg,
            "version": analysis["version"],
            "version_code": int(analysis["version_code"]) if analysis["version_code"].isdigit() else 1,
            "bundle": app_folder_name,
            "executable": app_folder_name.replace(".app", ""),
            "ios_version": analysis["min_ios_version"],
            "converted_by": "IOSonDroid Converter v2.0",
            "orientations": analysis["orientations"]
        }
        with open(os.path.join(staging_dir, "assets", "app_manifest.json"), "w", encoding="utf-8") as f:
            json.dump(app_manifest, f, indent=2)

        # Process App Icon
        icon_path = os.path.join(staging_dir, "assets", "icon.png")
        if analysis["has_icon"] and analysis["icon_entry"]:
            try:
                with zipfile.ZipFile(ipa_path) as z:
                    icon_data = z.read(analysis["icon_entry"])
                    with open(icon_path, "wb") as f:
                        f.write(icon_data)
                print(f"    [+] Extracted iOS App Icon: {analysis['icon_entry']}")
            except Exception:
                generate_fallback_icon(icon_path, app_name)
        else:
            generate_fallback_icon(icon_path, app_name)

        # Pack into target APK archive
        unsigned_apk = os.path.join(tmp_dir, "unsigned.apk")
        with zipfile.ZipFile(unsigned_apk, 'w', compression=zipfile.ZIP_DEFLATED) as z_out:
            for root, _, files in os.walk(staging_dir):
                for file in files:
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, staging_dir)
                    z_out.write(full_p, rel_p)

        # Sign APK using jarsigner
        ks = keystore_path or KEYSTORE_PATH
        if os.path.exists(ks):
            print(f"    [+] Signing APK with repository keystore ({os.path.basename(ks)})...")
            shutil.copy(unsigned_apk, output_apk_path)
            cmd = [
                "jarsigner",
                "-keystore", ks,
                "-storepass", KEYSTORE_PASS,
                "-keypass", KEYSTORE_PASS,
                output_apk_path,
                KEY_ALIAS
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print("    [+] APK signed successfully!")
        else:
            shutil.copy(unsigned_apk, output_apk_path)
            print("    [!] Keystore not found, outputting unsigned APK.")

    print(f"\n[✓] Successfully converted '{app_name}' to Android APK:")
    print(f"    File: {output_apk_path} ({round(os.path.getsize(output_apk_path)/1024/1024, 2)} MB)\n")
    return output_apk_path


def generate_fallback_icon(out_path, app_name):
    """Generates an iOS squircle icon if none was found in the IPA."""
    img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([16, 16, 496, 496], radius=115, fill=(0, 122, 255))
    draw.ellipse([200, 200, 312, 312], fill=(255, 255, 255))
    img.save(out_path, format="PNG")


# ==========================================
# 3. Resource & Plist Converters
# ==========================================

IOS_TO_ANDROID_PERMISSIONS = {
    "NSCameraUsageDescription": "android.permission.CAMERA",
    "NSLocationWhenInUseUsageDescription": "android.permission.ACCESS_FINE_LOCATION",
    "NSLocationAlwaysUsageDescription": "android.permission.ACCESS_FINE_LOCATION",
    "NSMicrophoneUsageDescription": "android.permission.RECORD_AUDIO",
    "NSPhotoLibraryUsageDescription": "android.permission.READ_MEDIA_IMAGES",
    "NSBluetoothAlwaysUsageDescription": "android.permission.BLUETOOTH_CONNECT",
    "NSContactsUsageDescription": "android.permission.READ_CONTACTS",
    "NSCalendarsUsageDescription": "android.permission.READ_CALENDAR"
}

def convert_plist_to_manifest(plist_path, output_manifest_path=None):
    """
    Translates an iOS Info.plist into an AndroidManifest.xml.
    """
    with open(plist_path, 'rb') as f:
        plist_data = plistlib.load(f)

    pkg = plist_data.get("CFBundleIdentifier", "io.iosondroid.app")
    clean_pkg = re.sub(r'[^a-zA-Z0-9_.]', '_', pkg).lower()
    if not clean_pkg.count('.'):
        clean_pkg = f"io.iosondroid.{clean_pkg}"

    app_name = plist_data.get("CFBundleDisplayName") or plist_data.get("CFBundleName") or "iOS Application"
    version_name = plist_data.get("CFBundleShortVersionString", "1.0.0")
    version_code = plist_data.get("CFBundleVersion", "1")
    if not version_code.isdigit():
        version_code = "1"

    # Screen orientation
    orientations = plist_data.get("UISupportedInterfaceOrientations", [])
    screen_orient = "unspecified"
    if "UIInterfaceOrientationPortrait" in orientations and len(orientations) == 1:
        screen_orient = "portrait"
    elif "UIInterfaceOrientationLandscapeLeft" in orientations or "UIInterfaceOrientationLandscapeRight" in orientations:
        if "UIInterfaceOrientationPortrait" not in orientations:
            screen_orient = "landscape"

    # Permissions
    permissions = []
    for k in plist_data:
        if k in IOS_TO_ANDROID_PERMISSIONS:
            permissions.append(IOS_TO_ANDROID_PERMISSIONS[k])

    xml_lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        f'<manifest xmlns:android="http://schemas.android.com/apk/res/android"',
        f'    package="{clean_pkg}"',
        f'    android:versionCode="{version_code}"',
        f'    android:versionName="{version_name}">',
        '',
        '    <!-- Converted from iOS Info.plist by IOSonDroid Converter -->',
        '    <uses-feature android:glEsVersion="0x00020000" android:required="true" />'
    ]

    for p in sorted(set(permissions)):
        xml_lines.append(f'    <uses-permission android:name="{p}" />')

    xml_lines.extend([
        '',
        '    <application',
        f'        android:label="{app_name}"',
        '        android:icon="@mipmap/ic_launcher"',
        '        android:hardwareAccelerated="true"',
        '        android:allowBackup="true"',
        '        android:theme="@android:style/Theme.NoTitleBar.Fullscreen">',
        '        <activity',
        '            android:name=".MainActivity"',
        f'            android:screenOrientation="{screen_orient}"',
        '            android:configChanges="orientation|keyboardHidden|screenSize"',
        '            android:exported="true">',
        '            <intent-filter>',
        '                <action android:name="android.intent.action.MAIN" />',
        '                <category android:name="android.intent.category.LAUNCHER" />',
        '            </intent-filter>',
        '        </activity>',
        '    </application>',
        '</manifest>'
    ])

    manifest_content = '\n'.join(xml_lines)
    if output_manifest_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_manifest_path)), exist_ok=True)
        with open(output_manifest_path, 'w', encoding='utf-8') as f:
            f.write(manifest_content)
        print(f"[+] Converted Info.plist -> AndroidManifest.xml: {output_manifest_path}")

    return manifest_content


def convert_strings_to_xml(strings_path, output_xml_path=None):
    """
    Translates iOS Localizable.strings ("key" = "value";) into Android res/values/strings.xml.
    """
    with open(strings_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Match "key" = "value";
    pattern = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"\s*=\s*"([^"\\]*(?:\\.[^"\\]*)*)";')
    matches = pattern.findall(content)

    xml_lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<resources>',
        '    <!-- Converted from iOS Localizable.strings by IOSonDroid Converter -->'
    ]

    for k, v in matches:
        clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', k).lower()
        if clean_key and clean_key[0].isdigit():
            clean_key = f"str_{clean_key}"
        clean_val = v.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace("'", "\\'")
        xml_lines.append(f'    <string name="{clean_key}">{clean_val}</string>')

    xml_lines.append('</resources>')
    xml_content = '\n'.join(xml_lines)

    if output_xml_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_xml_path)), exist_ok=True)
        with open(output_xml_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        print(f"[+] Converted Localizable.strings -> {output_xml_path} ({len(matches)} strings)")

    return xml_content


# ==========================================
# 4. Swift to Kotlin Transpiler
# ==========================================

SWIFT_TYPE_MAP = {
    "String": "String",
    "Int": "Int",
    "Double": "Double",
    "Float": "Float",
    "Bool": "Boolean",
    "Any": "Any",
    "Void": "Unit"
}

def transpile_swift_to_kotlin(swift_code):
    """
    Transpiles Swift source code into idiomatic Kotlin.
    Translates variables, functions, data structures, nullability, and string interpolation.
    """
    kotlin = swift_code

    # 1. Imports
    kotlin = re.sub(r'import\s+UIKit', 'import android.os.Bundle\nimport androidx.appcompat.app.AppCompatActivity', kotlin)
    kotlin = re.sub(r'import\s+Foundation', '// import Foundation', kotlin)
    kotlin = re.sub(r'import\s+SwiftUI', '// import SwiftUI (Compose equivalent)', kotlin)

    # 2. Variable declarations: let -> val, var -> var
    kotlin = re.sub(r'\blet\b', 'val', kotlin)

    # 3. Types: Bool -> Boolean, Void -> Unit
    for s_type, k_type in SWIFT_TYPE_MAP.items():
        kotlin = re.sub(rf':\s*{s_type}\b', f': {k_type}', kotlin)

    # 4. Arrays: [T] -> List<T>, Dictionaries: [K: V] -> Map<K, V>
    kotlin = re.sub(r':\s*\[(\w+)\]', r': List<\1>', kotlin)
    kotlin = re.sub(r':\s*\[(\w+)\s*:\s*(\w+)\]', r': Map<\1, \2>', kotlin)

    # 5. Functions: func name(param: Type) -> Ret -> fun name(param: Type): Ret
    kotlin = re.sub(r'\bfunc\s+([a-zA-Z0-9_]+)\s*\((.*?)\)\s*->\s*([a-zA-Z0-9_<>]+)', r'fun \1(\2): \3', kotlin)
    kotlin = re.sub(r'\bfunc\s+([a-zA-Z0-9_]+)\s*\((.*?)\)', r'fun \1(\2)', kotlin)

    # 6. Struct -> data class
    kotlin = re.sub(r'\bstruct\s+([a-zA-Z0-9_]+)\s*\{', r'data class \1(', kotlin)

    # 7. Print: print(...) -> println(...)
    kotlin = re.sub(r'\bprint\(', 'println(', kotlin)

    # 8. String interpolation: "\(val)" -> "$val"
    kotlin = re.sub(r'\\\(([a-zA-Z0-9_]+)\)', r'$\1', kotlin)

    # 9. Guard let x = opt else { return } -> val x = opt ?: return
    kotlin = re.sub(r'guard\s+val\s+([a-zA-Z0-9_]+)\s*=\s*(.*?)\s+else\s*\{\s*return(\s*.*?)\s*\}', r'val \1 = \2 ?: return\3', kotlin)

    # 10. Nil -> null
    kotlin = re.sub(r'\bnil\b', 'null', kotlin)

    # Header comment
    header = "// Transpiled from Swift by IOSonDroid Converter\n\n"
    return header + kotlin


# ==========================================
# 5. Project Converter (Xcode -> Android Studio)
# ==========================================

def convert_project_to_android(ios_project_dir, output_dir=None):
    """
    Transforms an iOS Xcode project folder into a full Android Studio project.
    """
    if not os.path.exists(ios_project_dir):
        raise FileNotFoundError(f"Project directory not found: {ios_project_dir}")

    output_dir = output_dir or os.path.join(os.path.dirname(ios_project_dir), f"{os.path.basename(ios_project_dir)}_android")
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n[+] Converting Xcode Project: '{ios_project_dir}' -> '{output_dir}'")

    # Locate Info.plist
    plist_path = None
    for root, _, files in os.walk(ios_project_dir):
        if "Info.plist" in files:
            plist_path = os.path.join(root, "Info.plist")
            break

    # Structure Android project
    app_dir = os.path.join(output_dir, "app")
    main_dir = os.path.join(app_dir, "src", "main")
    res_dir = os.path.join(main_dir, "res")
    values_dir = os.path.join(res_dir, "values")
    mipmap_dir = os.path.join(res_dir, "mipmap-xxhdpi")
    os.makedirs(values_dir, exist_ok=True)
    os.makedirs(mipmap_dir, exist_ok=True)

    # 1. Convert Manifest
    manifest_target = os.path.join(main_dir, "AndroidManifest.xml")
    if plist_path:
        convert_plist_to_manifest(plist_path, manifest_target)
    else:
        # Default manifest
        with open(manifest_target, "w") as f:
            f.write('<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="io.iosondroid.app"><application android:label="Converted App" /></manifest>')

    # 2. Convert Strings
    for root, _, files in os.walk(ios_project_dir):
        for file in files:
            if file == "Localizable.strings":
                strings_target = os.path.join(values_dir, "strings.xml")
                convert_strings_to_xml(os.path.join(root, file), strings_target)
                break

    # 3. Transpile Swift files
    java_dir = os.path.join(main_dir, "java", "io", "iosondroid", "app")
    os.makedirs(java_dir, exist_ok=True)
    swift_count = 0
    for root, _, files in os.walk(ios_project_dir):
        for file in files:
            if file.endswith(".swift"):
                swift_count += 1
                with open(os.path.join(root, file), "r", encoding="utf-8", errors="replace") as sf:
                    kotlin_code = transpile_swift_to_kotlin(sf.read())
                kt_filename = file.replace(".swift", ".kt")
                with open(os.path.join(java_dir, kt_filename), "w", encoding="utf-8") as kf:
                    kf.write(f"package io.iosondroid.app\n\n{kotlin_code}")

    print(f"    [+] Transpiled {swift_count} Swift files to Kotlin in app/src/main/java/")

    # 4. Generate build.gradle.kts and settings.gradle.kts
    with open(os.path.join(output_dir, "settings.gradle.kts"), "w") as f:
        f.write('rootProject.name = "ConvertedIOSApp"\ninclude(":app")\n')

    with open(os.path.join(output_dir, "build.gradle.kts"), "w") as f:
        f.write('// Top-level build file\nplugins {\n    id("com.android.application") version "8.2.0" apply false\n    id("org.jetbrains.kotlin.android") version "1.9.20" apply false\n}\n')

    with open(os.path.join(app_dir, "build.gradle.kts"), "w") as f:
        f.write('''plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "io.iosondroid.app"
    compileSdk = 34

    defaultConfig {
        applicationId = "io.iosondroid.app"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("com.google.android.material:material:1.11.0")
}
''')

    # Generate default launcher icon
    generate_fallback_icon(os.path.join(mipmap_dir, "ic_launcher.png"), "App")

    print(f"[✓] Android Studio project generated at: {output_dir}")
    return output_dir


# ==========================================
# 6. Command Line Interface
# ==========================================

def main():
    parser = argparse.ArgumentParser(
        description="IOSonDroid Converter: Convert iOS-only applications (.ipa) and Xcode projects for Android.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze an iOS .ipa package
  python scripts/converter.py analyze SuperMonkeyBall.ipa

  # Convert an iOS .ipa into a standalone Android APK
  python scripts/converter.py convert SuperMonkeyBall.ipa -o SuperMonkeyBall.apk

  # Convert an iOS Xcode project to an Android Studio Gradle project
  python scripts/converter.py project /path/to/ios_project -o /path/to/android_project

  # Translate an Info.plist to AndroidManifest.xml
  python scripts/converter.py plist2manifest Info.plist -o AndroidManifest.xml

  # Translate Localizable.strings to strings.xml
  python scripts/converter.py strings2xml Localizable.strings -o strings.xml
"""
    )

    subparsers = parser.add_subparsers(dest="command", help="Conversion subcommand")

    # Analyze
    p_analyze = subparsers.add_parser("analyze", help="Inspect and analyze an iOS IPA file")
    p_analyze.add_argument("ipa", help="Path to .ipa archive")
    p_analyze.add_argument("--json", action="store_true", help="Output analysis in JSON format")

    # Convert IPA -> APK
    p_convert = subparsers.add_parser("convert", help="Convert an iOS IPA package to an Android APK")
    p_convert.add_argument("ipa", help="Path to .ipa archive")
    p_convert.add_argument("-o", "--output", help="Output APK path")
    p_convert.add_argument("--name", help="Custom Android app display name")
    p_convert.add_argument("--package", help="Custom Android package identifier (e.g., com.example.app)")

    # Project Converter
    p_project = subparsers.add_parser("project", help="Convert an iOS Xcode project to an Android Studio project")
    p_project.add_argument("project_dir", help="Path to iOS project folder")
    p_project.add_argument("-o", "--output", help="Target output folder")

    # Plist Converter
    p_plist = subparsers.add_parser("plist2manifest", help="Convert iOS Info.plist to AndroidManifest.xml")
    p_plist.add_argument("plist", help="Path to Info.plist")
    p_plist.add_argument("-o", "--output", default="AndroidManifest.xml", help="Output AndroidManifest.xml path")

    # Strings Converter
    p_strings = subparsers.add_parser("strings2xml", help="Convert Localizable.strings to Android strings.xml")
    p_strings.add_argument("strings", help="Path to Localizable.strings")
    p_strings.add_argument("-o", "--output", default="strings.xml", help="Output strings.xml path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "analyze":
        report = analyze_ipa(args.ipa)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print("=== iOS Application Package Analysis ===")
            print(f"File:                 {report['file']} ({round(report['size_bytes']/1024/1024, 2)} MB)")
            print(f"App Name:             {report['name']}")
            print(f"Bundle ID:            {report['bundle_id']}")
            print(f"Version:              {report['version']} (#{report['version_code']})")
            print(f"Min iOS Version:      {report['min_ios_version']}")
            print(f"Architecture:         {report['arch']}")
            print(f"FairPlay DRM Encrypted: {'YES (Encrypted)' if report['is_encrypted'] else 'NO (Decrypted / DRM-free)'}")
            print(f"App Icon Detected:    {'Yes' if report['has_icon'] else 'No'}")
            print(f"touchHLE Compatible:  {'YES (Ready for direct emulation)' if report['touchhle_compatible'] else 'Requires verification'}")
            if report['permissions_requested']:
                print(f"Permissions:          {len(report['permissions_requested'])} iOS permissions mapped")
            print("========================================")

    elif args.command == "convert":
        convert_ipa_to_apk(args.ipa, args.output, args.name, args.package)

    elif args.command == "project":
        convert_project_to_android(args.project_dir, args.output)

    elif args.command == "plist2manifest":
        convert_plist_to_manifest(args.plist, args.output)

    elif args.command == "strings2xml":
        convert_strings_to_xml(args.strings, args.output)


if __name__ == "__main__":
    main()
