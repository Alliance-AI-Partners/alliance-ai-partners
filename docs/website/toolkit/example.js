// Example: patterns taken from the finished Home page build. Copy the code patterns, not the copy: every promise on a page must come from the Brand DNA.
// Every script: loader, init, page, then sections. Return K.report() (frame id, size, image slots, notes).
const K = (new Function('figma', (await figma.getNodeByIdAsync('24:3')).characters + '\nreturn K;'))(figma);
await K.init('Desktop');                       // 'Mobile' for the 390 frame
await K.page('07 · Embedded developers');
if (K.P.children.some(n => n.name === 'Embedded developers — Desktop')) return { skipped: 'exists' };   // retry-safe
const R = K.root('Embedded developers — Desktop', 0);   // mobile: K.root('<Page> — Mobile', 1600)
K.header(R, 'Services');

// HERO, split text | image (or text | vector mark). Never centred.
{
  const { c } = K.section(R, 'Hero', { padTop: 96, padBottom: 128 });          // mobile: { padTop: 48, padBottom: 72, gap: 28 } and stack
  const row = K.f('H', { name: 'Hero grid', gap: 64, align: 'CENTER' }); K.add(c, row, { w: 'fill' });
  const text = K.f('V', { name: 'Text', gap: 32 }); K.add(row, text, { w: 652 });   // 1.08fr of 1320
  K.add(text, await K.t('An extra developer, without the hiring.', 'Display/XL', 'tP', { accent: 'hiring.', name: 'Title' }));
  K.add(text, await K.t('A developer from our team joins yours full time, works on your tools and your hours, and costs [PRICE] a month.', 'Body/LG', 'tS', { name: 'Lead' }), { w: 560 });
  const a = K.f('H', { name: 'Actions', gap: 24, align: 'CENTER' }); K.add(text, a);
  K.add(a, K.btn('See where AI can help', { size: 'LG' }));          // the page's one Primary
  K.add(a, K.link('Compare the costs'));                             // underlined link with arrow
  K.add(row, K.img('IMG-07-1', 'Two ribbons joining', 'New: two satin ribbons weaving into one band over faceted hills', 604, 560), { grow: 1 });
}

// SECTION HEAD + BENTO (one large card, two stacked). No row of three identical cards.
{
  const { c } = K.section(R, 'What you get', { gap: 48 });
  await K.head(c, 'Part of your team from week one.', 'Same tools, same stand-ups, same standards. You manage the work; we handle recruiting, benefits and equipment.', { accent: 'team' });
  const grid = K.f('H', { name: 'Bento', gap: 24, align: 'MIN' }); K.add(c, grid, { w: 'fill' });
  const big = await K.card({ name: 'Card · Fits your process', gap: 20, pad: 0 }); K.add(grid, big, { w: 648 });
  K.add(big, K.img('IMG-07-2', 'Weekly update', 'Existing: brand-kit/emails/previews/monthly-report-desktop.png', 648, 340, { radius: 0 }), { w: 'fill' });
  const body = K.f('V', { name: 'Body', gap: 16, pad: [8, 32, 32, 32] }); K.add(big, body, { w: 'fill' });
  K.add(body, await K.t('You see progress every week', 'Heading/3', 'tP'));
  K.add(body, await K.t('A short written update every week: what shipped, what is next, what needs you.', 'Body/Default', 'tS'));
  const right = K.f('V', { name: 'Right column', gap: 24 }); K.add(grid, right, { grow: 1, w: 'fill' });
  for (const [icon, title, line] of [['security-governance', 'Your code, your accounts', 'Work happens in your systems wherever possible. You own what we build.'], ['training-enablement', 'Reviewed by a person', 'A person reviews every piece of work before it reaches you.']]) {
    const cd = await K.card({ name: 'Card · ' + title, gap: 16 }); K.add(right, cd, { w: 'fill' });
    K.add(cd, await K.svc(icon, 40));                                  // service icon (mono on light; K.svc(name, 40, true) on navy)
    K.add(cd, await K.t(title, 'Heading/3', 'tP'));
    K.add(cd, await K.t(line, 'Body/Default', 'tS'));
  }
}

// NAVY CHAPTER with a list (check icons, hairlines) and service rows
{
  const { c } = K.section(R, 'Pricing', { ground: 'navy', gap: 56 });
  await K.head(c, 'One price, no hiring costs.', 'You don’t pay for recruiting, benefits or equipment.', { style: 'Heading/1' });
  const row = K.f('H', { name: 'Two columns', gap: 64, align: 'MIN' }); K.add(c, row, { w: 'fill' });
  const list = K.f('V', { name: 'Included' }); K.add(row, list, { w: 560 });
  for (const p of ['Recruiting', 'Benefits', 'Equipment']) {
    const r = K.f('H', { name: 'Item', gap: 16, align: 'MIN', pad: [16, 0] }); K.add(list, r, { w: 'fill' }); K.sides(r, 'b');
    K.add(r, await K.icon('check', 20, 'accent')); K.add(r, await K.t(p, 'Body/Default', 'tP'), { grow: 1, w: 'fill' });
  }
  const rows = K.f('V', { name: 'Prices' }); K.add(row, rows, { grow: 1, w: 'fill' });
  K.add(rows, K.inst('svcRow', { Title: 'Embedded developer', Text: 'Full time, on your hours.', Price: 'From [PRICE] a month' }), { w: 'fill' });
  K.add(rows, K.btn('See all prices', { variant: 'Secondary', icon: true }));
}

