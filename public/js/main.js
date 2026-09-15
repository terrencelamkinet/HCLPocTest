const state = {
  theme: window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
};

function applyTheme() {
  document.documentElement.setAttribute('data-theme', state.theme);
  document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
    btn.textContent = state.theme === 'dark' ? 'Light mode' : 'Dark mode';
    btn.setAttribute('aria-label', state.theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
  });
}

function initThemeToggle() {
  document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
    btn.addEventListener('click', () => {
      state.theme = state.theme === 'dark' ? 'light' : 'dark';
      applyTheme();
    });
  });
  applyTheme();
}

function initMobileNav() {
  const toggle = document.querySelector('[data-nav-toggle]');
  const nav = document.querySelector('.main-nav');
  if (!toggle || !nav) return;
  toggle.addEventListener('click', () => {
    nav.classList.toggle('open');
    toggle.setAttribute('aria-expanded', nav.classList.contains('open') ? 'true' : 'false');
  });
}

function markActiveNav() {
  const page = document.body.dataset.page;
  document.querySelectorAll('[data-nav]').forEach(link => {
    if (link.dataset.nav === page) link.classList.add('active');
  });
}

function animateNumbers() {
  const items = document.querySelectorAll('[data-count]');
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  items.forEach(el => {
    const target = Number(el.dataset.count || 0);
    if (reduce) {
      el.textContent = el.dataset.suffix ? `${target}${el.dataset.suffix}` : target.toLocaleString();
      return;
    }
    let current = 0;
    const step = Math.max(1, Math.ceil(target / 40));
    const tick = () => {
      current += step;
      if (current >= target) current = target;
      el.textContent = el.dataset.raw === 'true'
        ? `${current}${el.dataset.suffix || ''}`
        : `${current.toLocaleString()}${el.dataset.suffix || ''}`;
      if (current < target) requestAnimationFrame(tick);
    };
    tick();
  });
}

function initTabs() {
  const buttons = document.querySelectorAll('[data-tab-target]');
  if (!buttons.length) return;
  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tabTarget;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(target)?.classList.add('active');
    });
  });
}

function initFAQ() {
  document.querySelectorAll('.faq-question').forEach(btn => {
    btn.addEventListener('click', () => {
      const item = btn.closest('.faq-item');
      item.classList.toggle('open');
    });
  });
}

async function loadJsonView() {
  const viewer = document.querySelector('[data-json-viewer]');
  if (!viewer) return;
  try {
    const res = await fetch('./data/demo-data.json');
    const data = await res.json();
    viewer.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    viewer.textContent = 'Unable to load demo-data.json';
  }
}

async function loadSyntheticTables() {
  const targets = document.querySelectorAll('[data-table]');
  if (!targets.length) return;
  const res = await fetch('./data/demo-data.json');
  const data = await res.json();

  targets.forEach(target => {
    const type = target.dataset.table;
    if (type === 'companies') {
      target.innerHTML = data.companies.map(c => `
        <tr>
          <td>${c.company}</td>
          <td>${c.segment}</td>
          <td>${c.owner}</td>
          <td>${c.healthScore}</td>
          <td>${c.lastTouchpointDays} days</td>
          <td>${c.pipelineStage}</td>
        </tr>`).join('');
    }
    if (type === 'projects') {
      target.innerHTML = data.projects.map(p => `
        <tr>
          <td>${p.project}</td>
          <td>${p.account}</td>
          <td>${p.stage}</td>
          <td>${p.value}</td>
          <td>${p.nextStep}</td>
          <td>${p.daysOpen}</td>
        </tr>`).join('');
    }
    if (type === 'activity') {
      target.innerHTML = data.activityFeed.map(a => `
        <tr>
          <td>${a.time}</td>
          <td>${a.type}</td>
          <td>${a.account}</td>
          <td>${a.summary}</td>
          <td>${a.status}</td>
        </tr>`).join('');
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initThemeToggle();
  initMobileNav();
  markActiveNav();
  animateNumbers();
  initTabs();
  initFAQ();
  loadJsonView();
  loadSyntheticTables();
});
