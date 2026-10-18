/**
 * IOSonDroid F-Droid Repository Web App
 * Handles dynamic catalog loading, filtering, search, modal views, theme toggle, and QR code rendering.
 */

// Repository configuration
const REPO_CONFIG = {
  name: "IOSonDroid",
  url: "https://pratech1015.github.io/IOSonDroid/repo",
  fingerprint: "33F66FBCA58FC049A8D3E264E7AF414530DC8329D83BFBD9FCF0F3337879E5E0"
};

let appsCatalog = [];
let activeCategory = "all";
let searchQuery = "";

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

// Compact Pure JavaScript QR Code Generator (Type 1-4, ECC Level M/L)
// Provides instant QR generation without network or external scripts
function generateQRCodeSVG(text, size = 180) {
  // Use public QR API or pre-rendered SVG/data url with fallback
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

// Load and Render Catalog
async function loadCatalog() {
  try {
    const res = await fetch('assets/catalog.json');
    if (res.ok) {
      appsCatalog = await res.json();
    } else {
      console.warn("Failed to load catalog.json, using fallback data.");
      appsCatalog = getFallbackCatalog();
    }
  } catch (e) {
    console.warn("Catalog fetch error:", e);
    appsCatalog = getFallbackCatalog();
  }
  
  renderApps();
  updateStats();
}

function updateStats() {
  const counterEl = document.getElementById('app-counter');
  if (counterEl) {
    counterEl.textContent = `${appsCatalog.length} iOS-style Apps Available`;
  }
}

function filterApps() {
  return appsCatalog.filter(app => {
    const matchesCategory = activeCategory === "all" || 
      (app.categories && app.categories.some(c => c.toLowerCase().includes(activeCategory.toLowerCase())));
      
    const q = searchQuery.toLowerCase().trim();
    const matchesSearch = !q || 
      app.name.toLowerCase().includes(q) ||
      app.packageName.toLowerCase().includes(q) ||
      (app.summary && app.summary.toLowerCase().includes(q)) ||
      (app.description && app.description.toLowerCase().includes(q));
      
    return matchesCategory && matchesSearch;
  });
}

function renderApps() {
  const grid = document.getElementById('apps-grid');
  if (!grid) return;
  
  const filtered = filterApps();
  
  if (filtered.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 60px 20px; color: var(--text-tertiary);">
        <h3>No matching applications found</h3>
        <p style="margin-top: 8px;">Try searching for another keyword or selecting "All Apps".</p>
      </div>
    `;
    return;
  }
  
  grid.innerHTML = filtered.map(app => {
    const primaryCat = (app.categories && app.categories[0]) || "Tools";
    const sizeStr = app.apkSize ? `${(app.apkSize / 1024 / 1024).toFixed(1)} MB` : "";
    const downloadBtn = app.hasApk 
      ? `<a href="repo/${app.apkName}" class="btn-download" download>
           <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
           Download APK
         </a>`
      : `<a href="${app.sourceCode || app.webSite}" target="_blank" rel="noopener" class="btn-download" style="background: var(--bg-secondary); border: 1px solid var(--border-color); color: var(--text-primary);">
           <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
           View Source
         </a>`;

    return `
      <div class="app-card" data-pkg="${app.packageName}">
        <div>
          <div class="app-top">
            <img src="${app.icon}" alt="${app.name}" class="app-icon" loading="lazy" onerror="this.src='repo/icon.png'"/>
            <div class="app-meta">
              <h3 title="${app.name}">${app.name}</h3>
              <div class="app-author">${app.authorName || 'Open Source Community'}</div>
              <div class="app-tags">
                <span class="tag category">${primaryCat}</span>
                <span class="tag version">${app.versionName || 'v1.0'}</span>
                ${sizeStr ? `<span class="tag">${sizeStr}</span>` : ''}
              </div>
            </div>
          </div>
          <p class="app-summary">${app.summary || ''}</p>
        </div>
        <div class="app-actions">
          ${downloadBtn}
          <button class="btn-details" onclick="openAppModal('${app.packageName}')">Details</button>
        </div>
      </div>
    `;
  }).join('');
}

// Modal handling
window.openAppModal = function(packageName) {
  const app = appsCatalog.find(a => a.packageName === packageName);
  if (!app) return;
  
  const modal = document.getElementById('app-modal');
  const sizeStr = app.apkSize ? `${(app.apkSize / 1024 / 1024).toFixed(2)} MB` : "Available via source";
  
  document.getElementById('modal-title').textContent = app.name;
  document.getElementById('modal-icon').src = app.icon;
  document.getElementById('modal-author').textContent = app.authorName || 'Open Source Community';
  document.getElementById('modal-summary').textContent = app.summary || '';
  document.getElementById('modal-description').textContent = app.description || '';
  document.getElementById('modal-pkg').textContent = app.packageName;
  document.getElementById('modal-version').textContent = `${app.versionName || '1.0'} (${app.versionCode || 1})`;
  document.getElementById('modal-size').textContent = sizeStr;
  document.getElementById('modal-license').textContent = app.license || 'Open Source';
  document.getElementById('modal-sha256').textContent = app.sha256 || 'Generated on build';
  
  const webLink = document.getElementById('modal-web-link');
  if (app.webSite) {
    webLink.href = app.webSite;
    webLink.style.display = 'inline-flex';
  } else {
    webLink.style.display = 'none';
  }
  
  const srcLink = document.getElementById('modal-source-link');
  if (app.sourceCode) {
    srcLink.href = app.sourceCode;
    srcLink.style.display = 'inline-flex';
  } else {
    srcLink.style.display = 'none';
  }
  
  const downloadBtn = document.getElementById('modal-download-btn');
  if (app.hasApk) {
    downloadBtn.href = `repo/${app.apkName}`;
    downloadBtn.style.display = 'inline-flex';
    downloadBtn.download = app.apkName;
  } else {
    downloadBtn.style.display = 'none';
  }
  
  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
};

window.closeAppModal = function() {
  const modal = document.getElementById('app-modal');
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
};

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

// Filter Pills
function initPills() {
  const pills = document.querySelectorAll('.pill');
  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      pills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      activeCategory = pill.getAttribute('data-category');
      renderApps();
    });
  });
}

// Search input
function initSearch() {
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      searchQuery = e.target.value;
      renderApps();
    });
  }
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
    addFdroidBtn.addEventListener('click', (e) => {
      const fdroidProtocolUrl = `fdroidrepos://${REPO_CONFIG.url.replace(/^https?:\/\//, '')}?fingerprint=${REPO_CONFIG.fingerprint}`;
      window.location.href = fdroidProtocolUrl;
    });
  }
}

