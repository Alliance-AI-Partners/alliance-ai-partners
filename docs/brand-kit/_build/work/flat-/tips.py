"""Thin tapered ends (crescent tips, spike and ribbon tips) that the 0.5-coverage trace cuts short.

The trace closes a thin gap where its blurred coverage stops crossing 0.5, so a tip that tapers below ~1 px ends
blunt and early. Each tip listed in TIPS is measured on the original at sub-pixel precision and the two edges that
meet at it are run on to a sharp point:
  1. per scan line (pixel rows or columns across the feature) the feature's extent and centre: the integral of its
     unclipped coverage (exact below 1 px and independent of the blur) and the centroid. Where a thin navy sliver
     runs beside the feature (P-stem spikes), a per-line least-squares fit of [cyan | sliver | spike | navy] with the
     image's measured edge-spread function instead;
  2. the true tip: extent w(s) = a*u + b*u^2 (u = distance before the tip), seen through a 1-px box and a Gaussian
     blur (both fitted), and a quadratic centre line -> tip point;
  3. each edge keeps the vector up to a junction (where it is still ~2.5 px wide and agrees with the original), is
     split there exactly, and a new cubic runs on from the junction (G1) to the tip, least-squares on the measured
     edges; the two new cubics meet at the tip as a corner.
Used by build_flat.py after the trace; `extend` returns the new path and a record per tip for fit/flat-NN.json."""
import os

import numpy as np
from PIL import Image, ImageDraw

import flatlib as F
from flatlib import kit

# per mark: tip node as the trace leaves it (x, y), what the feature is made of ('gap' = navy in cyan, 'spike' =
# cyan in navy), scan axis (0: columns, 1: rows), scan range (px behind / beyond the traced tip), window half-height H,
# flank px and sides for the baseline; bg='beyond' takes the background from the lines past the tip (stationary
# neighbours); sliver=True fits [cyan | navy sliver | spike | navy] per line. Marks 03 and 09 have no thin tapers;
# 11's ribbon/stem ends are soft cyan-to-white fades (no crisp taper), so they stay at their 0.5-coverage ends.
# Left as traced (measured short by < 3 px, extension gave no clear gain): the wide spikes where the crescent meets
# the leg's outer edge (10: 1.8 px, 12: 2.8 px, 16: 1.4 px) and 07's ribbon head (1.8 px, 66 deg corner).
TIPS = {
    '10': [dict(name='crescent', at=(173.284, 411.983), kind='gap', axis=0, back=12, fwd=24),
           dict(name='P-stem spike', at=(351.206, 360.537), kind='spike', axis=1, back=14, fwd=14, sliver=True)],
    '16': [dict(name='crescent', at=(353.417, 418.187), kind='gap', axis=0, back=16, fwd=14),
           dict(name='P-stem spike', at=(599.71, 351.933), kind='spike', axis=1, back=14, fwd=14, sliver=True)],
    '12': [dict(name='crescent', at=(331.294, 532.644), kind='gap', axis=0, back=16, fwd=14),
           dict(name='P-stem sliver', at=(616.787, 442.675), kind='gap', axis=1, back=14, fwd=16, H=3, flank=2, bg='beyond')],
    '07': [dict(name='P curl tip', at=(488.713, 400.839), kind='spike', axis=1, back=6, fwd=9, H=3, flank=2, sides='hi'),
           dict(name='ribbon tail', at=(145.621, 487.904), kind='spike', axis=1, back=16, fwd=14, H=3, flank=2)],
}

# symmetrised edge-spread function of the RGB-projection coverage (pixel-centre distance from the edge -> coverage),
# measured on the straight outer edge of mark 10's left leg; it has long chroma (4:2:0) tails
ESF_D = np.array([0.0, 0.12, 0.38, 0.62, 0.88, 1.12, 1.38, 1.62, 1.88, 2.12, 2.38, 2.62, 2.88, 3.12, 4.0])
ESF_V = np.array([0.5, 0.592, 0.760, 0.857, 0.906, 0.9355, 0.9515, 0.959, 0.970, 0.9795, 0.985, 0.986, 0.991, 0.9955, 1.0])


