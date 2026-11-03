const L = {};
L.BANNED = ['leverage', 'seamless', 'cutting-edge', 'revolutionary', 'game-changing', 'disrupt', 'supercharge', 'unleash', 'unlock', '10x', 'synergy', 'magic', 'ninja', 'guru', 'rockstar', 'hustle', 'alpha', 'cheapest', 'best rate', 'a fraction of the cost', 'top 1%', 'get started', 'learn more', 'welcome to', 'elevate', 'next-gen', 'empower'];
L.FIGURE = /(US\$|A\$|NZ\$|£|€|\$)\s?\d|\d+(\.\d+)?\s?%|\b\d{1,3}(,\d{3})+\b|\b\d+(\.\d+)?\s?(billion|million)\b/i;
L.SMALL = ['UI/Caption', 'UI/Label', 'UI/Tag', 'Data/Mono', 'Body/SM'];
L.BIG = ['Display/XL', 'Display/LG', 'Heading/1', 'Heading/2', 'Heading/3'];
L.run = async (rootId, opts) => {
  opts = opts || {};
  const R = await figma.getNodeByIdAsync(rootId);
  const RB = R.absoluteBoundingBox;
  const styles = Object.fromEntries((await figma.getLocalTextStylesAsync()).map(s => [s.id, s.name]));
  const out = [];
  const add = (sev, kind, node, msg) => { if (out.length < (opts.max || 80)) out.push({ sev, kind, section: sectionName(node), node: node.id, msg }); };
  const sectionOf = n => { let p = n; while (p.parent && p.parent.id !== R.id) p = p.parent; return p; };
  const sectionName = n => { const s = sectionOf(n); return s ? s.name : ''; };
  const inInstance = n => { let p = n.parent; while (p && p.id !== R.id) { if (p.type === 'INSTANCE') return p; p = p.parent; } return null; };
  const mains = new Map();
  for (const n of R.findAllWithCriteria({ types: ['INSTANCE'] })) { try { mains.set(n.id, await n.getMainComponentAsync()); } catch (e) { mains.set(n.id, null); } }
  const isNavy = n => {
    let p = n;
    while (p && p.id !== R.parent.id) {
      const m = p.explicitVariableModes || {};
      if (Object.values(m).includes('3:3')) return true;
      const mc = p.type === 'INSTANCE' ? mains.get(p.id) : null;
      if (mc) { const mm = mc.explicitVariableModes || {}; const pm = (mc.parent && mc.parent.explicitVariableModes) || {}; if (Object.values(mm).includes('3:3') || Object.values(pm).includes('3:3')) return true; }
      p = p.parent;
    }
    return false;
  };
  const texts = R.findAll(n => n.type === 'TEXT');
  const sectionsWithSources = new Set();
  for (const s of R.children) {
    if (s.findOne && s.findOne(n => n.name === 'Sources' || (n.type === 'INSTANCE' && n.name === 'Source key'))) sectionsWithSources.add(s.id);
  }
  const placeholders = new Set();
  for (const t of texts) {
    const str = t.characters; const low = str.toLowerCase();
    const inst = inInstance(t);
    for (const w of L.BANNED) { const re = new RegExp('(^|[^a-z])' + w.replace(/[.*+?^$(){}|[\]\\]/g, '\\$&') + '([^a-z]|$)', 'i'); if (re.test(low)) add('high', 'banned-word', t, '"' + w + '" in: ' + str.slice(0, 80)); }
    (str.match(/\[[^\]]{1,40}\]/g) || []).forEach(p => placeholders.add(p));
    if (/["]/.test(str) || /(^|\s)'|'(\s|$)|\w'\w/.test(str)) add('polish', 'straight-quote', t, str.slice(0, 80));
    if (str.includes('...')) add('polish', 'three-dots', t, str.slice(0, 80));
    if (!inst && /\bAlliance\b(?! AI Partners| Blue)/.test(str)) add('high', 'short-name', t, 'write the full name Alliance AI Partners: ' + str.slice(0, 80));
    const stripped = str.replace(/\[[^\]]*\]/g, '');
    if (L.FIGURE.test(stripped)) { const s = sectionOf(t); if (s && !sectionsWithSources.has(s.id)) add('high', 'unsourced-figure', t, str.slice(0, 100)); }
    if (typeof t.fontSize === 'number' && t.fontSize < 12) add('medium', 'tiny-text', t, t.fontSize + 'px: ' + str.slice(0, 40));
    const bb = t.absoluteBoundingBox;
    if (bb && (bb.x < RB.x - 1 || bb.x + bb.width > RB.x + RB.width + 1)) add('high', 'text-outside-frame', t, str.slice(0, 60));
    let segs = [];
    try { segs = t.getStyledTextSegments(['textStyleId', 'fills']); } catch (e) {}
    const acc = segs.filter(s => (styles[s.textStyleId] || '').endsWith(' Accent'));
    if (acc.length > 1) add('medium', 'accent-count', t, acc.length + ' accent ranges: ' + str.slice(0, 60));
    for (const a of acc) { const words = a.characters.trim().split(/\s+/).filter(Boolean); if (words.length > 1) add('medium', 'accent-words', t, '"' + a.characters.trim() + '"'); }
    if (!isNavy(t)) {
      for (const s of segs) for (const f of (s.fills || [])) {
        const bv = f.boundVariables && f.boundVariables.color && f.boundVariables.color.id;
        const c = f.color || {};
        if (bv === 'VariableID:3:59' || bv === 'VariableID:3:7' || (c.r < 0.05 && c.g > 0.78 && c.b > 0.95)) add('high', 'cyan-text-on-light', t, str.slice(0, 60));
      }
    }
  }
  // labels above headings: a small-style text directly before a big heading in the same auto-layout parent
  for (const t of texts) {
    if (inInstance(t)) continue;
    const st = styles[t.textStyleId] || '';
    if (!L.BIG.includes(st)) continue;
    const p = t.parent; if (!p || !('layoutMode' in p) || p.layoutMode !== 'VERTICAL') continue;
    const i = p.children.indexOf(t);
    const prev = i > 0 ? p.children[i - 1] : null;
    if (prev && prev.type === 'TEXT' && L.SMALL.includes(styles[prev.textStyleId] || '')) add('high', 'label-above-heading', t, '"' + prev.characters.slice(0, 40) + '" above "' + t.characters.slice(0, 40) + '"');
  }
  // collapsed frames
  for (const f of R.findAll(n => n.type === 'FRAME' && 'children' in n && n.children.length > 0)) {
    if (inInstance(f)) continue;
    if (f.height < 2 || f.width < 2) add('high', 'collapsed-frame', f, f.name + ' ' + Math.round(f.width) + 'x' + Math.round(f.height));
  }
  // solid Ribbon Cyan fills on a light ground (only a 10% tint is allowed there)
  for (const f of R.findAll(n => n.type !== 'TEXT' && 'fills' in n && Array.isArray(n.fills) && n.fills.length)) {
    if (inInstance(f) || isNavy(f)) continue;
    for (const p of f.fills) { const bv = p.boundVariables && p.boundVariables.color && p.boundVariables.color.id; if ((bv === 'VariableID:3:7' || bv === 'VariableID:3:59') && (p.opacity === undefined || p.opacity > 0.25)) add('high', 'solid-cyan-on-light', f, f.name + ' opacity ' + (p.opacity === undefined ? 1 : p.opacity)); }
  }
  // primary buttons per screenful
  const view = R.width > 600 ? 900 : 800;
  const insts = R.findAllWithCriteria({ types: ['INSTANCE'] });
  const prims = insts.filter(n => { const mc = mains.get(n.id); return mc && mc.name.startsWith('Variant=Primary'); }).map(b => ({ b, y: b.absoluteBoundingBox.y - RB.y })).sort((a, b) => a.y - b.y);
  for (let i = 1; i < prims.length; i++) if (prims[i].y - prims[i - 1].y < view) add('high', 'two-primaries', prims[i].b, 'Primary at y ' + Math.round(prims[i - 1].y) + ' and ' + Math.round(prims[i].y));
  // image slot names
  const slots = insts.filter(n => { const mc = mains.get(n.id); return mc && mc.parent && mc.parent.name === 'Image slot'; });
  for (const s of slots) if (!/^IMG-\d{2}-\d+[a-z]? · /.test(s.name)) add('medium', 'slot-name', s, s.name);
  // scrims over images: at least 82% Partner Navy under every line of real text (slot labels and buttons excluded)
  const alphaAt = (st, x) => { x = Math.max(0, Math.min(1, x)); if (x <= st[0].position) return st[0].color.a; for (let i = 1; i < st.length; i++) { const a = st[i - 1], b = st[i]; if (x <= b.position) return a.color.a + (b.color.a - a.color.a) * (x - a.position) / Math.max(1e-6, b.position - a.position); } return st[st.length - 1].color.a; };
  const skipT = (n, root) => { let p = n.parent; while (p && p !== root) { if (p.type === 'INSTANCE' && (/^Button/.test(p.name) || /^IMG-\d\d-\d+[a-z]? · /.test(p.name))) return true; p = p.parent; } return false; };
  for (const sc of R.findAll(n => /scrim/i.test(n.name) && 'fills' in n && Array.isArray(n.fills) && n.fills.some(p => p.type === 'GRADIENT_LINEAR'))) {
    const g = sc.fills.find(p => p.type === 'GRADIENT_LINEAR'), m = g.gradientTransform, po = g.opacity === undefined ? 1 : g.opacity, SB = sc.absoluteBoundingBox;
    let worst = 1;
    for (const t of sc.parent.findAll(x => x.type === 'TEXT' && x.visible !== false)) {
      if (skipT(t, sc.parent)) continue; const B = t.absoluteBoundingBox; if (!B) continue;
      if (B.x > SB.x + SB.width || B.x + B.width < SB.x || B.y > SB.y + SB.height || B.y + B.height < SB.y) continue;
      for (const [x, y] of [[B.x, B.y], [B.x + B.width, B.y], [B.x, B.y + B.height], [B.x + B.width, B.y + B.height]]) worst = Math.min(worst, alphaAt(g.gradientStops, m[0][0] * (x - SB.x) / SB.width + m[0][1] * (y - SB.y) / SB.height + m[0][2]) * po);
    }
    if (worst < 0.8) add('high', 'weak-scrim', sc, sc.name + ' is ' + Math.round(worst * 100) + '% navy under some text; hold 82% or more under every line');
  }
  // headings: count Display/XL (one statement per page)
  const xl = texts.filter(t => styles[t.textStyleId] === 'Display/XL' && !inInstance(t));
  if (xl.length > 1) add('medium', 'display-xl-count', xl[1], xl.length + ' Display/XL texts');
  return { frame: R.name, size: [Math.round(R.width), Math.round(R.height)], sections: R.children.map(c => c.name), primaries: prims.map(p => Math.round(p.y)), slots: slots.map(s => s.name), placeholders: [...placeholders], findings: out };
};
