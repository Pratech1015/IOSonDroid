#!/usr/bin/env python3
"""
generate_metadata.py
Populates the metadata/ directory with rich F-Droid metadata YAML files
for all curated iOS-on-Android apps.
"""

import os
import yaml

METADATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'metadata')
os.makedirs(METADATA_DIR, exist_ok=True)

APPS_METADATA = [
    {
        "packageName": "si.savage.procreate",
        "Name": "Procreate - Digital Illustration & Painting",
        "Summary": "The award-winning iOS creative digital art studio built for Android",
        "Categories": ["Graphics", "Productivity"],
        "License": "Proprietary / Open Compatibility Container",
        "AuthorName": "Savage Interactive Pty Ltd & IOSonDroid Team",
        "WebSite": "https://procreate.com",
        "SourceCode": "https://github.com/Pratech1015/IOSonDroid",
        "IssueTracker": "https://github.com/Pratech1015/IOSonDroid/issues",
        "Changelog": "https://procreate.com/updates",
        "Description": (
            "Procreate is the premier creative studio loved by millions of digital artists and illustrators. "
            "Packaged and converted for Android devices using the IOSonDroid standalone compatibility engine.\n\n"
            "Features:\n"
            "* Ultra-high definition canvases and responsive touch sketching\n"
            "* Advanced Valkyrie brush engine with customizable pressure curve\n"
            "* Full layer system with 25 layer blend modes and clipping masks\n"
            "* Continuous autosave so you never lose your artwork\n"
            "* Bluetooth stylus pressure and tilt sensitivity support\n"
            "* Comprehensive export formats (PSD, TIFF, transparent PNG, multi-page PDF)\n"
            "* 4K time-lapse recording and replay support"
        )
    },
    {
        "packageName": "org.touchhle.android",
        "Name": "touchHLE - iOS App Emulator",
        "Summary": "High-level emulator for early iPhone OS / iOS apps and games",
        "Categories": ["Emulation", "Games"],
        "License": "GPL-3.0-or-later",
        "AuthorName": "touchHLE Team & hikari_no_yume",
        "WebSite": "https://touchhle.org",
        "SourceCode": "https://github.com/touchHLE/touchHLE",
        "IssueTracker": "https://github.com/touchHLE/touchHLE/issues",
        "Changelog": "https://touchhle.org/news/",
        "Description": (
            "touchHLE is an open-source, high-level emulator designed to run early iPhone OS "
            "and iOS apps (such as classic Super Monkey Ball, Rolando, Doom Classic, and early 32-bit apps) "
            "directly on modern Android devices.\n\n"
            "Features:\n"
            "* Run decrypted .ipa and .app bundles with native ARM performance\n"
            "* Built-in graphical app launcher for Android\n"
            "* Full touch screen and multi-touch support recreating the iPhone experience\n"
            "* OpenAL-based high fidelity audio emulation\n"
            "* Hardware accelerated OpenGL ES graphics rendering"
        )
    },
    {
        "packageName": "com.bluebubbles.messaging",
        "Name": "BlueBubbles - iMessage for Android",
        "Summary": "Send and receive Apple iMessages and FaceTime calls on Android",
        "Categories": ["Communication", "Ecosystem"],
        "License": "Apache-2.0",
        "AuthorName": "BlueBubbles Team",
        "WebSite": "https://bluebubbles.app",
        "SourceCode": "https://github.com/BlueBubblesApp/bluebubbles-app",
        "IssueTracker": "https://github.com/BlueBubblesApp/bluebubbles-app/issues",
        "Changelog": "https://github.com/BlueBubblesApp/bluebubbles-app/releases",
        "Description": (
            "BlueBubbles is an open-source ecosystem client that brings Apple iMessage to Android. "
            "Communicate seamlessly with iPhone users without losing any of Apple's flagship messaging features.\n\n"
            "Features:\n"
            "* Full iMessage support: Send and receive texts, voice notes, stickers, and high-res media\n"
            "* Tapbacks: Love, like, dislike, laugh, emphasize, and question reactions\n"
            "* Typing indicators and read receipts in real-time\n"
            "* FaceTime integration: Receive incoming FaceTime calls directly on Android\n"
            "* Direct message replies and message editing support\n"
            "* End-to-end encrypted connection to your private bridge"
        )
    },
    {
        "packageName": "com.moseoridev.warpshare",
        "Name": "WarpShare - Apple AirDrop Client",
        "Summary": "Native Apple AirDrop file transfer sender and receiver for Android",
        "Categories": ["Connectivity", "Tools"],
        "License": "GPL-3.0-or-later",
        "AuthorName": "moseoridev & MoKee OpenSource",
        "WebSite": "https://github.com/moseoridev/WarpShare",
        "SourceCode": "https://github.com/moseoridev/WarpShare",
        "IssueTracker": "https://github.com/moseoridev/WarpShare/issues",
        "Changelog": "https://github.com/moseoridev/WarpShare/releases",
        "Description": (
            "WarpShare enables high-speed, local peer-to-peer file sharing between Android and Apple devices "
            "(Mac, iPhone, iPad) using the native Apple AirDrop protocol.\n\n"
            "Features:\n"
            "* Send files, photos, and videos to Apple devices running macOS or iOS\n"
            "* Discovered seamlessly in Apple's native AirDrop sharing sheet\n"
            "* Uses local Wi-Fi / AWDL direct transfers with maximum throughput\n"
            "* Zero external servers, zero cloud uploads, completely private and offline\n"
            "* Material You UI paired with Cupertino device discovery icons"
        )
    },
    {
        "packageName": "de.seemoo.at_tracking_detection",
        "Name": "AirGuard - AirTag & Find My Protection",
        "Summary": "Protect against unwanted Apple AirTag and Find My tracking",
        "Categories": ["Security", "Privacy"],
        "License": "MIT",
        "AuthorName": "SEEMOO Lab (TU Darmstadt)",
        "WebSite": "https://airguard.app",
        "SourceCode": "https://github.com/seemoo-lab/AirGuard",
        "IssueTracker": "https://github.com/seemoo-lab/AirGuard/issues",
        "Changelog": "https://github.com/seemoo-lab/AirGuard/releases",
        "Description": (
            "AirGuard protects Android users against unwanted tracking by Apple AirTags, "
            "Apple Find My accessories, and Bluetooth beacons. Developed by the Secure Mobile "
            "Networking Lab (SEEMOO) at TU Darmstadt.\n\n"
            "Features:\n"
            "* Background scanning for nearby Apple AirTags and Find My network trackers\n"
            "* Automatic alerts when a tracker has been following you over multiple locations\n"
            "* Play alarm sound directly on the suspect AirTag to locate it easily\n"
            "* Interactive map showing where and when the tracker was detected\n"
            "* Instructions on how to safely disable suspect trackers"
        )
    },
    {
        "packageName": "com.agupta07505.smartisland",
        "Name": "SmartIsland - iOS Dynamic Island",
        "Summary": "Interactive Apple iOS Dynamic Island notifications and pill for Android",
        "Categories": ["System", "Customization"],
        "License": "GPL-3.0-or-later",
        "AuthorName": "agupta07505",
        "WebSite": "https://github.com/agupta07505/SmartIsland",
        "SourceCode": "https://github.com/agupta07505/SmartIsland",
        "IssueTracker": "https://github.com/agupta07505/SmartIsland/issues",
        "Changelog": "https://github.com/agupta07505/SmartIsland/releases",
        "Description": (
            "SmartIsland brings the Apple iPhone Dynamic Island interaction model to any Android device. "
            "It turns your punch-hole camera cutout into a fluid, responsive floating pill.\n\n"
            "Features:\n"
            "* Music playback controls with animated frequency visualizer\n"
            "* Incoming phone call notifications with instant answer/reject actions\n"
            "* Timer and stopwatch countdown live activities\n"
            "* Battery charging animations and percentage status\n"
            "* Expandable pill with long-press gesture interactions\n"
            "* Customizable position, size, and notch alignment"
        )
    },
    {
        "packageName": "com.mccal.folio",
        "Name": "Folio Launcher - iOS SpringBoard",
        "Summary": "Clean Apple iOS 17/18-style SpringBoard launcher for Android",
        "Categories": ["System", "Launcher"],
        "License": "GPL-3.0-or-later",
        "AuthorName": "McCal-Codes",
        "WebSite": "https://github.com/McCal-Codes/folio",
        "SourceCode": "https://github.com/McCal-Codes/folio",
        "IssueTracker": "https://github.com/McCal-Codes/folio/issues",
        "Changelog": "https://github.com/McCal-Codes/folio/releases",
        "Description": (
            "Folio Launcher is a minimalist, iPhone-inspired SpringBoard launcher designed to replicate "
            "the visual polish and fluid physics of Apple iOS on Android.\n\n"
            "Features:\n"
            "* Authentic iOS SpringBoard grid with rounded squircle app icons\n"
            "* iOS-style App Library with automated categorization and alphabetical search\n"
            "* iOS widget stacking support and home screen editing mode (jiggle mode)\n"
            "* Fluid spring physics and transition animations\n"
            "* Support for foldables, tablets, and standard Android smartphones"
        )
    },
    {
        "packageName": "io.iosondroid.calculator",
        "Name": "Cupertino Calculator - iOS Calculator",
        "Summary": "Pixel-perfect recreation of the Apple iOS Calculator for Android",
        "Categories": ["Stock Apps", "Tools"],
        "License": "MIT",
        "AuthorName": "IOSonDroid Community",
        "WebSite": "https://github.com/AppAuxin/iOS-Calculator",
        "SourceCode": "https://github.com/AppAuxin/iOS-Calculator",
        "IssueTracker": "https://github.com/AppAuxin/iOS-Calculator/issues",
        "Changelog": "https://github.com/AppAuxin/iOS-Calculator/releases",
        "Description": (
            "Cupertino Calculator is a faithful recreation of Apple's default iOS Calculator app for Android.\n\n"
            "Features:\n"
            "* Iconic circular orange and dark-gray keypad layout\n"
            "* Swipe gesture across the display digits to delete characters\n"
            "* Landscape orientation switches seamlessly into Apple's Scientific Calculator\n"
            "* Native iOS haptic feedback on button presses\n"
            "* San Francisco typography and Apple Human Interface Guidelines styling"
        )
    },
    {
        "packageName": "io.iosondroid.notes",
        "Name": "Cupertino Notes - iOS Notes",
        "Summary": "Apple iOS Notes recreation with rich text, folders, and yellow accents",
        "Categories": ["Stock Apps", "Productivity"],
        "License": "Apache-2.0",
        "AuthorName": "IOSonDroid Community",
        "WebSite": "https://github.com/IOSonDroid/CupertinoNotes",
        "SourceCode": "https://github.com/IOSonDroid/CupertinoNotes",
        "IssueTracker": "https://github.com/IOSonDroid/CupertinoNotes/issues",
        "Changelog": "https://github.com/IOSonDroid/CupertinoNotes/releases",
        "Description": (
            "Cupertino Notes brings the elegance of Apple's iOS Notes app to Android.\n\n"
            "Features:\n"
            "* Classic yellow-accented Apple notepad aesthetic with paper texture\n"
            "* Folder hierarchy: iCloud, On My Device, and Quick Notes\n"
            "* Checklists, bullet lists, numbered lists, and title/heading typography\n"
            "* Pin favorite notes to the top of your list\n"
            "* Encrypted local storage with biometric lock (Fingerprint/Face Unlock)\n"
            "* Markdown export and sharing options"
        )
    },
    {
        "packageName": "io.iosondroid.controlcenter",
        "Name": "iOS Control Center",
        "Summary": "Apple iOS frosted-glass Control Center overlay with quick toggles",
        "Categories": ["System", "Customization"],
        "License": "GPL-3.0-or-later",
        "AuthorName": "IOSonDroid Community",
        "WebSite": "https://github.com/IOSonDroid/iOSControlCenter",
        "SourceCode": "https://github.com/IOSonDroid/iOSControlCenter",
        "IssueTracker": "https://github.com/IOSonDroid/iOSControlCenter/issues",
        "Changelog": "https://github.com/IOSonDroid/iOSControlCenter/releases",
        "Description": (
            "iOS Control Center provides a fluid Apple-style Control Center swipe panel on Android.\n\n"
            "Features:\n"
            "* Swipe down from top-right corner or edge handle to reveal\n"
            "* Frosted glass backdrop blur effect matching iOS 17/18\n"
            "* Large volume and brightness vertical sliders with smooth animation\n"
            "* Quick connectivity platter: Wi-Fi, Bluetooth, Airplane mode, Cellular data\n"
            "* Media playback widget with track details and play/pause/skip\n"
            "* Flashlight, Calculator, Camera, Screen Record, and Do Not Disturb shortcuts"
        )
    },
    {
        "packageName": "de.seemoo.openhaystack",
        "Name": "OpenHaystack Mobile - Find My Network",
        "Summary": "Track custom Bluetooth tags using Apple's crowdsourced Find My network",
        "Categories": ["Connectivity", "Tools"],
        "License": "GPL-3.0-or-later",
        "AuthorName": "SEEMOO Lab",
        "WebSite": "https://seemoo.de/openhaystack",
        "SourceCode": "https://github.com/seemoo-lab/openhaystack",
        "IssueTracker": "https://github.com/seemoo-lab/openhaystack/issues",
        "Changelog": "https://github.com/seemoo-lab/openhaystack/releases",
        "Description": (
            "OpenHaystack Mobile allows tracking DIY AirTags and personal Bluetooth beacons using "
            "Apple's massive Find My network directly from an Android device.\n\n"
            "Features:\n"
            "* Track OpenHaystack devices broadcast via Bluetooth LE\n"
            "* Map view showing current and historical locations\n"
            "* Compatible with ESP32, nRF51/nRF52, BBC micro:bit, and Raspberry Pi Pico beacons\n"
            "* Zero dependence on Apple iPhone hardware"
        )
    },
    {
        "packageName": "oss.krtirtho.spotube",
        "Name": "Spotube - Apple Music Experience",
        "Summary": "Apple Music-inspired music client with synced lyrics and Cupertino UI",
        "Categories": ["Multimedia", "Music"],
        "License": "GPL-3.0-or-later",
        "AuthorName": "Kingkor Roy Tirtho",
        "WebSite": "https://spotube.krtirtho.dev",
        "SourceCode": "https://github.com/krtirtho/spotube",
        "IssueTracker": "https://github.com/krtirtho/spotube/issues",
        "Changelog": "https://github.com/krtirtho/spotube/releases",
        "Description": (
            "Spotube is a modern, privacy-respecting music player that delivers an Apple Music-like "
            "experience on Android with stunning Cupertino aesthetics.\n\n"
            "Features:\n"
            "* Apple Music-styled frosted glass now-playing sheet with fluid gradient backgrounds\n"
            "* Real-time time-synced karaoke lyrics with line-by-line animations\n"
            "* Zero audio ads, completely free and open source\n"
            "* High-bitrate audio playback with local caching and offline downloads\n"
            "* Clean Cupertino-inspired design system"
        )
    },
    {
        "packageName": "ml.docilealligator.infinityforreddit",
        "Name": "Infinity - Apollo Experience",
        "Summary": "The closest open-source equivalent to Apollo for Reddit on Android",
        "Categories": ["Communication", "Social"],
        "License": "GPL-3.0-or-later",
        "AuthorName": "Docile Alligator",
        "WebSite": "https://github.com/Docile-Alligator/Infinity-For-Reddit",
        "SourceCode": "https://github.com/Docile-Alligator/Infinity-For-Reddit",
        "IssueTracker": "https://github.com/Docile-Alligator/Infinity-For-Reddit/issues",
        "Changelog": "https://github.com/Docile-Alligator/Infinity-For-Reddit/releases",
        "Description": (
            "Infinity for Reddit provides Android users with the fluid, gesture-first experience "
            "that made the iOS-exclusive Apollo for Reddit famous.\n\n"
            "Features:\n"
            "* Full swipe gestures to upvote, downvote, save, collapse comments, and reply\n"
            "* Clean compact card and media views inspired by iOS Apollo\n"
            "* Lazy Mode: Smooth automated scrolling through posts and media\n"
            "* Deep theme customization with OLED true dark mode\n"
            "* Multi-account support and custom API key integration"
        )
    }
]

def main():
    for app in APPS_METADATA:
        pkg = app["packageName"]
        yml_path = os.path.join(METADATA_DIR, f"{pkg}.yml")
        with open(yml_path, "w", encoding="utf-8") as f:
            yaml.dump(app, f, sort_keys=False, allow_unicode=True)
        print(f"Generated metadata: {yml_path}")

if __name__ == "__main__":
    main()