def esf(d):
    d = np.asarray(d, float)
    v = np.interp(np.abs(d), ESF_D, ESF_V)
    return np.where(d >= 0, v, 1 - v)


def maps(work, bg, cyan):
    """unclipped coverage of the cyan over the navy (projection on the navy -> cyan line)"""
    dv = cyan - bg
    al = ((work - bg) @ dv) / (dv @ dv)
    return {'gap': 1 - al, 'spike': al}


# ------------------------------------------------------------------ path helpers

def segs_abs(sub):
    """closed subpath -> [[P0, P3]] lines / [[P0, P1, P2, P3]] cubics as numpy points"""
    cur = np.array(sub['start'], float)
    out = []
    for g in sub['segs']:
        if g[0] == 'L':
            e = np.array(g[1:3]); out.append([cur, e])
        else:
            e = np.array(g[5:7]); out.append([cur, np.array(g[1:3]), np.array(g[3:5]), e])
        cur = e
    if np.linalg.norm(cur - np.array(sub['start'])) > 1e-6:
        out.append([cur, np.array(sub['start'], float)])
    return out


def to_sub(segs):
    return {'start': tuple(segs[0][0]), 'closed': True,
            'segs': [('L', *s[1]) if len(s) == 2 else ('C', *s[1], *s[2], *s[3]) for s in segs]}


def ev(s, t):
    t = np.atleast_1d(np.asarray(t, float))
    return s[0] + t[:, None] * (s[1] - s[0]) if len(s) == 2 else F.bez(*s, t)


def tangent(s, t):
    if len(s) == 2:
        return F.unit(s[1] - s[0])
    return F.unit(F.bez_d1(*s, [t])[0])


def split(s, t):
    """exact split of a line / cubic at parameter t -> (first part, second part)"""
    if len(s) == 2:
        m = s[0] + t * (s[1] - s[0])
        return [s[0], m], [m, s[1]]
    p0, p1, p2, p3 = s
    a, b, c = p0 + t * (p1 - p0), p1 + t * (p2 - p1), p2 + t * (p3 - p2)
    d, e = a + t * (b - a), b + t * (c - b)
    f = d + t * (e - d)
    return [p0, a, d, f], [f, e, c, p3]


def find_node(subs, xy, tol=0.6):
    """(subpath index, index of the segment ending at the node nearest xy)"""
    best = None
    for si, s in enumerate(subs):
        for k, g in enumerate(segs_abs(s)):
            dist = float(np.linalg.norm(g[-1] - np.asarray(xy)))
            if best is None or dist < best[0]:
                best = (dist, si, k)
    if best[0] > tol:
        raise ValueError('tip node %s not found (nearest %.2f px): the trace changed, update TIPS' % (xy, best[0]))
    return best[1], best[2]


def walk_cross(segs, s_line, axis, n=600):
    """first crossing of consecutive segments (ordered away from the tip, each oriented away from it) with the
    scan line coordinate s_line -> (segment order index, t along the oriented segment, point) or None"""
    for i, sg in enumerate(segs):
        t = np.linspace(0, 1, n)
        v = ev(sg, t)[:, axis] - s_line
        idx = np.nonzero(np.sign(v[:-1]) * np.sign(v[1:]) <= 0)[0]
        if len(idx):
            j = idx[0]
            lo, hi = t[j], t[j + 1]
            for _ in range(40):
                mid = 0.5 * (lo + hi)
                if np.sign(ev(sg, mid)[0, axis] - s_line) == np.sign(v[j]):
                    lo = mid
                else:
                    hi = mid
            tt = 0.5 * (lo + hi)
            return i, tt, ev(sg, tt)[0]
    return None


def reverse(sg):
    return sg[::-1]


