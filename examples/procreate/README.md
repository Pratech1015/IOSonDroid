# Procreate Conversion Testing Example

This directory contains authentic iOS project assets for **Procreate** (`si.savage.procreate`) to test the `ios2droid` converter suite.

## Files
- `Info.plist`: Authentic Procreate bundle definitions, permissions (Photo Library, Bluetooth styluses, Camera, Microphone), and orientation setup.
- `BrushEngine.swift`: Procreate-style brush engine model (`BrushStrokePoint`, `ProcreateBrush`, `CanvasDrawingEngine`, `CanvasLayer`) utilizing CoreGraphics & UIKit types.
- `Localizable.strings`: Authentic Procreate UI strings for localization.

## Testing with `ios2droid`

### 1. Convert Info.plist to AndroidManifest.xml
```bash
./bin/ios2droid plist2manifest examples/procreate/Info.plist -o AndroidManifest.xml
```

### 2. Transpile Swift Drawing Code to Kotlin
```bash
./bin/ios2droid swift2kt examples/procreate/BrushEngine.swift -o BrushEngine.kt
```

### 3. Convert Localizable.strings to Android strings.xml
```bash
./bin/ios2droid strings2xml examples/procreate/Localizable.strings -o strings.xml
```

### 4. Generate Full Android Studio Project
```bash
./bin/ios2droid project examples/procreate -o ProcreateAndroid
```

### 5. Run Procreate Test Suite
```bash
python3 -m unittest tests/test_procreate.py
```