// SOURCED STATS: Stat instances + Source keys + a numbered source list
{
  const { c } = K.section(R, 'Cost of hiring', { gap: 48 });
  const stats = K.f('H', { name: 'Stats', gap: 0, align: 'MIN' }); K.add(c, stats, { w: 'fill' }); K.sides(stats, 'tb');
  const keyProp = K.key('key', 'Key');
  for (const [i, [v, cap]] of [['US$196,500', 'A year in the United States: median pay of US$135,980 plus benefits.']].entries()) {
    const cell = K.f('V', { name: 'Stat cell', pad: [32, 32] }); K.add(stats, cell, { grow: 1, w: 'fill' }); if (i) K.sides(cell, 'l');
    const st = K.inst('stat', { Value: v, Caption: cap }); K.add(cell, st, { w: 'fill' });
    st.findOne(n => n.type === 'INSTANCE' && n.name === 'Source key').setProperties({ [keyProp]: String(i + 1) });
  }
  await K.sources(c, ['U.S. Bureau of Labor Statistics, software developers, median pay, May 2025; benefits are 30.8% of compensation for professional workers (June 2026). Retrieved 2026-11-02.']);
}

// TABLE (comparison). ours = the index of Alliance's own row (tinted)
{
  const { c } = K.section(R, 'Compare', { gap: 32 });
  await K.table(c, [{ label: 'Option', w: 'grow' }, { label: 'Cost per month', w: 240, num: true }, { label: 'Notice', w: 200 }], [['Hire locally (US)', 'About US$16,400', 'Months to hire'], ['Alliance AI Partners', '[PRICE]', '[30] days']], { ours: 1 });
}

// FULL-BLEED BAND with image + navy scrim + text (a Navy chapter, no container)
{
  const { s } = K.section(R, 'Band', { ground: 'navy', bleed: true });
  const band = figma.createFrame(); band.name = 'Band'; band.fills = []; band.clipsContent = true; K.add(s, band, { w: 'fill' }); band.layoutSizingVertical = 'FIXED'; band.resize(1440, 600);
  const img = K.img('IMG-07-3', 'Dawn wave', 'Existing: design-system/imagery/backgrounds/dawn-wave.webp', 1440, 600, { tone: 'Navy', radius: 0 }); band.appendChild(img); img.x = 0; img.y = 0;
  const scrim = figma.createRectangle(); scrim.name = 'Scrim'; band.appendChild(scrim); scrim.resize(1440, 600);
  scrim.fills = [{ type: 'GRADIENT_LINEAR', gradientTransform: [[1, 0, 0], [0, 1, 0]], gradientStops: [{ position: 0, color: { r: 0.071, g: 0.106, b: 0.165, a: 0.82 } }, { position: 0.6, color: { r: 0.071, g: 0.106, b: 0.165, a: 0 } }] }];
  // scrim from the top instead: gradientTransform [[0, 1, 0], [-1, 0, 1]]
  const tx = K.f('V', { name: 'Text', gap: 24 }); band.appendChild(tx); tx.x = 60; tx.y = 160;
  const h = await K.t('Start with one developer.', 'Display/LG', 'tP', { name: 'Title' }); K.add(tx, h); h.layoutSizingHorizontal = 'FIXED'; h.resize(760, h.height); h.textAutoResize = 'HEIGHT';
  K.add(tx, K.btn('See where AI can help', { size: 'LG' }));      // allowed: the hero Primary is out of view
}

// ACCORDION (FAQ) and FORM FIELDS
{
  const { c } = K.section(R, 'Questions', { gap: 32 });
  const acc = K.f('V', { name: 'Accordion' }); K.add(c, acc, { w: 'fill' }); K.sides(acc, 't');
  const a = K.inst('acc', { Question: 'Who manages the developer?', Answer: 'You do, day to day.' }, 'State=Open'); K.add(acc, a, { w: 'fill' });
  a.findOne(n => n.type === 'TEXT' && n.name === 'answer').layoutSizingHorizontal = 'FILL';
  const form = K.f('V', { name: 'Form', gap: 24 }); K.add(c, form, { w: 560 });
  const f1 = K.inst('field', { Label: 'Work email', Help: 'We reply to this address.' }, 'State=Default'); K.add(form, f1, { w: 'fill' });
  f1.findOne(n => n.type === 'TEXT' && n.name === 'value').characters = 'name@company.com';      // placeholder or value text
  K.add(form, K.inst('select', { Label: 'Where is your team?' }, 'State=Default'), { w: 'fill' });
  K.add(form, K.inst('textarea', { Label: 'What slows your team down?' }, 'State=Default'), { w: 'fill' });
  K.add(form, K.inst('checkbox', { Label: 'Send me the monthly AI notes' }, 'State=Unchecked'));
  K.add(form, K.btn('Book your AI check-up', { size: 'LG' }));
  K.add(c, K.inst('alert', { Title: 'Your AI check-up is booked', Body: 'We sent the details to your email.' }, 'Type=Success'), { w: 560 });
}

// OTHER COMPONENTS: K.inst('steps'), K.inst('tz'), K.inst('article', {Title, Meta}), K.inst('person', {Name:'[Name]', Role:'[Role]'}),
// K.inst('job', {Title, Meta}), K.inst('download', {Name, Meta}), K.inst('chip', {Label:'Team online'}, 'Status=Live'), K.inst('tag', {Label}),
// K.logo('logoL'|'logoD'|'markL'|'markD', heightPx) (never add shadows to a logo), K.sets.swallow.createInstance(), K.rule(width).
// Icons: await K.icon('arrow-right', 20, 'tS') — names in K.I. Service icons: await K.svc('automation', 40) — names in K.SI.
// Colour names for K.t / K.p: tP tS tT link accent onA pageS raised sunken bSub bD bS cyan (cyan only on navy or as 10% tint).
K.footer(R);
return K.report();