def tip_edges(sub, k):
    """rotate a closed subpath to start at node k (end of segment k): rot[0] leaves the tip, rot[-1] arrives.
    -> rot, edge A (arriving side, segments reversed to run away from the tip), edge B (leaving side)"""
    segs = segs_abs(sub)
    rot = segs[k + 1:] + segs[:k + 1]
    return rot, [reverse(s) for s in rot[::-1]], rot


# ------------------------------------------------------------------ measurement

def _cross_near(edge, s, axis, T0, reach):
    c = walk_cross(edge[:6], s, axis)
    if c is None or np.linalg.norm(c[2] - T0) > reach:
        return None
    return c


def _row_model(x, E1, c, w):
    # w may go negative so that noise around a vanished spike averages to zero instead of biasing it up
    return (1 - esf(x - E1)) + esf(x - (c - w / 2)) - esf(x - (c + w / 2))


def _fit_row(x, v, p):
    p = np.array(p, float)
    for _ in range(40):
        r = _row_model(x, *p) - v
        J = np.zeros((len(x), 3))
        for k in range(3):
            dp = np.zeros(3); dp[k] = 1e-3
            J[:, k] = (_row_model(x, *(p + dp)) - _row_model(x, *(p - dp))) / 2e-3
        step = np.linalg.solve(J.T @ J + 1e-3 * np.eye(3), -J.T @ r)
        p += np.clip(step, -1, 1)
        if np.abs(step).max() < 1e-4:
            break
    return p


def scan(den, sub, k, f):
    """Per scan line across the feature near the tip node k: (s, extent w, centre c, vector extent, vector centre).
    s runs from `back` px behind the traced tip to `fwd` px beyond it; the perpendicular coordinate is the other axis."""
    rot, eA, eB = tip_edges(sub, k)
    T0 = rot[0][0]
    axis, back, fwd = f['axis'], f['back'], f['fwd']
    mid = 0.5 * (ev(eA[0], 1.0)[0] + ev(eB[0], 1.0)[0])
    sgn = 1 if T0[axis] - mid[axis] > 0 else -1          # the tip lies towards sgn along the scan axis
    reach = back * 1.6 + 6
    prof = (lambda li: den[:, li]) if axis == 0 else (lambda li: den[li, :])
    H, fl, sides = f.get('H', 5), f.get('flank', 4), f.get('sides', 'both')
    start = int(np.floor(T0[axis] - sgn * back))
    lines = list(range(start, int(np.floor(T0[axis] + sgn * fwd)), sgn))
    bgprof = None
    if f.get('bg') == 'beyond':   # per-pixel background from the last lines, beyond the tip (stationary along s)
        bgprof = np.median(np.stack([prof(li) for li in lines[-6:]]), 0)
    rows, cents = [], []
    p3 = None
    for li in lines:
        s = li + 0.5
        before = sgn * (s - T0[axis]) < 0
        ca = _cross_near(eA, s, axis, T0, reach) if before else None
        cb = _cross_near(eB, s, axis, T0, reach) if before else None
        if ca is not None and cb is not None:
            pa, pb = ca[2][1 - axis], cb[2][1 - axis]
            vw, vc = abs(pb - pa), 0.5 * (pa + pb)
        else:
            pa = pb = None
            vw = 0.0
            if len(cents) >= 3:
                q = np.array(cents[-4:])
                vc = float(np.polyval(np.polyfit(q[:, 0], q[:, 1], 1), s))
            else:
                continue
        pr = prof(li).astype(float)
        if bgprof is not None:
            pr = pr - bgprof
        if f.get('sliver'):
            # [cyan | navy sliver | cyan spike | navy], sliver on the low side of the perpendicular coordinate
            if p3 is None:
                E1 = _sliver_edge(sub, s, axis, min(pa, pb), T0, reach)
                p3 = [E1, vc, vw]
            i0, i1 = int(np.floor(p3[0] - 4)), int(np.ceil(p3[1] + p3[2] / 2 + 5))
            x = np.arange(i0, i1) + 0.5
            q = _fit_row(x, pr[i0:i1], p3)
            w, c = float(q[2]), float(q[1])
            # a vanished spike has no position: keep tracking from the last line where it was visible
            p3 = [float(q[0]), c, w] if w > 0.3 else [float(q[0]), p3[1], max(w, 0.3)]
        else:
            ic = int(np.floor(vc))
            i0, i1 = ic - H, ic + H
            parts = []
            if sides in ('both', 'lo'):
                parts.append(pr[i0 - fl - 1:i0 - 1])
            if sides in ('both', 'hi'):
                parts.append(pr[i1 + 2:i1 + 2 + fl])
            base = float(np.mean(np.concatenate(parts))) if parts and bgprof is None else 0.0
            seg = pr[i0:i1 + 1] - base
            pos = np.arange(i0, i1 + 1) + 0.5
            w = float(seg.sum())
            c = float((seg * pos).sum() / seg.sum()) if w > 0.05 else vc
        rows.append((s, w, c, vw, vc))
        if w > 0.4:
            cents.append((s, c))
    return dict(rows=np.array(rows), axis=axis, sgn=sgn, T0=T0)


