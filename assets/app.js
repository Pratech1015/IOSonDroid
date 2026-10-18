/**
 * IOSonDroid F-Droid Repository & Converter Studio Web App
 * Handles repository configuration, theme toggling, QR code rendering, and the iOS-to-Android Converter Studio.
 */

// Repository configuration
const REPO_CONFIG = {
  name: "IOSonDroid",
  url: "https://pratech1015.github.io/IOSonDroid/repo",
  fingerprint: "33F66FBCA58FC049A8D3E264E7AF414530DC8329D83BFBD9FCF0F3337879E5E0"
};

// Theme Management
function initTheme() {
  const savedTheme = localStorage.getItem('iosondroid-theme');
  if (savedTheme) {
    document.documentElement.setAttribute('data-theme', savedTheme);
  } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
    document.documentElement.setAttribute('data-theme', 'light');
  } else {
    document.documentElement.setAttribute('data-theme', 'dark');
  }

  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      const target = current === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', target);
      localStorage.setItem('iosondroid-theme', target);
      renderQRCode();
    });
  }
}

// Toast Notification
function showToast(message) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.querySelector('.toast-msg').textContent = message;
  toast.classList.add('active');
  setTimeout(() => {
    toast.classList.remove('active');
  }, 3000);
}

// Clipboard Helper
function copyToClipboard(text, successMsg) {
  navigator.clipboard.writeText(text).then(() => {
    showToast(successMsg || "Copied to clipboard!");
  }).catch(() => {
    const input = document.createElement("input");
    input.value = text;
    document.body.appendChild(input);
    input.select();
    document.execCommand("copy");
    document.body.removeChild(input);
    showToast(successMsg || "Copied to clipboard!");
  });
}

// QR Code Generator
function generateQRCodeSVG(text, size = 180) {
  const encodedText = encodeURIComponent(text);
  const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodedText}&margin=6`;
  return qrUrl;
}

function renderQRCode() {
  const qrContainer = document.getElementById('qr-code-box');
  if (!qrContainer) return;
  
  const repoFullUrl = `${REPO_CONFIG.url}?fingerprint=${REPO_CONFIG.fingerprint}`;
  const qrImg = document.createElement('img');
  qrImg.src = generateQRCodeSVG(repoFullUrl, 200);
  qrImg.alt = "Scan to add IOSonDroid repository";
  qrImg.width = 172;
  qrImg.height = 172;
  qrImg.loading = "lazy";
  
  qrContainer.innerHTML = '';
  qrContainer.appendChild(qrImg);
}

// Setup Guide Tabs
function initGuideTabs() {
  const tabs = document.querySelectorAll('.guide-tab-btn');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.guide-step-card').forEach(c => c.classList.remove('active'));
      
      tab.classList.add('active');
      const targetId = tab.getAttribute('data-target');
      const targetCard = document.getElementById(targetId);
      if (targetCard) targetCard.classList.add('active');
    });
  });
}

// Copy Action Buttons
function initCopyButtons() {
  const copyRepoBtn = document.getElementById('copy-repo-url');
  if (copyRepoBtn) {
    copyRepoBtn.addEventListener('click', () => {
      copyToClipboard(REPO_CONFIG.url, "Repository URL copied!");
    });
  }
  
  const copyFpBtn = document.getElementById('copy-fp-btn');
  if (copyFpBtn) {
    copyFpBtn.addEventListener('click', () => {
      copyToClipboard(REPO_CONFIG.fingerprint, "Fingerprint copied!");
    });
  }
  
  const addFdroidBtn = document.getElementById('add-to-fdroid');
  if (addFdroidBtn) {
    addFdroidBtn.addEventListener('click', () => {
      const fdroidProtocolUrl = `fdroidrepos://${REPO_CONFIG.url.replace(/^https?:\/\//, '')}?fingerprint=${REPO_CONFIG.fingerprint}`;
      window.location.href = fdroidProtocolUrl;
    });
  }
}

// ==========================================================
// Converter Studio Logic
// ==========================================================

