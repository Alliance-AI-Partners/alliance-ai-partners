// ===== PAGEKIT v1 · Alliance AI Partners website mock (Figma file 1VGkymJ9AH6vGYgFDAU68A) =====
// Paste this whole block at the top of a use_figma script, then: await K.init('Desktop'|'Mobile'); await K.page('<Figma page name>');
// Every colour, space, radius and type size is bound to the file's variables and styles. Never hard-code a brand hex.
const K = { images: [], notes: [], ground: 'light' };
K.VAR = { pageS: '3:48', raised: '3:49', sunken: '3:50', invRaised: '3:52', scrim: '3:53', tP: '3:54', tS: '3:55', tT: '3:56', link: '3:58', accent: '3:59', onA: '3:60', bSub: '3:61', bD: '3:62', bS: '3:63', aP: '3:64', aS: '3:67', checked: '3:70', ok: '3:74', err: '3:72', warn: '3:76', info: '3:78', navy: '3:8', daylight: '3:9', white: '3:10', cyan: '3:7', p30: '3:12', p38: '3:13', gutter: '3:99', secPad: '3:100', container: '3:101', hair: '3:126', rNone: '3:117', rSm: '3:118', rMd: '3:119', rLg: '3:120', rXl: '3:121', rPill: '3:122' };
K.SP = { 4: '3:104', 8: '3:105', 12: '3:106', 16: '3:107', 20: '3:108', 24: '3:109', 32: '3:110', 40: '3:111', 48: '3:112', 64: '3:113', 80: '3:114', 96: '3:115', 128: '3:116' };
K.C = { btn: '14:114', link: '14:123', nav: '14:129', rule: '14:130', iconBtn: '17:38', header: '17:126', menu: '17:127', footer: '17:351', slot: '18:238', tag: '18:239', chip: '18:247', alert: '18:276', acc: '18:291', field: '19:299', select: '19:336', textarea: '19:367', checkbox: '19:376', radio: '19:384', tz: '20:291', steps: '20:336', key: '20:341', stat: '20:342', svcRow: '21:261', article: '21:262', person: '21:269', job: '21:274', download: '21:282', logoL: '10:37', logoD: '11:37', logoW: '13:38', markL: '13:12', markD: '13:25', flatL: '13:6', flatD: '13:11', swallow: '22:261' };
K.I = Object.fromEntries('alert-triangle:6:6,arrow-left:6:9,arrow-right:6:12,arrow-up-right:6:15,calendar:6:19,check-circle:6:23,check:6:26,chevron-down:6:29,chevron-right:6:32,clock:6:36,close:6:39,copy:6:43,download:6:46,external-link:6:49,file:6:53,globe:6:57,info:6:61,link:6:64,lock:6:68,mail:6:72,map-pin:6:76,menu:6:79,minus:6:82,phone:6:86,play:6:89,plus:6:92,search:6:96,x-circle:6:100,linkedin:6:113,x:6:117,youtube:6:120,facebook:6:103,instagram:6:108'.split(',').map(s => { const [n, a, b] = s.split(':'); return [n, a + ':' + b]; }));
K.SI = Object.fromEntries('advisory:8:8:8:88,ai-strategy:8:14:8:94,automation:8:19:8:99,cloud-integration:8:25:8:105,data-analytics:8:30:8:110,growth:8:38:8:118,launch:8:46:8:126,machine-learning:8:60:8:140,partnership:8:65:8:145,research-insights:8:71:8:151,security-governance:8:76:8:156,training-enablement:8:82:8:162'.split(',').map(s => { const p = s.split(':'); return [p[0], { mono: p[1] + ':' + p[2], dark: p[3] + ':' + p[4] }]; }));

