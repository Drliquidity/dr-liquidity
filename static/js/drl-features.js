/* ============================================================
   DR LIQUIDITY — Feature Bundle
   Dark Mode + Command Palette + Keyboard Shortcuts + Toasts
   + Onboarding Tour + Sound Effects + Achievements
   ============================================================ */
(function() {
  'use strict';

  const STORAGE = {
    theme: 'drl-theme',
    onboarded: 'drl-onboarded',
    sound: 'drl-sound',
    achievements: 'drl-achievements'
  };

  // ----- THEME MANAGEMENT -----
  function getTheme() { return localStorage.getItem(STORAGE.theme) || 'light'; }
  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(STORAGE.theme, theme);
  }
  setTheme(getTheme());

  // ----- SOUND MANAGEMENT -----
  let soundEnabled = localStorage.getItem(STORAGE.sound) !== 'off';
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  let audioCtx = null;
  function ensureAudio() {
    if (!audioCtx && AudioCtx) audioCtx = new AudioCtx();
    if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
  }
  function playTone(freq, duration = 0.08, type = 'sine', vol = 0.06) {
    if (!soundEnabled || !audioCtx) return;
    try {
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = type;
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(vol, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
      osc.connect(gain).connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + duration);
    } catch(e) {}
  }
  const SFX = {
    click: () => playTone(800, 0.05, 'sine', 0.04),
    success: () => { playTone(523, 0.08); setTimeout(() => playTone(659, 0.08), 60); setTimeout(() => playTone(784, 0.12), 120); },
    error: () => playTone(220, 0.18, 'sawtooth', 0.05),
    hover: () => playTone(1200, 0.03, 'sine', 0.02),
    notification: () => { playTone(880, 0.06); setTimeout(() => playTone(1100, 0.08), 50); }
  };

  // ----- TOAST SYSTEM -----
  const toastContainer = document.createElement('div');
  toastContainer.className = 'toast-container';
  document.body.appendChild(toastContainer);
  function showToast({ title, message, type = 'info', duration = 3500 }) {
    ensureAudio();
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icons = { success: '✓', error: '✕', info: 'i', warning: '!' };
    toast.innerHTML = `
      <div class="toast-icon">${icons[type] || 'i'}</div>
      <div class="toast-content">
        <div class="toast-title">${title || ''}</div>
        ${message ? `<div class="toast-msg">${message}</div>` : ''}
      </div>
    `;
    toastContainer.appendChild(toast);
    if (type === 'success') SFX.success();
    else if (type === 'error') SFX.error();
    else SFX.notification();
    setTimeout(() => {
      toast.classList.add('dismissing');
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }
  window.showToast = showToast;

  // ----- COMMAND PALETTE -----
  const cmdkItems = [
    { group: 'Navigation', icon: '🏠', title: 'Home', kbd: 'G H', href: '/' },
    { group: 'Navigation', icon: '📊', title: 'Journal — All Trades', kbd: 'G J', href: '/journal' },
    { group: 'Navigation', icon: '📅', title: 'Journal — Calendar', kbd: 'G C', href: '/journal/calendar' },
    { group: 'Navigation', icon: '📆', title: 'Journal — Weekly', href: '/journal/weekly' },
    { group: 'Navigation', icon: '🗓️', title: 'Journal — Monthly', kbd: 'G M', href: '/journal/monthly' },
    { group: 'Navigation', icon: '📈', title: 'Journal — Analytics', href: '/journal/analytics' },
    { group: 'Navigation', icon: '➕', title: 'Log New Trade', kbd: 'N', href: '/journal/new' },
    { group: 'Navigation', icon: '🏢', title: 'Prop Firms Directory', kbd: 'G F', href: '/firms' },
    { group: 'Navigation', icon: '🛠️', title: 'Tools', kbd: 'G T', href: '/tools' },
    { group: 'Navigation', icon: '🧮', title: 'ROI Calculator', href: '/tools/calculator' },
    { group: 'Navigation', icon: '📚', title: 'Education', kbd: 'G E', href: '/education' },
    { group: 'Navigation', icon: '💬', title: 'Community', kbd: 'G M', href: '/community' },
    { group: 'Navigation', icon: '🛒', title: 'Verify Purchase', href: '/purchases/new' },
    { group: 'Navigation', icon: '📊', title: 'Dashboard', kbd: 'G D', href: '/dashboard' },
    { group: 'Navigation', icon: '👤', title: 'My Profile', kbd: 'G P', href: '/profile' },
    { group: 'Navigation', icon: 'ℹ️', title: 'About', href: '/about' },
    { group: 'Actions', icon: '🌗', title: 'Toggle Dark Mode', kbd: '⇧ D', action: () => toggleTheme() },
    { group: 'Actions', icon: '🔊', title: 'Toggle Sound Effects', action: () => toggleSound() },
    { group: 'Actions', icon: '🎓', title: 'Replay Onboarding Tour', action: () => startTour() },
  ];

  let cmdkOverlay = null;
  let cmdkActiveIdx = 0;
  let cmdkFiltered = [];
  function buildCmdk() {
    if (cmdkOverlay) return;
    cmdkOverlay = document.createElement('div');
    cmdkOverlay.className = 'cmdk-overlay';
    cmdkOverlay.innerHTML = `
      <div class="cmdk-modal">
        <div class="cmdk-input-wrap">
          <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
          <input type="text" class="cmdk-input" placeholder="Type a command or search..." autocomplete="off" />
          <span class="cmdk-kbd">ESC</span>
        </div>
        <div class="cmdk-results"></div>
      </div>
    `;
    document.body.appendChild(cmdkOverlay);
    cmdkOverlay.addEventListener('click', (e) => { if (e.target === cmdkOverlay) closeCmdk(); });
    const input = cmdkOverlay.querySelector('.cmdk-input');
    input.addEventListener('input', (e) => { renderCmdk(e.target.value); });
    input.addEventListener('keydown', handleCmdkKey);
  }
  function renderCmdk(query) {
    const q = (query || '').toLowerCase().trim();
    cmdkFiltered = cmdkItems.filter(i => !q || i.title.toLowerCase().includes(q) || i.group.toLowerCase().includes(q));
    if (cmdkActiveIdx >= cmdkFiltered.length) cmdkActiveIdx = 0;
    const results = cmdkOverlay.querySelector('.cmdk-results');
    if (cmdkFiltered.length === 0) {
      results.innerHTML = '<div class="cmdk-empty">No results found. Try a different search.</div>';
      return;
    }
    let html = '';
    let lastGroup = '';
    cmdkFiltered.forEach((item, i) => {
      if (item.group !== lastGroup) {
        html += `<div class="cmdk-group">${item.group}</div>`;
        lastGroup = item.group;
      }
      html += `<a href="${item.href || '#'}" data-idx="${i}" class="cmdk-item ${i === cmdkActiveIdx ? 'active' : ''}">
        <span class="cmdk-item-icon">${item.icon}</span>
        <span>${item.title}</span>
        ${item.kbd ? `<span class="cmdk-item-kbd">${item.kbd}</span>` : ''}
      </a>`;
      if (item.action) {
        const link = html.match(/data-idx="\d+"/);
      }
    });
    results.innerHTML = html;
    // Attach click handlers for actions
    results.querySelectorAll('.cmdk-item').forEach((el, i) => {
      el.addEventListener('click', (e) => {
        e.preventDefault();
        const item = cmdkFiltered[i];
        if (item.action) { item.action(); closeCmdk(); }
        else if (item.href) { window.location.href = item.href; }
      });
    });
  }
  function openCmdk() {
    buildCmdk();
    cmdkOverlay.classList.add('active');
    const input = cmdkOverlay.querySelector('.cmdk-input');
    input.value = '';
    cmdkActiveIdx = 0;
    renderCmdk('');
    setTimeout(() => input.focus(), 50);
  }
  function closeCmdk() { cmdkOverlay?.classList.remove('active'); }
  function handleCmdkKey(e) {
    if (e.key === 'ArrowDown') { e.preventDefault(); cmdkActiveIdx = Math.min(cmdkActiveIdx + 1, cmdkFiltered.length - 1); renderCmdk(e.target.value); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); cmdkActiveIdx = Math.max(cmdkActiveIdx - 1, 0); renderCmdk(e.target.value); }
    else if (e.key === 'Enter') {
      e.preventDefault();
      const item = cmdkFiltered[cmdkActiveIdx];
      if (item) {
        if (item.action) { item.action(); closeCmdk(); }
        else if (item.href) { window.location.href = item.href; }
      }
    } else if (e.key === 'Escape') { closeCmdk(); }
  }

  // ----- THEME TOGGLE -----
  function toggleTheme() {
    const cur = getTheme();
    const next = cur === 'light' ? 'dark' : 'light';
    setTheme(next);
    showToast({ title: next === 'dark' ? '🌙 Dark mode' : '☀️ Light mode', message: 'Theme switched', type: 'info', duration: 2000 });
  }
  function toggleSound() {
    soundEnabled = !soundEnabled;
    localStorage.setItem(STORAGE.sound, soundEnabled ? 'on' : 'off');
    showToast({ title: soundEnabled ? '🔊 Sound on' : '🔇 Sound off', type: 'info', duration: 2000 });
    if (soundEnabled) SFX.success();
  }
  window.toggleTheme = toggleTheme;
  window.toggleSound = toggleSound;

  // ----- KEYBOARD SHORTCUTS (Gmail-style) -----
  // Press letter to go, then letter to navigate
  const shortcuts = {
    'h': '/',
    'j': '/journal',
    'f': '/firms',
    't': '/tools',
    'c': '/tools/calculator',
    'e': '/education',
    'm': '/community',
    'd': '/dashboard',
    'p': '/profile',
    'n': '/journal/new',
    'a': '/journal/analytics',
    'w': '/journal/weekly',
    'l': '/journal/calendar',
    'o': '/journal/monthly',
    'b': '/firms',
  };
  let lastKey = null;
  let lastKeyTime = 0;
  document.addEventListener('keydown', (e) => {
    // Don't trigger in inputs
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return;
    if (e.ctrlKey || e.metaKey || e.altKey) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); openCmdk(); return; }
      if (e.shiftKey && e.key === 'D') { e.preventDefault(); toggleTheme(); return; }
      if (e.key === '/') { e.preventDefault(); openCmdk(); return; }
      return;
    }
    if (e.key === 'Escape') { closeCmdk(); return; }
    const key = e.key.toLowerCase();
    const now = Date.now();
    if (lastKey && (now - lastKeyTime) < 1000 && shortcuts[lastKey + key]) {
      e.preventDefault();
      window.location.href = shortcuts[lastKey + key];
      lastKey = null;
      return;
    }
    if (shortcuts[key]) {
      // If there's a "G" prefix map, support "G then X"
      if (lastKey === 'g' && shortcuts['g' + key]) {
        e.preventDefault();
        window.location.href = shortcuts['g' + key];
        lastKey = null;
        return;
      }
      // Direct shortcut (no prefix)
      // Only trigger if no other modifier + a single key
      if (e.key.length === 1) {
        lastKey = key;
        lastKeyTime = now;
        // Visual hint
        showKeyHint(key);
        return;
      }
    }
    if (key === 'g' && !e.shiftKey) { lastKey = 'g'; lastKeyTime = now; showKeyHint('g'); return; }
    lastKey = null;
  });

  // Show a key hint popup
  function showKeyHint(key) {
    let hint = document.getElementById('drl-key-hint');
    if (!hint) {
      hint = document.createElement('div');
      hint.id = 'drl-key-hint';
      hint.style.cssText = 'position:fixed;bottom:5rem;left:50%;transform:translateX(-50%);background:rgba(0,0,0,0.85);color:white;padding:0.5rem 1rem;border-radius:0.5rem;font-family:monospace;font-weight:700;font-size:0.9rem;z-index:9999;backdrop-filter:blur(8px);';
      document.body.appendChild(hint);
    }
    hint.textContent = '⌨ ' + key.toUpperCase() + '...';
    hint.style.display = 'block';
    clearTimeout(hint._timer);
    hint._timer = setTimeout(() => { hint.style.display = 'none'; }, 900);
  }

  // ----- ONBOARDING TOUR -----
  function startTour() {
    const steps = [
      { sel: 'a[href="/journal/new"]', title: 'Log Your First Trade', desc: 'Click here to add a trade. We track entry, exit, P&L, and your emotions.', position: 'bottom' },
      { sel: 'a[href="/firms"]', title: 'Compare Prop Firms', desc: '14 firms with verified discount codes. We don\'t take paid placements.', position: 'bottom' },
      { sel: 'a[href="/tools"]', title: 'Use Our Tools', desc: 'ROI Calculator + Performance Tracker. Free forever.', position: 'bottom' },
      { sel: 'a[href="/community"]', title: 'Join the Community', desc: 'Share wins, ask questions. Verified buyers get a badge.', position: 'bottom' },
    ];
    const overlay = document.createElement('div');
    overlay.className = 'tour-overlay active';
    overlay.innerHTML = '<div class="tour-spotlight"></div><div class="tour-card"></div>';
    document.body.appendChild(overlay);
    const spotlight = overlay.querySelector('.tour-spotlight');
    const card = overlay.querySelector('.tour-card');
    let stepIdx = 0;
    function renderStep() {
      const step = steps[stepIdx];
      const target = document.querySelector(step.sel);
      if (!target) { stepIdx = (stepIdx + 1) % steps.length; renderStep(); return; }
      const rect = target.getBoundingClientRect();
      spotlight.style.left = (rect.left - 8) + 'px';
      spotlight.style.top = (rect.top - 8) + 'px';
      spotlight.style.width = (rect.width + 16) + 'px';
      spotlight.style.height = (rect.height + 16) + 'px';
      const cardTop = rect.bottom + 16;
      const cardLeft = Math.max(20, Math.min(window.innerWidth - 380, rect.left));
      card.style.top = cardTop + 'px';
      card.style.left = cardLeft + 'px';
      card.innerHTML = `
        <div class="tour-step-num">${stepIdx + 1}/${steps.length}</div>
        <div class="tour-title">${step.title}</div>
        <div class="tour-desc">${step.desc}</div>
        <div class="tour-actions">
          <button class="tour-btn tour-btn-skip" id="tour-skip">Skip tour</button>
          <div style="display:flex;align-items:center;gap:0.75rem;">
            <div class="tour-progress">${steps.map((_, i) => `<div class="tour-dot ${i === stepIdx ? 'active' : ''}"></div>`).join('')}</div>
            <button class="tour-btn tour-btn-next" id="tour-next">${stepIdx === steps.length - 1 ? "Got it! ✓" : 'Next →'}</button>
          </div>
        </div>
      `;
      card.querySelector('#tour-skip').onclick = endTour;
      card.querySelector('#tour-next').onclick = () => {
        SFX.click();
        if (stepIdx === steps.length - 1) { endTour(); showToast({ title: '🎉 You\'re all set!', message: 'Start logging trades', type: 'success' }); }
        else { stepIdx++; renderStep(); }
      };
    }
    function endTour() { overlay.remove(); localStorage.setItem(STORAGE.onboarded, '1'); }
    renderStep();
    SFX.success();
  }

  // Auto-start tour for new users (not authenticated, first visit)
  function maybeAutoTour() {
    if (localStorage.getItem(STORAGE.onboarded)) return;
    if (window.location.pathname === '/') {
      setTimeout(startTour, 1500);
    }
  }

  // ----- ACHIEVEMENTS -----
  function unlockAchievement(id, title, description, icon) {
    const unlocked = JSON.parse(localStorage.getItem(STORAGE.achievements) || '[]');
    if (unlocked.find(a => a.id === id)) return;
    unlocked.push({ id, title, description, icon, at: Date.now() });
    localStorage.setItem(STORAGE.achievements, JSON.stringify(unlocked));
    showToast({ title: `🏆 ${title}`, message: description, type: 'success', duration: 5000 });
  }
  window.unlockAchievement = unlockAchievement;
  function getAchievements() { return JSON.parse(localStorage.getItem(STORAGE.achievements) || '[]'); }
  window.getAchievements = getAchievements;

  // ----- FLOATING TOOLBAR (theme + sound + cmdk) -----
  function injectToolbar() {
    if (document.getElementById('drl-toolbar')) return;
    const toolbar = document.createElement('div');
    toolbar.id = 'drl-toolbar';
    toolbar.style.cssText = 'position:fixed;bottom:1.25rem;right:1.25rem;z-index:100;display:flex;flex-direction:column;gap:0.5rem;';
    toolbar.innerHTML = `
      <button id="drl-cmdk" title="Command palette (⌘K)" class="drl-fab">⌘K</button>
      <button id="drl-theme" title="Toggle theme" class="drl-fab drl-fab-theme">
        <span class="theme-toggle"></span>
      </button>
      <button id="drl-sound" title="Toggle sound" class="drl-fab">🔊</button>
    `;
    document.body.appendChild(toolbar);
    const style = document.createElement('style');
    style.textContent = `
      .drl-fab {
        width: 44px; height: 44px; border-radius: 12px;
        background: var(--bg-elevated); border: 1px solid var(--border-primary);
        color: var(--text-primary); font-weight: 800; font-size: 0.9rem;
        box-shadow: var(--shadow-md); cursor: pointer; transition: all 0.2s;
        display: flex; align-items: center; justify-content: center;
      }
      .drl-fab:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); }
      .drl-fab-theme { padding: 0; }
    `;
    document.head.appendChild(style);
    document.getElementById('drl-cmdk').onclick = openCmdk;
    document.getElementById('drl-theme').onclick = toggleTheme;
    document.getElementById('drl-sound').onclick = () => {
      const newState = !soundEnabled;
      toggleSound();
      document.getElementById('drl-sound').textContent = newState ? '🔊' : '🔇';
    };
  }

  // ----- INIT -----
  function init() {
    injectToolbar();
    // Auto-tour disabled — was causing the page to dim 1.5s after load with a 75% black overlay
    // Users can still trigger it manually via the command palette (⌘K → "Start Tour")
    // maybeAutoTour();
    // Click sound effect on buttons
    document.addEventListener('click', (e) => {
      const btn = e.target.closest('a, button, .btn-premium, .btn-premium-outline');
      if (btn && !btn.classList.contains('no-sfx')) {
        ensureAudio();
        SFX.click();
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