def _sliver_edge(sub, s, axis, below, T0, reach):
    """crossing of the whole subpath with scan line s that lies just below `below` (the far side of the sliver)"""
    best = None
    for sg in segs_abs(sub):
        t = np.linspace(0, 1, 400)
        p = ev(sg, t)
        v = p[:, axis] - s
        for j in np.nonzero(np.sign(v[:-1]) * np.sign(v[1:]) <= 0)[0]:
            q = p[j] + (p[j + 1] - p[j]) * (v[j] / (v[j] - v[j + 1]) if v[j] != v[j + 1] else 0)
            o = q[1 - axis]
            if o < below - 0.3 and np.linalg.norm(q - T0) < reach and (best is None or o > best):
                best = o
    return best


# ------------------------------------------------------------------ tip fit

_FINE = np.arange(-7, 7.0001, 0.05)


def _kernel(sig):
    k = np.exp(-0.5 * (_FINE / sig) ** 2)
    k = np.convolve(k, (np.abs(_FINE) <= 0.5).astype(float), mode='same')
    return k / k.sum()


def fit_tip(m, w_max=3.6, sig_max=1.2):
    """True tip from the extent profile: w = a*u + b*u^2 (a, b >= 0, u = distance before the tip), observed through a
    1-px box and a Gaussian sigma; grid over (tip, sigma), non-negative least squares for (a, b).
    Centre line: polynomial in s (quadratic from 10 lines on, else linear) weighted by sqrt(w) on lines with w > 0.25."""
    R, sgn = m['rows'], m['sgn']
    s, w, c = R[:, 0], R[:, 1], R[:, 2]
    i0 = int(np.argmax(w < w_max))
    ss, ww = s[i0:], w[i0:]
    i_last = np.nonzero(ww > 0.3)[0][-1]
    s_last = ss[i_last]
    # constant floor w0 (residual bias of the extent estimate), fitted only when >= 4 lines past the tip pin it
    sets = ((0, 1, 2), (0, 2), (1, 2)) if len(ss) - 1 - i_last >= 4 else ((0, 1), (0,), (1,))
    best = None
    for sig in np.arange(0.3, sig_max + 1e-4, 0.05):
        k2 = _kernel(sig)
        for sT in np.arange(s_last - sgn * 2, s_last + sgn * 6, sgn * 0.05):
            A = np.array([[float((np.clip(sgn * (sT - (sv + _FINE)), 0, None) ** p * k2).sum()) for p in (1, 2)] + [1.0]
                          for sv in ss])
            for cols in sets:   # a, b >= 0
                co, *_ = np.linalg.lstsq(A[:, cols], ww, rcond=None)
                if np.any(co[[i for i, cc in enumerate(cols) if cc < 2]] < 0):
                    continue
                full = np.zeros(3); full[list(cols)] = co
                r = float(((A @ full - ww) ** 2).sum())
                if best is None or r < best[0]:
                    best = (r, sT, sig, full)
    r, sT, sig, (a, b, w0) = best
    sel = (np.arange(len(s)) >= i0) & (w > 0.25)
    pc = np.polyfit(s[sel], c[sel], 2 if sel.sum() >= 10 else 1, w=np.sqrt(w[sel]))
    cT = float(np.polyval(pc, sT))
    T = np.array([sT, cT]) if m['axis'] == 0 else np.array([cT, sT])
    return dict(sT=float(sT), sigma=float(sig), a=float(a), b=float(b), w0=float(w0), pc=pc, T=T,
                rms=float(np.sqrt(r / len(ss))), n=int(len(ss)))


