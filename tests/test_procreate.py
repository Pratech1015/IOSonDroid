#!/usr/bin/env python3
"""
test_procreate.py - Comprehensive Unit & Integration Tests for Procreate Conversion
Tests analysis, DRM detection, Info.plist translation, Swift brush engine transpilation,
and Xcode-to-Android project generation specifically for Procreate (si.savage.procreate).
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

PROCREATE_BUNDLE_ID = "si.savage.procreate"
PROCREATE_APP_NAME = "Procreate"
PROCREATE_VERSION = "5.3.5"
PROCREATE_BUILD = "39012"

class TestProcreateConverter(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.bin_ios2droid = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bin', 'ios2droid'))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_mock_procreate_ipa(self, is_encrypted=True):
        """Creates an authentic mock Procreate .ipa package with FairPlay DRM & Info.plist."""
        ipa_path = os.path.join(self.test_dir, "Procreate.ipa")
        
        plist_data = {
            "CFBundleDisplayName": PROCREATE_APP_NAME,
            "CFBundleName": PROCREATE_APP_NAME,
            "CFBundleIdentifier": PROCREATE_BUNDLE_ID,
            "CFBundleShortVersionString": PROCREATE_VERSION,
            "CFBundleVersion": PROCREATE_BUILD,
            "MinimumOSVersion": "15.4",
            "UISupportedInterfaceOrientations": [
                "UIInterfaceOrientationLandscapeLeft",
                "UIInterfaceOrientationLandscapeRight",
                "UIInterfaceOrientationPortrait",
                "UIInterfaceOrientationPortraitUpsideDown"
            ],
            "NSPhotoLibraryUsageDescription": "Procreate needs access to your photos to import canvases and export artwork.",
            "NSPhotoLibraryAddUsageDescription": "Procreate needs access to save artworks and time-lapses to your Photos.",
            "NSBluetoothAlwaysUsageDescription": "Procreate connects to supported pressure-sensitive styluses.",
            "NSBluetoothPeripheralUsageDescription": "Procreate pairs with smart Bluetooth styluses.",
            "NSCameraUsageDescription": "Procreate uses the camera for Face Paint and AR canvas projection.",
            "NSMicrophoneUsageDescription": "Procreate records audio for time-lapse video replay commentary.",
            "UIFileSharingEnabled": True,
            "LSSupportsOpeningDocumentsInPlace": True,
            "CFBundleIcons": {
                "CFBundlePrimaryIcon": {
                    "CFBundleIconFiles": ["AppIconProcreate"]
                }
            }
        }

        # Mach-O ARM64 header (magic = 0xfeedfacf, 8 fields / 32 bytes)
        magic = 0xfeedfacf
        cputype = 0x0100000C  # CPU_TYPE_ARM64
        cpusubtype = 0         # CPU_SUBTYPE_ARM64_ALL
        filetype = 2           # MH_EXECUTE
        ncmds = 1
        sizeofcmds = 20
        flags = 0x00200085
        reserved = 0
        header = struct.pack('<IIIIIIII', magic, cputype, cpusubtype, filetype, ncmds, sizeofcmds, flags, reserved)

        # LC_ENCRYPTION_INFO_64 (cmd=0x2C, cmdsize=20, cryptoff=16384, cryptsize=65536, cryptid=1 if encrypted else 0)
        cryptid = 1 if is_encrypted else 0
        cmd = struct.pack('<IIIII', 0x2C, 20, 16384, 65536, cryptid)
        macho_bytes = header + cmd + b'\x00' * 256

        # Generate Procreate-style brush icon
        icon_img = Image.new("RGBA", (512, 512), (20, 20, 24))
        # Draw brush colored gradient
        for y in range(512):
            for x in range(512):
                if 120 < x < 390 and 120 < y < 390:
                    icon_img.putpixel((x, y), (255, 45, 85, 255))
        icon_file = os.path.join(self.test_dir, "AppIconProcreate.png")
        icon_img.save(icon_file)

        with zipfile.ZipFile(ipa_path, 'w') as z:
            z.writestr(f"Payload/Procreate.app/Info.plist", plistlib.dumps(plist_data))
            z.writestr(f"Payload/Procreate.app/Procreate", macho_bytes)
            z.write(icon_file, f"Payload/Procreate.app/AppIconProcreate.png")

        return ipa_path, plist_data

    def test_procreate_drm_encrypted_ipa_analysis(self):
        """Tests that FairPlay DRM is accurately detected on App Store Procreate IPAs."""
        ipa_path, _ = self.create_mock_procreate_ipa(is_encrypted=True)
        report = converter.analyze_ipa(ipa_path)

        self.assertTrue(report["is_valid_ipa"])
        self.assertEqual(report["name"], "Procreate")
        self.assertEqual(report["bundle_id"], "si.savage.procreate")
        self.assertEqual(report["version"], "5.3.5")
        self.assertEqual(report["arch"], "arm64")
        self.assertTrue(report["is_encrypted"], "FairPlay DRM must be detected")
        self.assertEqual(report["cryptid"], 1)
        self.assertTrue(report["has_icon"])
        self.assertEqual(len(report["permissions_requested"]), 6)

    def test_procreate_decrypted_ipa_conversion_to_apk(self):
        """Tests converting a decrypted Procreate IPA to a signed Android APK."""
        ipa_path, _ = self.create_mock_procreate_ipa(is_encrypted=False)
        out_apk = os.path.join(self.test_dir, "procreate_android.apk")

        result = converter.convert_ipa_to_apk(ipa_path, output_apk_path=out_apk)
        self.assertTrue(os.path.exists(result))
        self.assertGreater(os.path.getsize(result), 1024 * 1024)

        # Inspect APK packaging
        with zipfile.ZipFile(result, 'r') as z:
            manifest_bytes = z.read("assets/app_manifest.json")
            manifest_data = json.loads(manifest_bytes.decode('utf-8'))
            self.assertEqual(manifest_data["name"], "Procreate")
            self.assertEqual(manifest_data["package"], "si.savage.procreate")
            self.assertIn("assets/touchHLE_apps/Procreate.app/Procreate", z.namelist())
            self.assertIn("assets/touchHLE_apps/Procreate.app/Info.plist", z.namelist())

        # Verify cryptographic signature
        res = subprocess.run(["jarsigner", "-verify", result], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("jar verified", res.stdout)

    def test_procreate_plist_to_android_manifest(self):
        """Tests translating Procreate's Info.plist into an AndroidManifest.xml."""
        _, plist_data = self.create_mock_procreate_ipa()
        plist_path = os.path.join(self.test_dir, "Info.plist")
        manifest_path = os.path.join(self.test_dir, "AndroidManifest.xml")

        with open(plist_path, "wb") as f:
            plistlib.dump(plist_data, f)

        converter.convert_plist_to_manifest(plist_path, manifest_path)
        self.assertTrue(os.path.exists(manifest_path))

        with open(manifest_path, "r", encoding="utf-8") as f:
            xml = f.read()

        # Check Android package identifier
        self.assertIn('package="si.savage.procreate"', xml)
        self.assertIn('android:versionName="5.3.5"', xml)
        self.assertIn('android:versionCode="39012"', xml)

        # Check permissions required by Procreate
        self.assertIn('android.permission.READ_MEDIA_IMAGES', xml)
        self.assertIn('android.permission.WRITE_EXTERNAL_STORAGE', xml)
        self.assertIn('android.permission.BLUETOOTH', xml)
        self.assertIn('android.permission.BLUETOOTH_CONNECT', xml)
        self.assertIn('android.permission.CAMERA', xml)
        self.assertIn('android.permission.RECORD_AUDIO', xml)

        # Check hardware acceleration & OpenGL ES requirement
        self.assertIn('android:hardwareAccelerated="true"', xml)
        self.assertIn('android:glEsVersion="0x00020000"', xml)

    def test_procreate_swift_brush_engine_transpilation(self):
        """Tests transpiling Procreate brush stroke and canvas drawing code from Swift to Kotlin."""
        swift_source = r'''
import UIKit
import CoreGraphics

struct BrushStrokePoint {
    let location: CGPoint
    let pressure: CGFloat
    let tilt: Float
    let timestamp: Double
}

struct ProcreateBrush {
    let name: String
    let diameter: Float
    let spacing: Float
    let opacity: Float
    let color: UIColor
}

class CanvasDrawingEngine {
    var activeBrush: ProcreateBrush?
    var points: [BrushStrokePoint] = []

    func renderStroke(point: BrushStrokePoint, context: CGContext) -> Bool {
        guard let brush = activeBrush else { return false }
        print("Drawing stroke point at (\(point.location.x), \(point.location.y)) with pressure \(point.pressure)")
        return true
    }
}
'''
        kotlin_code = converter.transpile_swift_to_kotlin(swift_source)

        # Verify Kotlin translation
        self.assertIn("data class BrushStrokePoint(", kotlin_code)
        self.assertIn("data class ProcreateBrush(", kotlin_code)
        self.assertIn("val location: PointF", kotlin_code)
        self.assertIn("val pressure: Float", kotlin_code)
        self.assertIn("val color: Color", kotlin_code)
        self.assertIn("class CanvasDrawingEngine", kotlin_code)
        self.assertIn("fun renderStroke(point: BrushStrokePoint, context: Canvas): Boolean", kotlin_code)
        self.assertIn("val brush = activeBrush ?: return false", kotlin_code)
        self.assertIn("println(", kotlin_code)
        self.assertIn("import android.graphics.Canvas", kotlin_code)
        self.assertIn("import android.graphics.PointF", kotlin_code)

    def test_procreate_xcode_project_conversion(self):
        """Tests converting a Procreate-like Xcode project folder into an Android Studio project."""
        project_dir = os.path.join(self.test_dir, "ProcreateIOS")
        os.makedirs(os.path.join(project_dir, "Sources"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "Resources"), exist_ok=True)

        _, plist_data = self.create_mock_procreate_ipa()
        with open(os.path.join(project_dir, "Info.plist"), "wb") as f:
            plistlib.dump(plist_data, f)

        # Procreate Localizable strings
        strings_content = '''
"brush_library" = "Brush Library";
"color_palettes" = "Color Palettes";
"layers" = "Layers";
"canvas_size" = "Canvas Size";
"export_artwork" = "Share Artwork";
'''
        with open(os.path.join(project_dir, "Resources", "Localizable.strings"), "w", encoding="utf-8") as f:
            f.write(strings_content)

        # Swift files
        with open(os.path.join(project_dir, "Sources", "CanvasView.swift"), "w", encoding="utf-8") as f:
            f.write('''
import UIKit
import CoreGraphics

struct CanvasLayer {
    let id: String
    let opacity: Float
    let isVisible: Bool
}
''')

        output_android = os.path.join(self.test_dir, "ProcreateAndroid")
        converter.convert_project_to_android(project_dir, output_android)

        # Verify Android project structure
        self.assertTrue(os.path.exists(os.path.join(output_android, "build.gradle.kts")))
        self.assertTrue(os.path.exists(os.path.join(output_android, "settings.gradle.kts")))
        self.assertTrue(os.path.exists(os.path.join(output_android, "app", "build.gradle.kts")))
        
        manifest_path = os.path.join(output_android, "app", "src", "main", "AndroidManifest.xml")
        self.assertTrue(os.path.exists(manifest_path))
        with open(manifest_path, "r", encoding="utf-8") as f:
            self.assertIn('package="si.savage.procreate"', f.read())

        strings_path = os.path.join(output_android, "app", "src", "main", "res", "values", "strings.xml")
        self.assertTrue(os.path.exists(strings_path))
        with open(strings_path, "r", encoding="utf-8") as f:
            strings_xml = f.read()
            self.assertIn('<string name="brush_library">Brush Library</string>', strings_xml)
            self.assertIn('<string name="color_palettes">Color Palettes</string>', strings_xml)

        kotlin_file = os.path.join(output_android, "app", "src", "main", "java", "io", "iosondroid", "app", "CanvasView.kt")
        self.assertTrue(os.path.exists(kotlin_file))
        with open(kotlin_file, "r", encoding="utf-8") as f:
            kt = f.read()
            self.assertIn("data class CanvasLayer(", kt)
            self.assertIn("val isVisible: Boolean", kt)

    def test_procreate_cli_workflow(self):
        """Tests the end-to-end CLI experience: ./bin/ios2droid with Procreate."""
        ipa_path, plist_data = self.create_mock_procreate_ipa(is_encrypted=True)

        # 1. Test CLI analyze
        proc = subprocess.run([self.bin_ios2droid, "analyze", ipa_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("App Name:             Procreate", proc.stdout)
        self.assertIn("Bundle ID:            si.savage.procreate", proc.stdout)
        self.assertIn("Architecture:         arm64", proc.stdout)
        self.assertIn("FairPlay DRM Encrypted: YES (Encrypted)", proc.stdout)

        # 2. Test CLI analyze --json
        proc_json = subprocess.run([self.bin_ios2droid, "analyze", ipa_path, "--json"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(proc_json.returncode, 0)
        data = json.loads(proc_json.stdout)
        self.assertEqual(data["bundle_id"], "si.savage.procreate")
        self.assertTrue(data["is_encrypted"])

        # 3. Test CLI plist2manifest
        plist_path = os.path.join(self.test_dir, "Info.plist")
        with open(plist_path, "wb") as f:
            plistlib.dump(plist_data, f)
        manifest_out = os.path.join(self.test_dir, "ProcreateManifest.xml")
        proc_manifest = subprocess.run([self.bin_ios2droid, "plist2manifest", plist_path, "-o", manifest_out], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(proc_manifest.returncode, 0)
        self.assertTrue(os.path.exists(manifest_out))

        # 4. Test CLI swift2kt
        swift_file = os.path.join(self.test_dir, "BrushEngine.swift")
        with open(swift_file, "w") as f:
            f.write("func renderBrush(diameter: Float) -> Bool { return true }\n")
        kt_out = os.path.join(self.test_dir, "BrushEngine.kt")
        proc_swift = subprocess.run([self.bin_ios2droid, "swift2kt", swift_file, "-o", kt_out], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(proc_swift.returncode, 0)
        self.assertTrue(os.path.exists(kt_out))
        with open(kt_out) as f:
            self.assertIn("fun renderBrush(diameter: Float): Boolean", f.read())

if __name__ == "__main__":
    unittest.main()
