/* TEEBUSINESS · Admin enhancement layer — additive & defensive (Django 5.2).
   Nav icons · ⌘K command palette · instant table filter · toasts · reveals. */
(function () {
  'use strict';
  var ready = function (fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  };

  // ---- icon set (stroke paths) -------------------------------------------
  var ICONS = {
    dashboard: 'M3 10.5L12 3l9 7.5M5 9.5V20a1 1 0 001 1h3v-6h6v6h3a1 1 0 001-1V9.5',
    users: 'M17 20h5v-1a4 4 0 00-3-3.87M9 20H4v-1a4 4 0 013-3.87m6-1.13a4 4 0 10-4-4 4 4 0 004 4z',
    user: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM4 21v-1a6 6 0 0112 0v1',
    box: 'M20 7L12 3 4 7m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4',
    cart: 'M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2 4h12m-9 4a1 1 0 11-2 0 1 1 0 012 0zm8 0a1 1 0 11-2 0 1 1 0 012 0z',
    tag: 'M7 7h.01M3 11l8.5-8.5a2 2 0 012.8 0L21 9.2a2 2 0 010 2.8L12.5 20.5a2 2 0 01-2.8 0L3 13.8V11z',
    mail: 'M3 8l9 6 9-6M5 5h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2z',
    shield: 'M12 3l8 3v6c0 5-3.4 7.7-8 9-4.6-1.3-8-4-8-9V6l8-3z',
    bookmark: 'M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-4-7 4V5z',
    layers: 'M12 3l9 5-9 5-9-5 9-5zm9 9l-9 5-9-5m18 4l-9 5-9-5',
    bell: 'M15 17h5l-1.4-1.4A2 2 0 0118 14.2V11a6 6 0 10-12 0v3.2c0 .5-.2 1-.6 1.4L4 17h5m6 0a3 3 0 11-6 0',
    cog: 'M10.3 3.3a1 1 0 011.4 0l.8.8a1 1 0 00.9.3l1.1-.2a1 1 0 011.2.8l.2 1.1a1 1 0 00.5.7l1 .5a1 1 0 01.5 1.3l-.5 1a1 1 0 000 .9l.5 1a1 1 0 01-.5 1.3l-1 .5a1 1 0 00-.5.7l-.2 1.1a1 1 0 01-1.2.8l-1.1-.2a1 1 0 00-.9.3l-.8.8a1 1 0 01-1.4 0l-.8-.8a1 1 0 00-.9-.3l-1.1.2a1 1 0 01-1.2-.8l-.2-1.1a1 1 0 00-.5-.7l-1-.5a1 1 0 01-.5-1.3l.5-1a1 1 0 000-.9l-.5-1a1 1 0 01.5-1.3l1-.5a1 1 0 00.5-.7l.2-1.1a1 1 0 011.2-.8l1.1.2a1 1 0 00.9-.3l.8-.8zM12 15a3 3 0 100-6 3 3 0 000 6z',
    dot: 'M12 12h.01'
  };
  function iconFor(text, href) {
    var s = ((href || '') + ' ' + (text || '')).toLowerCase();
    if (/dashboard|accueil|home/.test(s)) return ICONS.dashboard;
    if (/order|commande/.test(s)) return ICONS.cart;
    if (/product|produit|item/.test(s)) return ICONS.box;
    if (/categor/.test(s)) return ICONS.tag;
    if (/brand|marque/.test(s)) return ICONS.bookmark;
    if (/size|stock/.test(s)) return ICONS.layers;
    if (/group|users|clients/.test(s)) return ICONS.users;
    if (/user|utilisateur|account|compte/.test(s)) return ICONS.user;
    if (/otp|security|securit|log|token|permission/.test(s)) return ICONS.shield;
    if (/mail|email|newsletter|campaign|message|communicat|promo/.test(s)) return ICONS.mail;
    if (/subscriber|abonn|notif/.test(s)) return ICONS.bell;
    if (/setting|param|config/.test(s)) return ICONS.cog;
    return ICONS.dot;
  }
  function svg(path, cls) {
    return '<svg class="' + (cls || 'tb-nav-ico') + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
      'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="' + path + '"/></svg>';
  }

  // ---- 1. nav-sidebar icons ----------------------------------------------
  function decorateNav() {
    var links = document.querySelectorAll('#nav-sidebar a');
    links.forEach(function (a) {
      if (a.querySelector('.tb-nav-ico')) return;
      a.insertAdjacentHTML('afterbegin', svg(iconFor(a.textContent, a.getAttribute('href'))));
    });
  }

  // ---- 2. command palette (⌘K) -------------------------------------------
  var pal, palInput, palList, palItems = [], palActive = 0, navItems = [];
  function collectNav() {
    navItems = [];
    document.querySelectorAll('#nav-sidebar a').forEach(function (a) {
      var grp = a.closest('table');
      var cap = grp ? grp.querySelector('caption') : null;
      navItems.push({
        label: a.textContent.trim(),
        href: a.getAttribute('href'),
        group: cap ? cap.textContent.trim() : '',
        icon: iconFor(a.textContent, a.getAttribute('href'))
      });
    });
  }
  function buildPalette() {
    if (pal) return;
    var ov = document.createElement('div');
    ov.className = 'tb-pal-overlay';
    ov.innerHTML = '<div class="tb-pal" role="dialog" aria-label="Navigation rapide">' +
      '<input type="text" placeholder="Rechercher une section, un modèle…" aria-label="Recherche" />' +
      '<div class="tb-pal-list"></div></div>';
    document.body.appendChild(ov);
    pal = ov; palInput = ov.querySelector('input'); palList = ov.querySelector('.tb-pal-list');
    ov.addEventListener('click', function (e) { if (e.target === ov) closePalette(); });
    palInput.addEventListener('input', renderPalette);
    palInput.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
      else if (e.key === 'Enter') { e.preventDefault(); go(); }
      else if (e.key === 'Escape') { closePalette(); }
    });
  }
  function renderPalette() {
    var q = palInput.value.trim().toLowerCase();
    var matches = navItems.filter(function (it) {
      return !q || (it.label + ' ' + it.group).toLowerCase().indexOf(q) !== -1;
    }).slice(0, 40);
    palActive = 0;
    if (!matches.length) { palList.innerHTML = '<div class="tb-pal-empty">Aucun résultat</div>'; palItems = []; return; }
    palList.innerHTML = matches.map(function (it, i) {
      return '<div class="tb-pal-item' + (i === 0 ? ' active' : '') + '" data-href="' + it.href + '">' +
        svg(it.icon) + '<span>' + it.label + '</span>' + (it.group ? '<small>' + it.group + '</small>' : '') + '</div>';
    }).join('');
    palItems = Array.prototype.slice.call(palList.querySelectorAll('.tb-pal-item'));
    palItems.forEach(function (el, i) {
      el.addEventListener('mouseenter', function () { setActive(i); });
      el.addEventListener('click', function () { window.location.href = el.getAttribute('data-href'); });
    });
  }
  function setActive(i) { palItems.forEach(function (el, j) { el.classList.toggle('active', i === j); }); palActive = i; }
  function move(d) { if (!palItems.length) return; var n = (palActive + d + palItems.length) % palItems.length; setActive(n); palItems[n].scrollIntoView({ block: 'nearest' }); }
  function go() { if (palItems[palActive]) window.location.href = palItems[palActive].getAttribute('data-href'); }
  function openPalette() { buildPalette(); collectNav(); renderPalette(); pal.classList.add('open'); palInput.value = ''; renderPalette(); setTimeout(function () { palInput.focus(); }, 20); }
  function closePalette() { if (pal) pal.classList.remove('open'); }

  // ---- 3. topbar command button ------------------------------------------
  function addCmdButton() {
    var header = document.getElementById('header');
    var tools = document.getElementById('user-tools');
    if (!header || document.querySelector('.tb-cmd')) return;
    var btn = document.createElement('button');
    btn.type = 'button'; btn.className = 'tb-cmd'; btn.setAttribute('aria-label', 'Recherche rapide');
    btn.innerHTML = svg(ICONS.dashboard.length ? 'M21 21l-4.35-4.35m1.35-5.65a7 7 0 11-14 0 7 7 0 0114 0z' : '', 'tb-cmd-ico') +
      '<span class="tb-cmd-label">Rechercher…</span><span class="tb-kbd">Ctrl K</span>';
    btn.addEventListener('click', openPalette);
    if (tools) header.insertBefore(btn, tools); else header.appendChild(btn);
  }

  // ---- 4. instant client-side table filter -------------------------------
  function addQuickFilter() {
    var rl = document.getElementById('result_list');
    var search = document.getElementById('changelist-search');
    if (!rl || !search || document.querySelector('.tb-quickfilter')) return;
    var input = document.createElement('input');
    input.type = 'text'; input.className = 'tb-quickfilter';
    input.placeholder = 'Filtre rapide (page actuelle)…';
    input.setAttribute('aria-label', 'Filtre rapide de la page');
    search.appendChild(input);
    var rows = Array.prototype.slice.call(rl.tBodies[0] ? rl.tBodies[0].rows : []);
    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase();
      rows.forEach(function (tr) {
        tr.style.display = (!q || tr.textContent.toLowerCase().indexOf(q) !== -1) ? '' : 'none';
      });
    });
  }

  // ---- 5. toasts ----------------------------------------------------------
  function enhanceToasts() {
    document.querySelectorAll('ul.messagelist li').forEach(function (li) {
      if (li.querySelector('.tb-toast-close')) return;
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'tb-toast-close'; b.setAttribute('aria-label', 'Fermer'); b.innerHTML = '&times;';
      b.addEventListener('click', function () { dismiss(li); });
      li.appendChild(b);
      if (li.classList.contains('success')) setTimeout(function () { dismiss(li); }, 5500);
    });
  }
  function dismiss(li) { li.style.transition = 'opacity .25s, transform .25s, margin .25s, height .25s'; li.style.opacity = '0'; li.style.transform = 'translateY(-6px)'; setTimeout(function () { li.remove(); }, 260); }

  // ---- 6. reveal on scroll -----------------------------------------------
  function reveals() {
    if (!('IntersectionObserver' in window)) return;
    var els = document.querySelectorAll('.tb-card, .dashboard .module, #changelist .results, .change-form .module');
    if (!els.length) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('tb-in'); io.unobserve(e.target); } });
    }, { threshold: 0.06 });
    els.forEach(function (el, i) { el.classList.add('tb-reveal'); el.style.transitionDelay = Math.min(i * 35, 210) + 'ms'; io.observe(el); });
  }

  // ---- 7. global keyboard -------------------------------------------------
  function keys() {
    document.addEventListener('keydown', function (e) {
      var mod = e.metaKey || e.ctrlKey;
      if (mod && (e.key === 'k' || e.key === 'K')) { e.preventDefault(); pal && pal.classList.contains('open') ? closePalette() : openPalette(); return; }
      if (e.key === 'Escape') closePalette();
      var tag = (e.target.tagName || '').toLowerCase();
      if (e.key === '/' && tag !== 'input' && tag !== 'textarea' && tag !== 'select') {
        var sb = document.getElementById('searchbar') || document.querySelector('.tb-quickfilter') || document.getElementById('nav-filter');
        if (sb) { e.preventDefault(); sb.focus(); }
      }
    });
  }

  ready(function () {
    try { decorateNav(); } catch (e) {}
    try { addCmdButton(); } catch (e) {}
    try { addQuickFilter(); } catch (e) {}
    try { enhanceToasts(); } catch (e) {}
    try { reveals(); } catch (e) {}
    try { keys(); } catch (e) {}
  });
})();