# ------------------------------------------------------------------ splice

W_JUNCTION = 2.5   # keep the traced edges while the feature is at least this wide (and agrees with the original)


def splice(sub, k, m, ft):
    """Run both edges of the tip at node k on to the measured tip. The junction line s_J is the first scan line where
    the traced extent falls 0.12 px short of the original (or below W_JUNCTION). Each edge is refitted from the node
    before its junction: data = the traced curve up to s_J, then the measured edge (centre -/+ extent/2, blended in
    over 3 px) to the tip; C2 spline with the traced tangent at the kept node (G1 there), merged to few cubics. A
    straight edge stays a line and the tip slides onto its extension. -> (new subpath starting at the tip, record)"""
    rot, eA, eB = tip_edges(sub, k)
    axis, sgn, T = m['axis'], m['sgn'], ft['T']
    sJ = next((s for s, w, c, vw, vc in m['rows'] if vw > 0 and (vw < W_JUNCTION or w - vw > 0.12)), None)
    if sJ is None:
        raise ValueError('no junction line found')
    iA, tA, JA = walk_cross(eA[:6], sJ, axis)
    iB, tB, JB = walk_cross(eB[:6], sJ, axis)
    N = len(rot)
    jA = N - 1 - iA                  # rot index of the segment holding J_A
    if not iB < jA:
        raise ValueError('junctions overlap')
    line_A, line_B = len(rot[jA]) == 2, len(rot[iB]) == 2
    if line_A and line_B:
        raise ValueError('both edges straight at the junction')
    if line_A or line_B:             # a straight edge stays straight: the tip slides onto its extension
        p0, p1 = rot[jA] if line_A else rot[iB]
        T = p0 + (ft['sT'] - p0[axis]) / (p1[axis] - p0[axis]) * (p1 - p0)
    # model edges between the junction and the tip (true extent, centre line), blended from the traced edge over 3 px
    S = np.append(np.arange(sJ, ft['sT'], sgn * 0.25)[1:], ft['sT'])
    u = np.clip(sgn * (ft['sT'] - S), 0, None)
    w = ft['a'] * u + ft['b'] * u ** 2
    c = np.polyval(ft['pc'], S)
    a_lo = JA[1 - axis] < JB[1 - axis]
    beta = np.clip(sgn * (S - sJ) / 3.0, 0, 1)

    def run(edge, i, t, lo):
        """cubics from the far node of edge[i] (edge segments run away from the tip) to the tip"""
        far = split(edge[i], t)[1][::-1]                      # far node -> J
        old = F.resample(ev(far, np.linspace(0, 1, 200)), 0.25)
        o = c - w / 2 if lo else c + w / 2
        for j, sv in enumerate(S):
            if beta[j] < 1 and sgn * (sv - m['T0'][axis]) < 0:
                cr = walk_cross(edge[:6], sv, axis)
                if cr is not None:
                    o[j] = (1 - beta[j]) * cr[2][1 - axis] + beta[j] * o[j]
        new = np.stack([S, o], 1) if axis == 0 else np.stack([o, S], 1)
        q = np.vstack([old, new[:-1], T])
        bz = F.fit_cubic(q, -tangent(edge[i], 1.0), None, tol=0.08, tiny=3.0, merge_tol=0.12)  # G1 split fit
        dense = np.vstack([F.bez(*b, np.linspace(0, 1, 2000)) for b in bz])
        err = float(np.sqrt(((q[:, None, :] - dense[None]) ** 2).sum(-1).min(1)).max())
        return [list(b) for b in bz], err
    errs, ncub = [], []
    if line_A:
        endA = [[rot[jA][0], T]]
    else:
        endA, e = run(eA, iA, tA, a_lo)
        errs.append(e); ncub.append(len(endA))
    if line_B:
        startB = [[T, rot[iB][1]]]
    else:
        bz, e = run(eB, iB, tB, not a_lo)
        startB = [b[::-1] for b in bz[::-1]]
        errs.append(e); ncub.append(len(bz))
    new = startB + rot[iB + 1:jA] + endA
    rec = dict(junction_line=round(float(sJ), 2), junction_A=[round(float(v), 3) for v in JA],
               junction_B=[round(float(v), 3) for v in JB], new_tip=[round(float(v), 3) for v in T],
               straight_edge_extended='A' if line_A else ('B' if line_B else None),
               refit_from_nodes=[[round(float(v), 3) for v in rot[jA][0]], [round(float(v), 3) for v in rot[iB][-1]]],
               new_cubics=ncub, fit_err_px=[round(e, 3) for e in errs])
    return to_sub(new), rec


