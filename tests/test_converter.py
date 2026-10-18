#!/usr/bin/env python3
"""
test_converter.py - Comprehensive Unit & Integration Tests for IOSonDroid Converter.
"""

import os
import sys
import unittest
import tempfile
import plistlib
import zipfile
import struct
import json
import subprocess
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))
import converter

class TestConverter(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_mock_ipa(self, app_name="SuperMonkeyBall", bundle_id="com.sega.supermonkeyball", is_encrypted=False):
        ipa_path = os.path.join(self.test_dir, f"{app_name}.ipa")
        plist_data = {
            "CFBundleDisplayName": "Super Monkey Ball",
            "CFBundleName": app_name,
            "CFBundleIdentifier": bundle_id,
            "CFBundleShortVersionString": "1.2.0",
            "CFBundleVersion": "42",
            "MinimumOSVersion": "3.0",
            "UISupportedInterfaceOrientations": ["UIInterfaceOrientationLandscapeLeft"],
            "NSCameraUsageDescription": "Used for scanning codes",
            "CFBundleIcons": {
                "CFBundlePrimaryIcon": {
                    "CFBundleIconFiles": ["AppIcon"]
                }
            }
        }

        # Create mock Mach-O binary
        # Header (28 bytes for 32-bit Mach-O)
        magic = 0xfeedface
        cputype = 12 # ARM
        cpusubtype = 9 # ARMv7
        filetype = 2 # MH_EXECUTE
        ncmds = 1
        sizeofcmds = 20
        flags = 0x00200085
        header = struct.pack('<IIIIIII', magic, cputype, cpusubtype, filetype, ncmds, sizeofcmds, flags)
        
        # Load command LC_ENCRYPTION_INFO (cmd=0x21, cmdsize=20, cryptoff=4096, cryptsize=8192, cryptid=1 if encrypted else 0)
        cryptid = 1 if is_encrypted else 0
        cmd = struct.pack('<IIIII', 0x21, 20, 4096, 8192, cryptid)
        macho_bytes = header + cmd + b'\x00' * 100

        # Create mock icon
        icon_img = Image.new("RGBA", (128, 128), (255, 128, 0))
        icon_bytes = tempfile.NamedTemporaryFile(suffix=".png")
        icon_img.save(icon_bytes.name)

        with zipfile.ZipFile(ipa_path, 'w') as z:
            z.writestr(f"Payload/{app_name}.app/Info.plist", plistlib.dumps(plist_data))
            z.writestr(f"Payload/{app_name}.app/{app_name}", macho_bytes)
            z.write(icon_bytes.name, f"Payload/{app_name}.app/AppIcon.png")

        return ipa_path

    def test_analyze_ipa(self):
        ipa_path = self.create_mock_ipa(is_encrypted=False)
        report = converter.analyze_ipa(ipa_path)

        self.assertTrue(report["is_valid_ipa"])
        self.assertEqual(report["name"], "Super Monkey Ball")
        self.assertEqual(report["bundle_id"], "com.sega.supermonkeyball")
        self.assertEqual(report["version"], "1.2.0")
        self.assertEqual(report["arch"], "armv7")
        self.assertFalse(report["is_encrypted"])
        self.assertTrue(report["has_icon"])
        self.assertTrue(report["touchhle_compatible"])

    def test_analyze_encrypted_ipa(self):
        ipa_path = self.create_mock_ipa(is_encrypted=True)
        report = converter.analyze_ipa(ipa_path)

        self.assertTrue(report["is_valid_ipa"])
        self.assertTrue(report["is_encrypted"])
        self.assertEqual(report["cryptid"], 1)

    def test_convert_ipa_to_apk(self):
        ipa_path = self.create_mock_ipa()
        out_apk = os.path.join(self.test_dir, "test_output.apk")

        apk_result = converter.convert_ipa_to_apk(ipa_path, output_apk_path=out_apk)
        self.assertTrue(os.path.exists(apk_result))
        self.assertGreater(os.path.getsize(apk_result), 0)

        # Inspect resulting APK contents
        with zipfile.ZipFile(apk_result, 'r') as z:
            namelist = z.namelist()
            self.assertIn("assets/app_manifest.json", namelist)
            self.assertIn("assets/touchHLE_apps/SuperMonkeyBall.app/Info.plist", namelist)
            self.assertIn("assets/touchHLE_apps/SuperMonkeyBall.app/SuperMonkeyBall", namelist)
            
            # Check manifest data
            manifest_data = json.loads(z.read("assets/app_manifest.json").decode('utf-8'))
            self.assertEqual(manifest_data["name"], "Super Monkey Ball")
            self.assertEqual(manifest_data["package"], "com.sega.supermonkeyball")

        # Verify signature
        res = subprocess.run(["jarsigner", "-verify", apk_result], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0, f"jarsigner verification failed: {res.stderr}")
        self.assertIn("jar verified", res.stdout)

    def test_plist_to_manifest(self):
        plist_path = os.path.join(self.test_dir, "Info.plist")
        manifest_path = os.path.join(self.test_dir, "AndroidManifest.xml")
        plist_data = {
            "CFBundleDisplayName": "FlightTracker iOS",
            "CFBundleIdentifier": "com.example.flighttracker",
            "CFBundleShortVersionString": "2.4.0",
            "CFBundleVersion": "100",
            "UISupportedInterfaceOrientations": ["UIInterfaceOrientationPortrait"],
            "NSCameraUsageDescription": "Camera for AR flight view",
            "NSLocationWhenInUseUsageDescription": "Location for airport distance"
        }
        with open(plist_path, "wb") as f:
            plistlib.dump(plist_data, f)

        converter.convert_plist_to_manifest(plist_path, manifest_path)
        self.assertTrue(os.path.exists(manifest_path))

        with open(manifest_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('package="com.example.flighttracker"', content)
        self.assertIn('android:versionName="2.4.0"', content)
        self.assertIn('android:screenOrientation="portrait"', content)
        self.assertIn('android.permission.CAMERA', content)
        self.assertIn('android.permission.ACCESS_FINE_LOCATION', content)

    def test_strings_to_xml(self):
        strings_path = os.path.join(self.test_dir, "Localizable.strings")
        xml_path = os.path.join(self.test_dir, "strings.xml")
        
        strings_content = '''
        /* Welcome header */
        "welcome_title" = "Welcome to iOS on Android";
        "action_start" = "Start Flight & Play";
        "error_network" = "Could not connect to Apple server";
        '''
        with open(strings_path, "w", encoding="utf-8") as f:
            f.write(strings_content)

        converter.convert_strings_to_xml(strings_path, xml_path)
        self.assertTrue(os.path.exists(xml_path))

        with open(xml_path, "r", encoding="utf-8") as f:
            xml_text = f.read()

        self.assertIn('<string name="welcome_title">Welcome to iOS on Android</string>', xml_text)
        self.assertIn('<string name="action_start">Start Flight &amp; Play</string>', xml_text)
        self.assertIn('<string name="error_network">Could not connect to Apple server</string>', xml_text)

    def test_swift_to_kotlin(self):
        swift_sample = r'''
import UIKit

struct Flight {
    let id: String
    var altitude: Int
    let isLanding: Bool
}

func calculateSpeed(distance: Double, time: Double) -> Double {
    let speed = distance / time
    print("Calculated speed: \(speed)")
    return speed
}
'''
        kt = converter.transpile_swift_to_kotlin(swift_sample)
        self.assertIn('val id: String', kt)
        self.assertIn('var altitude: Int', kt)
        self.assertIn('val isLanding: Boolean', kt)
        self.assertIn('fun calculateSpeed(distance: Double, time: Double): Double', kt)
        self.assertIn('println("Calculated speed: $speed")', kt)

    def test_project_converter(self):
        proj_dir = os.path.join(self.test_dir, "MockXcodeProject")
        os.makedirs(proj_dir, exist_ok=True)
        
        plist_data = {"CFBundleDisplayName": "Mock App", "CFBundleIdentifier": "com.test.mock"}
        with open(os.path.join(proj_dir, "Info.plist"), "wb") as f:
            plistlib.dump(plist_data, f)

        with open(os.path.join(proj_dir, "Main.swift"), "w") as f:
            f.write("func hello() { print(\"Hello world\") }")

        out_android = os.path.join(self.test_dir, "AndroidOutput")
        converter.convert_project_to_android(proj_dir, out_android)

        self.assertTrue(os.path.exists(os.path.join(out_android, "build.gradle.kts")))
        self.assertTrue(os.path.exists(os.path.join(out_android, "app", "build.gradle.kts")))
        self.assertTrue(os.path.exists(os.path.join(out_android, "app", "src", "main", "AndroidManifest.xml")))
        self.assertTrue(os.path.exists(os.path.join(out_android, "app", "src", "main", "java", "io", "iosondroid", "app", "Main.kt")))

if __name__ == '__main__':
    unittest.main()