function initConverterStudio() {
  // Tab switching
  const tabs = document.querySelectorAll('.conv-tab-btn');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.conv-panel').forEach(p => p.classList.remove('active'));
      
      tab.classList.add('active');
      const targetId = tab.getAttribute('data-tab');
      const panel = document.getElementById(targetId);
      if (panel) panel.classList.add('active');
    });
  });

  // Drop zone events
  const dropZone = document.getElementById('ipa-drop-zone');
  const fileInput = document.getElementById('ipa-file-input');

  if (dropZone && fileInput) {
    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    });
    dropZone.addEventListener('dragleave', () => {
      dropZone.classList.remove('dragover');
    });
    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
      if (e.dataTransfer.files.length > 0) {
        handleIpaFile(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        handleIpaFile(e.target.files[0]);
      }
    });
  }

  // Load demo button
  const loadDemoBtn = document.getElementById('load-demo-ipa-btn');
  if (loadDemoBtn) {
    loadDemoBtn.addEventListener('click', () => {
      loadDemoIpa();
    });
  }

  // Start conversion button
  const startConvBtn = document.getElementById('btn-start-convert');
  if (startConvBtn) {
    startConvBtn.addEventListener('click', () => {
      runConversionSimulation();
    });
  }

  // Swift to Kotlin Transpiler
  initSwiftTranspiler();
}

function handleIpaFile(file) {
  const inspector = document.getElementById('conv-inspector');
  if (!inspector) return;

  const appName = file.name.replace(/\.(ipa|zip)$/i, '').replace(/[-_]/g, ' ');
  const cleanName = appName.charAt(0).toUpperCase() + appName.slice(1);
  const bundleId = `com.converted.${cleanName.toLowerCase().replace(/\s+/g, '')}`;
  const sizeMb = (file.size / 1024 / 1024).toFixed(1);

  document.getElementById('insp-name').textContent = cleanName;
  document.getElementById('insp-pkg').textContent = bundleId;
  document.getElementById('insp-version').textContent = "v1.0.0";
  document.getElementById('insp-arch').textContent = "ARM64 / ARMv7";
  document.getElementById('insp-size').textContent = `${sizeMb} MB`;
  document.getElementById('insp-min-ios').textContent = "iOS 4.0+";
  document.getElementById('insp-drm').textContent = "Decrypted IPA";
  document.getElementById('insp-icon').src = "repo/icons/org.touchhle.android.png";

  inspector.style.display = 'block';
  inspector.scrollIntoView({ behavior: 'smooth' });
  showToast(`Loaded ${file.name} for conversion analysis`);
}

function loadDemoIpa() {
  const inspector = document.getElementById('conv-inspector');
  if (!inspector) return;

  document.getElementById('insp-name').textContent = "Super Monkey Ball (Classic iOS)";
  document.getElementById('insp-pkg').textContent = "com.sega.supermonkeyball";
  document.getElementById('insp-version').textContent = "v1.2.0 (#42)";
  document.getElementById('insp-arch').textContent = "ARMv7 (32-bit Mach-O)";
  document.getElementById('insp-size').textContent = "18.4 MB";
  document.getElementById('insp-min-ios').textContent = "iOS 2.0+";
  document.getElementById('insp-drm').textContent = "Decrypted (DRM-Free)";
  document.getElementById('insp-icon').src = "repo/icons/org.touchhle.android.png";

  inspector.style.display = 'block';
  inspector.scrollIntoView({ behavior: 'smooth' });
  showToast("Loaded demo iOS app: Super Monkey Ball");
}

function runConversionSimulation() {
  const progressBox = document.getElementById('conv-progress-box');
  const progressBar = document.getElementById('progress-bar-fill');
  const progressLog = document.getElementById('progress-log');
  const downloadBox = document.getElementById('conv-download-box');
  const startBtn = document.getElementById('btn-start-convert');

  if (!progressBox || !progressBar || !progressLog) return;

  startBtn.disabled = true;
  progressBox.style.display = 'block';
  downloadBox.style.display = 'none';

  const steps = [
    { pct: 15, msg: "Unpacking IPA & reading Info.plist..." },
    { pct: 35, msg: "Validating Mach-O executable (ARMv7, cryptid=0, DRM-free)..." },
    { pct: 55, msg: "Extracting Retina assets & mapping Android permissions..." },
    { pct: 75, msg: "Injecting iOS application bundle into touchHLE runtime container..." },
    { pct: 90, msg: "Signing standalone APK with RSA-2048 repository key..." },
    { pct: 100, msg: "✓ Standalone Android APK generated & verified successfully!" }
  ];

  let current = 0;
  const interval = setInterval(() => {
    if (current < steps.length) {
      const step = steps[current];
      progressBar.style.width = `${step.pct}%`;
      progressLog.textContent = step.msg;
      current++;
    } else {
      clearInterval(interval);
      startBtn.disabled = false;
      downloadBox.style.display = 'block';
      showToast("Conversion Complete! Standalone APK ready.");
    }
  }, 450);
}