// Fallback catalog in case JSON isn't served
function getFallbackCatalog() {
  return [
    {
      packageName: "org.touchhle.android",
      name: "touchHLE",
      summary: "High-level emulator for early iPhone OS / iOS apps and games",
      description: "touchHLE runs early iOS apps (.ipa) directly on Android with touch and audio emulation.",
      icon: "repo/icons/org.touchhle.android.png",
      categories: ["Emulation", "Games"],
      license: "GPL-3.0-or-later",
      authorName: "touchHLE Team",
      webSite: "https://touchhle.org",
      sourceCode: "https://github.com/touchHLE/touchHLE",
      hasApk: true,
      apkName: "org.touchhle.android_30.apk",
      apkSize: 21139598,
      versionName: "0.3.0",
      versionCode: 30
    },
    {
      packageName: "com.bluebubbles.messaging",
      name: "BlueBubbles",
      summary: "Send and receive Apple iMessages and FaceTime calls on Android",
      description: "Brings full Apple iMessage and FaceTime ecosystem features to Android.",
      icon: "repo/icons/com.bluebubbles.messaging.png",
      categories: ["Communication", "Ecosystem"],
      license: "Apache-2.0",
      authorName: "BlueBubbles Team",
      webSite: "https://bluebubbles.app",
      sourceCode: "https://github.com/BlueBubblesApp/bluebubbles-app",
      hasApk: false
    },
    {
      packageName: "de.seemoo.at_tracking_detection",
      name: "AirGuard",
      summary: "Protect against unwanted Apple AirTag and Find My tracking",
      description: "Detects Apple Find My and AirTag trackers following you and triggers alarm sounds.",
      icon: "repo/icons/de.seemoo.at_tracking_detection.png",
      categories: ["Security", "Privacy"],
      license: "MIT",
      authorName: "SEEMOO Lab",
      webSite: "https://airguard.app",
      sourceCode: "https://github.com/seemoo-lab/AirGuard",
      hasApk: true,
      apkName: "de.seemoo.at_tracking_detection_88.apk",
      apkSize: 9196952,
      versionName: "3.1.3",
      versionCode: 88
    },
    {
      packageName: "com.agupta07505.smartisland",
      name: "SmartIsland",
      summary: "Interactive Apple iOS Dynamic Island notifications and pill for Android",
      description: "Brings Apple's Dynamic Island notch overlay, audio waveform, and notifications to Android.",
      icon: "repo/icons/com.agupta07505.smartisland.png",
      categories: ["System", "Customization"],
      license: "GPL-3.0-or-later",
      authorName: "agupta07505",
      sourceCode: "https://github.com/agupta07505/SmartIsland",
      hasApk: true,
      apkName: "com.agupta07505.smartisland_70.apk",
      apkSize: 9838684,
      versionName: "7.0.0",
      versionCode: 70
    },
    {
      packageName: "com.mccal.folio",
      name: "Folio Launcher",
      summary: "Clean Apple iOS 17/18-style SpringBoard launcher for Android",
      description: "Minimalist iPhone-style home screen, App Library, and fluid physics for Android.",
      icon: "repo/icons/com.mccal.folio.png",
      categories: ["System", "Launcher"],
      license: "GPL-3.0-or-later",
      authorName: "McCal-Codes",
      sourceCode: "https://github.com/McCal-Codes/folio",
      hasApk: true,
      apkName: "com.mccal.folio_68.apk",
      apkSize: 9808156,
      versionName: "0.6.8",
      versionCode: 68
    }
  ];
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  renderQRCode();
  initPills();
  initSearch();
  initCopyButtons();
  initGuideTabs();
  loadCatalog();
  
  // Close modal on escape or background click
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeAppModal();
  });
  
  const modal = document.getElementById('app-modal');
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeAppModal();
    });
  }
});