K.init = async (vp) => {
  await figma.loadFontAsync({ family: 'Mona Sans' });
  for (const s of ['Regular', 'SemiBold']) await figma.loadFontAsync({ family: 'Cascadia Mono', style: s });
  K.v = {};
  for (const [k, id] of Object.entries(K.VAR)) K.v[k] = await figma.variables.getVariableByIdAsync('VariableID:' + id);
  for (const [px, id] of Object.entries(K.SP)) K.v['sp' + px] = await figma.variables.getVariableByIdAsync('VariableID:' + id);
  K.ts = Object.fromEntries((await figma.getLocalTextStylesAsync()).map(s => [s.name, s]));
  K.es = Object.fromEntries((await figma.getLocalEffectStylesAsync()).map(s => [s.name, s]));
  K.theme = await figma.variables.getVariableCollectionByIdAsync('VariableCollectionId:3:47');
  K.vpc = await figma.variables.getVariableCollectionByIdAsync('VariableCollectionId:3:85');
  K.sets = {};
  for (const [k, id] of Object.entries(K.C)) K.sets[k] = await figma.getNodeByIdAsync(id);
  const defs = s => s.componentPropertyDefinitions;
  K.key = (setKey, name) => Object.keys(defs(K.sets[setKey])).find(d => d.split('#')[0] === name);
  K.vp = vp; K.M = vp === 'Mobile'; K.W = K.M ? 358 : 1320; K.FW = K.M ? 390 : 1440;
  return K;
};
K.page = async (name) => {
  let p = figma.root.children.find(x => x.name === name);
  if (!p) { p = figma.createPage(); p.name = name; K.notes.push('created page ' + name); }
  await figma.setCurrentPageAsync(p);
  K.P = p; return p;
};
// paints, spacing, radius
K.p = (name, op) => figma.variables.setBoundVariableForPaint({ type: 'SOLID', color: { r: 0, g: 0, b: 0 }, opacity: op === undefined ? 1 : op }, 'color', K.v[name]);
K.gap = (f, px) => { if (K.SP[px]) f.setBoundVariable('itemSpacing', K.v['sp' + px]); else f.itemSpacing = px; };
K.pad = (f, p) => {
  const a = Array.isArray(p) ? (p.length === 2 ? [p[0], p[1], p[0], p[1]] : p) : [p, p, p, p];
  ['paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft'].forEach((k, i) => { const px = a[i]; if (K.SP[px]) f.setBoundVariable(k, K.v['sp' + px]); else f[k] = px; });
};
K.rad = (n, r) => { const m = { none: 'rNone', sm: 'rSm', md: 'rMd', lg: 'rLg', xl: 'rXl', pill: 'rPill' }; if (typeof r === 'string') { for (const k of ['topLeftRadius', 'topRightRadius', 'bottomLeftRadius', 'bottomRightRadius']) n.setBoundVariable(k, K.v[m[r]]); } else n.cornerRadius = r; };
K.sides = (n, s, color = 'bD', w = 1) => { n.strokes = [K.p(color)]; n.strokeAlign = 'INSIDE'; n.strokeTopWeight = s.includes('t') ? w : 0; n.strokeBottomWeight = s.includes('b') ? w : 0; n.strokeLeftWeight = s.includes('l') ? w : 0; n.strokeRightWeight = s.includes('r') ? w : 0; };
// frames: K.f('V'|'H', {name, gap, pad, fill, radius, align, justify, clip, wrap})
K.f = (dir = 'V', o = {}) => {
  const f = figma.createAutoLayout(dir === 'H' ? 'HORIZONTAL' : 'VERTICAL'); f.name = o.name || 'Frame'; f.fills = []; f.clipsContent = !!o.clip;
  if (o.gap !== undefined) K.gap(f, o.gap);
  if (o.pad !== undefined) K.pad(f, o.pad);
  if (o.fill) f.fills = [K.p(o.fill, o.fillOpacity)];
  if (o.radius !== undefined) K.rad(f, o.radius);
  if (o.align) f.counterAxisAlignItems = o.align; // MIN | CENTER | MAX | BASELINE
  if (o.justify) f.primaryAxisAlignItems = o.justify; // MIN | CENTER | MAX | SPACE_BETWEEN
  if (o.clip) f.clipsContent = true;
  if (o.wrap) { f.layoutWrap = 'WRAP'; if (o.rowGap !== undefined) f.counterAxisSpacing = o.rowGap; }
  return f;
};
// add a child and size it: w/h = 'fill' | 'hug' | number; grow = 1 to take the remaining main-axis space
K.add = (parent, node, o = {}) => {
  parent.appendChild(node);
  const isText = node.type === 'TEXT';
  const w = o.w !== undefined ? o.w : (isText ? 'fill' : undefined);
  if (w === 'fill') { node.layoutSizingHorizontal = 'FILL'; if (isText) node.textAutoResize = 'HEIGHT'; }
  else if (typeof w === 'number') { node.layoutSizingHorizontal = 'FIXED'; node.resize(w, node.height); if (isText) node.textAutoResize = 'HEIGHT'; else if ('layoutMode' in node && node.layoutMode !== 'NONE' && o.h === undefined) node.layoutSizingVertical = 'HUG'; }
  else if (w === 'hug' && !isText) node.layoutSizingHorizontal = 'HUG';
  if (o.h === 'fill') node.layoutSizingVertical = 'FILL';
  else if (typeof o.h === 'number') { node.layoutSizingVertical = 'FIXED'; node.resize(node.width, o.h); }
  if (o.grow) node.layoutGrow = 1;
  if (o.abs) { node.layoutPositioning = 'ABSOLUTE'; if (o.x !== undefined) node.x = o.x; if (o.y !== undefined) node.y = o.y; }
  return node;
};
// text: K.t(str, style, color, {accent:'word', links:['substring'], name, align:'LEFT'|'CENTER'|'RIGHT'})
K.t = async (str, style, color = 'tP', o = {}) => {
  const t = figma.createText();
  const st = K.ts[style]; if (!st) throw new Error('No text style ' + style);
  await t.setTextStyleIdAsync(st.id);
  t.characters = str; t.fills = [K.p(color)]; t.name = o.name || str.slice(0, 48);
  if (o.align) t.textAlignHorizontal = o.align;
  if (o.accent) {
    const i = str.indexOf(o.accent);
    if (i < 0) K.notes.push('accent not found: ' + o.accent);
    else {
      const acc = K.ts[style + ' Accent'];
      if (acc) await t.setRangeTextStyleIdAsync(i, i + o.accent.length, acc.id); else K.notes.push('no accent style for ' + style);
      if (K.ground === 'navy') t.setRangeFills(i, i + o.accent.length, [K.p('accent')]);
    }
  }
  for (const l of (o.links || [])) {
    const i = str.indexOf(l); if (i < 0) { K.notes.push('link not found: ' + l); continue; }
    t.setRangeTextDecoration(i, i + l.length, 'UNDERLINE'); t.setRangeFills(i, i + l.length, [K.p('link')]);
    try { t.setRangeTextDecorationThickness(i, i + l.length, { unit: 'PIXELS', value: 1 }); t.setRangeTextDecorationOffset(i, i + l.length, { unit: 'PERCENT', value: 22 }); } catch (e) {}
  }
  return t;
};
// the top-level page frame: K.root('Home — Desktop', x)
K.root = (name, x = 0) => {
  const f = figma.createAutoLayout('VERTICAL'); f.name = name;
  figma.currentPage.appendChild(f);
  f.resize(K.FW, 200); f.counterAxisSizingMode = 'FIXED'; f.primaryAxisSizingMode = 'AUTO';
  f.fills = [K.p('pageS')]; f.clipsContent = true;
  if (K.M) f.setExplicitVariableModeForCollection(K.vpc, '3:5');
  f.x = x; f.y = 0; K.R = f; return f;
};
// a section: full width, Daylight or a whole Navy chapter, fluid vertical padding, centred 1320/358 container
// K.section(root, 'Hero', {ground:'navy', gap:48, padTop, padBottom, bleed:true (no container, no padding)})
K.section = (root, name, o = {}) => {
  const navy = o.ground === 'navy';
  const s = K.f('V', { name: 'Section · ' + name }); K.add(root, s, { w: 'fill' });
  s.counterAxisAlignItems = 'CENTER';
  if (navy) s.setExplicitVariableModeForCollection(K.theme, '3:3');
  s.fills = [K.p('pageS')];
  K.ground = navy ? 'navy' : 'light';
  if (o.bleed) return { s, c: s };
  if (o.padTop !== undefined) K.pad(s, [o.padTop, 0, o.padBottom !== undefined ? o.padBottom : o.padTop, 0]);
  else { s.setBoundVariable('paddingTop', K.v.secPad); s.setBoundVariable('paddingBottom', K.v.secPad); if (o.padBottom !== undefined) K.pad(s, [s.paddingTop, 0, o.padBottom, 0]); }
  const c = K.f('V', { name: 'Container', gap: o.gap !== undefined ? o.gap : 48 });
  s.appendChild(c); c.resize(K.W, 10); c.layoutSizingHorizontal = 'FIXED'; c.setBoundVariable('width', K.v.container); c.layoutSizingVertical = 'HUG';
  return { s, c };
};
// instances
K.inst = (key, props = {}, variant) => {
  const set = K.sets[key]; let comp = set;
  if (set.type === 'COMPONENT_SET') {
    const want = variant || (set.children.some(c => c.name.startsWith('Viewport=')) ? 'Viewport=' + K.vp : null);
    comp = want ? set.children.find(c => c.name === want) : set.defaultVariant;
    if (!comp) throw new Error('No variant ' + want + ' in ' + key);
  }
  const i = comp.createInstance();
  const defs = set.componentPropertyDefinitions; const mapped = {};
  for (const [k, val] of Object.entries(props)) { const full = Object.keys(defs).find(d => d.split('#')[0] === k); if (full) mapped[full] = val; else K.notes.push('unknown prop ' + k + ' on ' + key); }
  if (Object.keys(mapped).length) i.setProperties(mapped);
  return i;
};
K.header = (root, current) => {
  const h = K.inst('header'); K.add(root, h, { w: 'fill' }); h.name = 'Header';
  if (current && !K.M) { const n = h.findOne(x => x.type === 'INSTANCE' && x.name === 'Nav · ' + current); if (n) n.setProperties({ State: 'Current' }); }
  return h;
};
K.footer = (root) => { const f = K.inst('footer'); K.add(root, f, { w: 'fill' }); f.name = 'Footer'; return f; };
// K.btn('See where AI can help', {variant:'Primary'|'Secondary'|'Quiet', size:'SM'|'MD'|'LG', icon:true|false, iconName:'download'})
K.btn = (label, o = {}) => {
  const v = o.variant || 'Primary', s = o.size || (K.M ? 'LG' : 'MD');
  const comp = K.sets.btn.children.find(c => c.name === 'Variant=' + v + ', Size=' + s + ', State=Default');
  const b = comp.createInstance(); b.name = 'Button · ' + label;
  const props = { [K.key('btn', 'Label')]: label, [K.key('btn', 'Show icon')]: o.icon !== undefined ? o.icon : v === 'Primary' };
  if (o.iconName) props[K.key('btn', 'Icon')] = K.I[o.iconName];
  b.setProperties(props); return b;
};
K.link = (label, o = {}) => K.inst('link', { Label: label, Arrow: o.arrow !== false }, 'Size=' + (o.small ? 'Small' : 'Body'));
K.icon = async (name, px = 24, color) => {
  const comp = await figma.getNodeByIdAsync(K.I[name]); const i = comp.createInstance(); i.name = 'Icon · ' + name;
  try { i.rescale(px / 24); } catch (e) { i.resize(px, px); }
  if (color) for (const n of i.findAll(n => ('strokes' in n && n.strokes.length) || ('fills' in n && Array.isArray(n.fills) && n.fills.length))) { if ('strokes' in n && n.strokes.length) n.strokes = [K.p(color)]; if (n.fills && n.fills.length) n.fills = [K.p(color)]; }
  return i;
};
K.svc = async (name, px = 48, dark) => { const comp = await figma.getNodeByIdAsync(K.SI[name][dark ? 'dark' : 'mono']); const i = comp.createInstance(); i.name = 'Service icon · ' + name; try { i.rescale(px / 48); } catch (e) { i.resize(px, px); } return i; };
K.logo = (kind = 'logoL', heightPx = 36) => { const i = K.sets[kind].createInstance(); try { i.rescale(heightPx / 36); } catch (e) {} i.name = 'Logo'; return i; };
K.rule = (w) => { const r = K.sets.rule.createInstance(); r.resize(w || 240, 3); r.name = 'Ribbon rule'; return r; };
// image slot: K.img('IMG-001', 'Hero daybreak', 'New: dawn sky over ribbon hills', w, h, {tone:'Navy', radius:0})
K.img = (id, short, label, w, h, o = {}) => {
  const s = K.inst('slot', { Label: id + ' · ' + label }, 'Tone=' + (o.tone || 'Light'));
  s.name = id + ' · ' + short; s.resize(w, h);
  if (o.radius !== undefined) { for (const k of ['topLeftRadius', 'topRightRadius', 'bottomLeftRadius', 'bottomRightRadius']) { try { s.setBoundVariable(k, null); } catch (e) {} } s.cornerRadius = o.radius; }
  K.images.push({ id, short, label, node: s.id });
  return s;
};
// a raised card (white on Daylight, Partner 30 on navy): 18px radius, 32px padding, hairline, card shadow with lit edge
K.card = async (o = {}) => {
  const c = K.f('V', { name: o.name || 'Card', gap: o.gap !== undefined ? o.gap : 12, pad: o.pad !== undefined ? o.pad : (K.M ? 24 : 32), fill: 'raised', radius: o.radius || 'lg' });
  c.strokes = [K.p('bSub')]; c.strokeAlign = 'INSIDE'; c.strokeWeight = 1; c.clipsContent = true;
  await c.setEffectStyleIdAsync(K.es[o.effect || 'Elevation/Card'].id);
  return c;
};
// asymmetric section head: title 0.9fr | lead 1.1fr on desktop (baseline-aligned), stacked on mobile
K.head = async (parent, title, lead, o = {}) => {
  const style = o.style || 'Heading/2';
  const h = K.f(K.M ? 'V' : 'H', { name: 'Section head', gap: K.M ? 16 : 48, align: K.M ? 'MIN' : 'MAX' });
  K.add(parent, h, { w: 'fill' });
  const tt = await K.t(title, style, 'tP', { accent: o.accent, name: 'Title' });
  if (K.M) K.add(h, tt); else K.add(h, tt, { w: Math.round((K.W - 48) * 0.45) });
  if (lead) { const l = await K.t(lead, o.leadStyle || 'Body/LG', 'tS', { name: 'Lead', links: o.links }); K.add(h, l, K.M ? {} : { grow: 1, w: 'fill' }); }
  return h;
};
// numbered sources list (mono, below a hairline). items: ['U.S. Bureau of Labor Statistics, ... Retrieved 2026-11-02.']
K.sources = async (parent, items, o = {}) => {
  const l = K.f('V', { name: 'Sources', gap: 8, pad: [16, 0, 0, 0] }); K.add(parent, l, { w: 'fill' }); K.sides(l, 't');
  for (let i = 0; i < items.length; i++) {
    const r = K.f('H', { name: 'Source ' + (o.start || 1 + i), gap: 0 }); K.add(l, r, { w: 'fill' });
    K.add(r, await K.t(String((o.start || 1) + i), 'Data/Mono', 'tS', { name: 'n' }), { w: 32 });
    K.add(r, await K.t(items[i], 'Data/Mono', 'tT', { name: 'source' }), { grow: 1, w: 'fill' });
  }
  return l;
};
// table: cols [{label, w (number|'grow'), num:true}], rows [[cells]], {ours: rowIndex}
K.table = async (parent, cols, rows, o = {}) => {
  const tb = K.f('V', { name: o.name || 'Table' }); K.add(parent, tb, { w: 'fill' });
  const row = async (cells, kind) => {
    const r = K.f('H', { name: kind === 'head' ? 'Header row' : 'Row' }); K.add(tb, r, { w: 'fill' });
    K.sides(r, 'b', kind === 'head' ? 'bS' : 'bD');
    for (let i = 0; i < cols.length; i++) {
      const c = K.f('V', { name: 'Cell', pad: kind === 'head' ? [12, 16] : [16, 16] });
      if (cols[i].w === 'grow' || cols[i].w === undefined) K.add(r, c, { grow: 1, w: 'fill' }); else K.add(r, c, { w: cols[i].w });
      const style = kind === 'head' ? 'UI/Label' : (cols[i].num ? 'Data/Mono' : (kind === 'ours' ? 'Body/Strong' : 'Body/SM'));
      const t = await K.t(String(cells[i]), style, kind === 'head' ? 'tS' : 'tP', { align: cols[i].num ? 'RIGHT' : 'LEFT' });
      K.add(c, t, { w: 'fill' });
    }
    if (kind === 'ours') r.fills = [K.p('cyan', 0.10)]; // set after the cells exist, or the tint can come back solid
  };
  await row(cols.map(c => c.label), 'head');
  for (let i = 0; i < rows.length; i++) await row(rows[i], o.ours === i ? 'ours' : 'body');
  return tb;
};
// N equal columns inside a container width (desktop); returns {row, colW}
K.cols = (parent, n, gap = 24, o = {}) => {
  const row = K.f('H', { name: o.name || 'Columns', gap, align: o.align || 'MIN' }); K.add(parent, row, { w: 'fill' });
  const width = o.width || K.W; const colW = Math.floor((width - gap * (n - 1)) / n);
  return { row, colW };
};
K.report = () => ({ frame: K.R && K.R.id, name: K.R && K.R.name, size: K.R && [K.R.width, Math.round(K.R.height)], images: K.images, notes: K.notes });
// ===== END PAGEKIT =====
