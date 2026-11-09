/* Who gets talked about? UK places on a plain MapLibre base map (OpenFreeMap Positron), coloured by Commons "in <place>"
 * mentions 2005 to 2025 against what 2024 English Wikipedia views and population predict, or by either attention alone.
 * Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  const fmt = n => n == null ? 'n/a' : Number(n).toLocaleString('en-GB');
  const DIV = ['#2F6A9E', '#8FB0CF', '#C9C2B4', '#E3A58F', '#B4442E'];
  const SEQ = ['#F3E7C9', '#E9C98F', '#D99B5E', '#B4442E', '#6E1F14'];
  const SEQB = ['#E6EEF4', '#B3CBE0', '#7EA4C8', '#2F6A9E', '#173B5C'];
  let map = null, D = null, mode = qs.get('mode') || 'oe';
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const ct = document.getElementById('cartouche'); const fold = f => ct.classList.toggle('folded', f);
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));

  function colorExpr() {
    if (mode === 'm') return ['interpolate', ['linear'], ['get', 'lm'], 0, SEQ[0], 1, SEQ[1], 2, SEQ[2], 3, SEQ[3], 4.3, SEQ[4]];
    if (mode === 'v') return ['interpolate', ['linear'], ['get', 'lv'], 3, SEQB[0], 4, SEQB[1], 4.7, SEQB[2], 5.5, SEQB[3], 6.6, SEQB[4]];
    return ['interpolate', ['linear'], ['get', 'o'], -3, DIV[0], -1.5, DIV[1], 0, DIV[2], 1.5, DIV[3], 3, DIV[4]];
  }
  function key() {
    const t = document.getElementById('keyTitle'), b = document.getElementById('keyBar'), e = document.getElementById('keyEnds');
    if (mode === 'm') { t.textContent = 'Commons "in" mentions, 2005 to 2025'; b.style.background = `linear-gradient(90deg,${SEQ.join(',')})`; e.innerHTML = '<span>0</span><span>100</span><span>20,000</span>'; }
    else if (mode === 'v') { t.textContent = 'Wikipedia views, 2024'; b.style.background = `linear-gradient(90deg,${SEQB.join(',')})`; e.innerHTML = '<span>1,000</span><span>50,000</span><span>4 million</span>'; }
    else { t.textContent = 'Mentions against expectation'; b.style.background = `linear-gradient(90deg,${DIV.join(',')})`; e.innerHTML = '<span>1/8</span><span>as expected</span><span>8x</span>'; }
    document.querySelectorAll('.chip[data-m]').forEach(x => x.setAttribute('aria-pressed', x.dataset.m === mode));
  }
  function refresh() { map.setPaintProperty('pts', 'circle-color', colorExpr()); key(); }
  function popup(p, ll) {
    let h = `<b class="t">${esc(p.n)}</b><div class="nt">${esc(p.r)}</div><table>`;
    h += `<tr><td>Commons "in ${esc(p.n)}"</td><td><b>${fmt(p.m)}</b> (2005 to 2025)</td></tr>`;
    h += `<tr><td>of which</td><td>${fmt(p.m1)} in 2005 to 2014, ${fmt(p.m2)} in 2015 to 2025</td></tr>`;
    h += `<tr><td>Wikipedia views</td><td><b>${fmt(p.v)}</b> in 2024</td></tr>`;
    h += `<tr><td>Population</td><td>${fmt(p.p)} (${esc(p.ps)})</td></tr>`;
    if (p.e != null) {
      const r = Math.pow(2, p.o);
      h += `<tr><td>Expected mentions</td><td>${fmt(Math.round(p.e))}</td></tr>`;
      h += `<tr><td>Observed / expected</td><td><b>${r >= 1 ? r.toFixed(1) + ' times' : (r > 0.02 ? 'about 1/' + (1 / r).toFixed(1) : 'almost none')}</b>${p.e < 20 ? ' (few expected: treat with care)' : ''}</td></tr>`;
      if (p.s) h += `<tr><td>Commons seats</td><td>${esc(p.s)}</td></tr>`;
    }
    h += '</table>';
    if (p.f) h += `<p class="nt">${esc(p.f)}</p>`;
    if (p.x) h += `<p class="nt">Left out of the analysis: ${esc(p.x)}.</p>`;
    h += `<p class="nt">Expected: from views and population alone. Sources: Hansard (Open Parliament Licence) via Mentioned in the House; <a href="https://en.wikipedia.org/wiki/${encodeURIComponent(p.t.replace(/ /g, '_'))}" target="_blank" rel="noopener">Wikipedia: ${esc(p.t)}</a></p>`;
    new maplibregl.Popup({ maxWidth: '330px', anchor: small ? 'bottom' : undefined }).setLngLat(ll).setHTML(h).addTo(map);
  }
  function setup() {
    const feats = D.places.map((p, i) => ({ type: 'Feature', properties: Object.assign({ i, lm: Math.log10(p.m + 1), lv: Math.log10(Math.max(p.v, 1)), ex: p.e == null ? 1 : 0, sz: p.e == null ? 0 : Math.sqrt(Math.min(p.e, 900)) }, p), geometry: { type: 'Point', coordinates: [p.lo, p.la] } }));
    feats.sort((a, b) => (a.properties.e || 0) - (b.properties.e || 0));
    D.feats = feats;
    map.addSource('p', { type: 'geojson', data: { type: 'FeatureCollection', features: feats }, attribution: 'Hansard: Open Parliament Licence v3.0; Wikipedia pageviews: Wikimedia; Wikidata (CC0)' });
    const k0 = small ? 0.14 : 0.28;
    const rad = ['interpolate', ['linear'], ['zoom'], 4, ['+', 3, ['*', k0, ['get', 'sz']]], 8, ['+', 5, ['*', 0.45, ['get', 'sz']]], 13, ['+', 8, ['*', 0.6, ['get', 'sz']]]];
    map.addLayer({ id: 'xpts', type: 'circle', source: 'p', filter: ['==', ['get', 'ex'], 1], paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, 2.6, 9, 4.5, 13, 7], 'circle-color': '#B9B4AA', 'circle-stroke-color': '#fff', 'circle-stroke-width': 1 } });
    map.addLayer({ id: 'pts', type: 'circle', source: 'p', filter: ['==', ['get', 'ex'], 0], paint: { 'circle-radius': rad, 'circle-color': colorExpr(), 'circle-stroke-color': '#fff', 'circle-stroke-width': 1.2, 'circle-opacity': ['case', ['has', 'f'], 0.45, 0.95] } });
    map.addLayer({ id: 'lbl', type: 'symbol', source: 'p', minzoom: 8, layout: { 'text-field': ['get', 'n'], 'text-size': 11.5, 'text-font': ['Noto Sans Regular'], 'text-offset': [0, 1.1], 'text-anchor': 'top', 'text-optional': true }, paint: { 'text-color': '#2B2119', 'text-halo-color': '#fff', 'text-halo-width': 1.5 } });
    ['pts', 'xpts'].forEach(l => { map.on('click', l, e => popup(e.features[0].properties, e.lngLat)); map.on('mouseenter', l, () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', l, () => map.getCanvas().style.cursor = ''); });
    const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
    btn.addEventListener('click', e => { e.stopPropagation(); const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
    document.addEventListener('click', e => { if (!lp.contains(e.target) && e.target !== btn) { lp.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
    const vis = (ids, v) => ids.forEach(id => map.setLayoutProperty(id, 'visibility', v ? 'visible' : 'none'));
    document.getElementById('lyP').addEventListener('change', e => vis(['pts'], e.target.checked));
    document.getElementById('lyX').addEventListener('change', e => vis(['xpts'], e.target.checked));
    document.getElementById('lyL').addEventListener('change', e => vis(['lbl'], e.target.checked));
    const baseSym = map.getStyle().layers.filter(l => l.type === 'symbol' && !['lbl'].includes(l.id)).map(l => l.id);
    document.getElementById('lyB').addEventListener('change', e => vis(baseSym, e.target.checked));
    document.querySelectorAll('.chip[data-m]').forEach(b => b.addEventListener('click', () => { mode = b.dataset.m; refresh(); }));
    refresh();
  }
  function go(i) {
    const p = D.places[i]; fold(true);
    map.flyTo({ center: [p.lo, p.la], zoom: small ? 9.5 : 10, duration: 1200, offset: [0, Math.round(map.getContainer().clientHeight * (small ? 0.3 : 0.22))] });
    map.once('moveend', () => popup(p, [p.lo, p.la]));
  }
  function setupSearch() {
    const q = document.getElementById('q'), sug = document.getElementById('sug'); let items = [], k = -1;
    const idx = D.places.map((p, i) => ({ n: p.n, nn: norm(p.n), i, s: p.r }));
    const show = () => { const v = norm(q.value.trim()); sug.innerHTML = ''; k = -1; if (v.length < 2) { sug.style.display = 'none'; return; }
      items = idx.filter(x => x.nn.startsWith(v)).concat(idx.filter(x => !x.nn.startsWith(v) && v.length > 3 && x.nn.includes(v))).slice(0, 12);
      items.forEach((it, j) => { const li = document.createElement('li'); li.setAttribute('role', 'option'); li.innerHTML = `${esc(it.n)} <span>${esc(it.s)}</span>`; li.addEventListener('mousedown', e => { e.preventDefault(); pick(j); }); sug.appendChild(li); });
      sug.style.display = items.length ? 'block' : 'none'; };
    const pick = j => { const it = items[j]; if (!it) return; q.value = it.n; sug.style.display = 'none'; go(it.i); };
    q.addEventListener('input', show);
    q.addEventListener('keydown', e => { const lis = [...sug.children];
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); k = Math.max(0, Math.min(lis.length - 1, k + (e.key === 'ArrowDown' ? 1 : -1))); lis.forEach((l, i) => l.setAttribute('aria-selected', i === k)); }
      else if (e.key === 'Enter') { e.preventDefault(); if (!items.length) show(); pick(k < 0 ? 0 : k); } else if (e.key === 'Escape') sug.style.display = 'none'; });
    q.addEventListener('blur', () => setTimeout(() => sug.style.display = 'none', 150));
    document.querySelectorAll('[data-go]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); const i = D.places.findIndex(p => p.n === a.dataset.go); if (i < 0) return;
      document.getElementById('mapWrap').scrollIntoView({ behavior: 'smooth' }); go(i); }));
  }
  fetch('data/site.json').then(r => r.json()).then(d => {
    D = d;
    const at = (qs.get('at') || '').split(',').map(Number);
    const mo = at.length === 3 && at.every(isFinite) ? { center: [at[1], at[0]], zoom: at[2] } : { bounds: [[-8.3, 49.9], [1.9, 58.8]], fitBoundsOptions: { padding: small ? 10 : { top: 40, bottom: 40, left: 360, right: 60 } } };
    const m0 = new maplibregl.Map(Object.assign({ container: 'map', style: STYLE, attributionControl: { compact: true }, maxZoom: 15 }, mo));
    return new Promise((res, rej) => { m0.once('load', () => res(m0)); m0.once('error', e => { if (!m0.loaded()) rej(e.error || e); }); });
  }).then(mm => {
    map = mm; window.__map = mm;
    mm.on('error', e => { const er = e && e.error; if (er && (er.name === 'AbortError' || /abort/i.test(er.message || ''))) return; console.error(er || e); });
    const n = document.getElementById('nojs'); if (n) n.remove();
    mm.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    const foldAt = () => document.querySelectorAll('.maplibregl-ctrl-attrib.maplibregl-compact').forEach(at => { at.classList.remove('maplibregl-compact-show'); at.removeAttribute('open'); });
    mm.once('idle', foldAt); setTimeout(foldAt, 1500);
    setup(); setupSearch();
    if (qs.get('place')) { const i = D.places.findIndex(p => norm(p.n) === norm(qs.get('place'))); if (i >= 0) go(i); }
    document.getElementById('mapWrap').addEventListener('pointerdown', e => { if (e.target.closest && e.target.closest('.cartouche,.ov-top,.lp,.keys,.mfs-btn,.maplibregl-ctrl,.maplibregl-popup')) return; fold(true); }, { capture: true, passive: true, once: true });
  }).catch(e => { console.error(e); const n = document.getElementById('nojs'); if (n) n.textContent = 'The map could not load: ' + e.message; });
})();