def counts(d):
    subs = kit.parse_d(d)
    n = sum(len(s['segs']) for s in subs)
    nl = sum(1 for s in subs for g in s['segs'] if g[0] == 'L')
    return {'subpaths': len(subs), 'anchors': n, 'line_segs': nl, 'curve_segs': n - nl}


def extend(oid, d, mp):
    """Run every tip listed for this mark on to its measured point. -> (new d, [record per tip])"""
    recs = []
    for f in TIPS.get(oid, []):
        subs = kit.parse_d(d)
        si, k = find_node(subs, f['at'])
        m = scan(mp[f['kind']], subs[si], k, f)
        ft = fit_tip(m)
        subs[si], rec = splice(subs[si], k, m, ft)
        d = kit.format_d(subs, 3)
        T0 = m['T0']
        ax = m['axis']
        recs.append(dict(name=f['name'], kind=f['kind'], scan='columns' if ax == 0 else 'rows',
                         vector_tip_before=[round(float(v), 3) for v in T0],
                         measured_tip=[round(float(v), 3) for v in ft['T']],
                         extension_px=round(float(np.linalg.norm(np.array(rec['new_tip']) - T0)), 2),
                         taper=dict(a=round(ft['a'], 4), b=round(ft['b'], 5), blur_sigma=round(ft['sigma'], 2),
                                    floor=round(ft['w0'], 3), rms_px=round(ft['rms'], 4), lines=ft['n']),
                         **rec))
    return d, recs


# ------------------------------------------------------------------ verification