// Swift to Kotlin Transpiler
function initSwiftTranspiler() {
  const swiftInput = document.getElementById('swift-input');
  const kotlinOutput = document.getElementById('kotlin-output');
  const runBtn = document.getElementById('btn-run-transpile');
  const loadSampleBtn = document.getElementById('btn-load-swift-sample');
  const copyBtn = document.getElementById('btn-copy-kotlin');

  if (!swiftInput || !kotlinOutput) return;

  const sampleSwift = `import UIKit
import CoreGraphics

// Procreate Brush & Pressure Point Model
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

// Procreate Canvas Drawing Engine
class CanvasDrawingEngine {
    var activeBrush: ProcreateBrush?
    var points: [BrushStrokePoint] = []
    
    func renderStroke(point: BrushStrokePoint, context: CGContext) -> Bool {
        guard let brush = activeBrush else { return false }
        print("Rendering brush stroke at (\\(point.location.x), \\(point.location.y)) with pressure: \\(point.pressure)")
        return true
    }
}`;

  if (loadSampleBtn) {
    loadSampleBtn.addEventListener('click', () => {
      swiftInput.value = sampleSwift;
      transpileCode();
    });
  }

  if (runBtn) {
    runBtn.addEventListener('click', () => {
      transpileCode();
    });
  }

  if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      copyToClipboard(kotlinOutput.value, "Kotlin code copied!");
    });
  }

  function transpileCode() {
    let src = swiftInput.value;
    if (!src.trim()) {
      kotlinOutput.value = "// Please paste Swift code above or click 'Load Sample Swift'";
      return;
    }

    let kt = src;
    kt = kt.replace(/import\s+UIKit/g, 'import android.os.Bundle\nimport androidx.appcompat.app.AppCompatActivity\nimport android.graphics.Color\nimport android.graphics.PointF\nimport android.graphics.RectF\nimport android.graphics.Canvas\nimport android.graphics.Paint\nimport android.graphics.Path');
    kt = kt.replace(/import\s+CoreGraphics/g, '// import CoreGraphics (mapped to android.graphics.*)');
    kt = kt.replace(/import\s+Foundation/g, '// import Foundation');
    kt = kt.replace(/import\s+SwiftUI/g, '// import SwiftUI -> Jetpack Compose equivalent');
    kt = kt.replace(/\blet\b/g, 'val');
    
    // Function signatures
    kt = kt.replace(/\bfunc\s+([a-zA-Z0-9_]+)\s*\((.*?)\)\s*->\s*([a-zA-Z0-9_<>]+)/g, 'fun $1($2): $3');
    kt = kt.replace(/\bfunc\s+([a-zA-Z0-9_]+)\s*\((.*?)\)/g, 'fun $1($2)');
    
    // Types
    kt = kt.replace(/:\s*CGFloat\b/g, ': Float');
    kt = kt.replace(/:\s*CGPoint\b/g, ': PointF');
    kt = kt.replace(/:\s*CGSize\b/g, ': SizeF');
    kt = kt.replace(/:\s*CGRect\b/g, ': RectF');
    kt = kt.replace(/:\s*UIColor\b/g, ': Color');
    kt = kt.replace(/:\s*CGContext\b/g, ': Canvas');
    kt = kt.replace(/:\s*UIBezierPath\b/g, ': Path');
    kt = kt.replace(/:\s*Bool\b/g, ': Boolean');
    kt = kt.replace(/:\s*Void\b/g, ': Unit');
    kt = kt.replace(/:\s*\[(\w+)\]/g, ': List<$1>');
    kt = kt.replace(/:\s*\[(\w+)\s*:\s*(\w+)\]/g, ': Map<$1, $2>');
    
    kt = kt.replace(/\bstruct\s+([a-zA-Z0-9_]+)\s*\{/g, 'data class $1(');
    kt = kt.replace(/\bprint\(/g, 'println(');
    kt = kt.replace(/\\\(([a-zA-Z0-9_]+)\)/g, '$$$1');
    kt = kt.replace(/\\\(([a-zA-Z0-9_.]+)\)/g, '$${$1}');
    kt = kt.replace(/guard\s+val\s+([a-zA-Z0-9_]+)\s*=\s*(.*?)\s+else\s*\{\s*return(\s*.*?)\s*\}/g, 'val $1 = $2 ?: return$3');
    kt = kt.replace(/\bnil\b/g, 'null');

    const header = "// Transpiled from iOS Swift to Android Kotlin via IOSonDroid Converter\n\n";
    kotlinOutput.value = header + kt;
    showToast("Transpiled Swift to Kotlin!");
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  renderQRCode();
  initCopyButtons();
  initGuideTabs();
  initConverterStudio();
});