def report(recs, svg_after, d_before, d_after, orig, r_after, rm_after, meas, bg_meas, mo, excl, cov_o, out_png):
    """Before/after for every extended tip, on VectorCraft renders: mark IoU (0.5 masks, wordmark box excluded) and,
    in a crop around each tip, mean dE2000 (palette render and measured-colour render) and mean |coverage error|.
    Writes out_png: per tip original | before | after | original with before (blue) / after (red) outlines."""
    svg_before = svg_after.replace(d_after, d_before)
    tmp = os.path.join(F.WORK, '_tips_before.svg')

    def rend(svg, cmap=None, bg=F.NAVY_HEX):
        for k, v in (cmap or {}).items():
            svg = svg.replace('fill="%s"' % k, 'fill="%s"' % v)
        with open(tmp, 'w', encoding='utf-8') as fh:
            fh.write(svg)
        return F.render_rgb(tmp, bg)
    r_before = rend(svg_before)
    rm_before = rend(svg_before, meas, bg_meas)
    os.remove(tmp)
    H, W = mo.shape
    keep = np.ones((H, W), bool)
    if excl:
        x0, y0, x1, y1 = excl
        keep[max(0, y0):y1, max(0, x0):x1] = False
    covs = {k: F.cov2(r, F.NAVY, F.CYAN) for k, r in (('before', r_before), ('after', r_after))}
    out = {k: round(kit.iou(mo & keep, (cv > 0.5) & keep), 4) for k, cv in covs.items()}
    de = {k: kit.de2000(kit.srgb_to_lab(orig), kit.srgb_to_lab(r)) for k, r in
          (('before', r_before), ('after', r_after), ('m_before', rm_before), ('m_after', rm_after))}
    rows = []
    for rec in recs:
        pts = np.array([rec['junction_A'], rec['junction_B'], rec['vector_tip_before'], rec['new_tip']])
        bx = [int(np.floor(pts[:, 0].min())) - 6, int(np.floor(pts[:, 1].min())) - 6,
              int(np.ceil(pts[:, 0].max())) + 7, int(np.ceil(pts[:, 1].max())) + 7]
        x0, y0, x1, y1 = max(0, bx[0]), max(0, bx[1]), min(W, bx[2]), min(H, bx[3])
        sl = (slice(y0, y1), slice(x0, x1))
        cm = {}
        for k in ('before', 'after'):
            cm[k] = dict(de_mean=round(float(de[k][sl].mean()), 3),
                         de_mean_measured_colours=round(float(de['m_' + k][sl].mean()), 3),
                         coverage_abs_err_mean=round(float(np.abs(cov_o[sl] - covs[k][sl]).mean()), 4),
                         iou=round(kit.iou(mo[sl], covs[k][sl] > 0.5), 4))
        rec['crop'] = [x0, y0, x1, y1]
        rec['crop_metrics'] = cm
        rows.append(_panel(rec, orig, r_before, r_after, d_before, d_after, (x0, y0, x1, y1)))
    sheet = Image.new('RGB', (max(r.width for r in rows), sum(r.height for r in rows)), 'white')
    y = 0
    for r in rows:
        sheet.paste(r, (0, y)); y += r.height
    sheet.save(out_png)
    out['tips'] = recs
    return out


def _panel(rec, orig, r_before, r_after, d_before, d_after, box):
    x0, y0, x1, y1 = box
    z = int(np.clip(300 // max(x1 - x0, y1 - y0), 3, 12))

    def crop(a):
        im = Image.fromarray(np.clip(np.round(a), 0, 255).astype(np.uint8)).crop(box)
        return im.resize((im.width * z, im.height * z), Image.NEAREST)
    ims = [crop(orig), crop(r_before), crop(r_after), crop(orig)]
    dr = ImageDraw.Draw(ims[3])
    T = lambda p: ((p[0] - x0) * z, (p[1] - y0) * z)
    for d, col in ((d_before, (60, 140, 255)), (d_after, (255, 40, 40))):
        for s in kit.parse_d(d):
            poly = kit.flatten([s], tol=0.02)[0]
            dr.line([T(p) for p in poly + [poly[0]]], fill=col, width=1)
    w = sum(i.width for i in ims) + 8 * 3
    cm = rec['crop_metrics']
    lab = ('%s: tip (%.2f, %.2f) -> (%.2f, %.2f), +%.1f px | crop dE %.2f -> %.2f (measured colours %.2f -> %.2f) | '
           'original | before | after | outlines blue=before red=after' % (
               rec['name'], *rec['vector_tip_before'], *rec['new_tip'], rec['extension_px'],
               cm['before']['de_mean'], cm['after']['de_mean'],
               cm['before']['de_mean_measured_colours'], cm['after']['de_mean_measured_colours']))
    cell = Image.new('RGB', (max(w, 8 + 6 * len(lab)), ims[0].height + 22), 'white')
    ImageDraw.Draw(cell).text((4, 5), lab, fill='black')
    x = 0
    for im in ims:
        cell.paste(im, (x, 22)); x += im.width + 8
    return cell
