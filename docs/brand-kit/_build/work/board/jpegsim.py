"""JPEG 4:2:0 chroma model of original 02 (quality 100, all quantisers 1, 2x2 chroma subsampling), used to
recover the true colour of thin features whose chroma the subsampling diluted (board agent).

encode: JFIF YCbCr, chroma averaged over 2x2 blocks (libjpeg h2v2_downsample);
decode: libjpeg 'fancy' triangle upsampling (9/3/3/1 weights), back to RGB. Luma is untouched (q=1)."""
import numpy as np

M = np.array([[0.299, 0.587, 0.114], [-0.168736, -0.331264, 0.5], [0.5, -0.418688, -0.081312]])
Minv = np.linalg.inv(M)


def to_ycc(rgb):
    return rgb @ M.T


def to_rgb(ycc):
    return ycc @ Minv.T


def down2(c):
    H, W = c.shape
    c = np.pad(c, ((0, H % 2), (0, W % 2)), mode='edge')
    return c.reshape(c.shape[0] // 2, 2, c.shape[1] // 2, 2).mean((1, 3))


def up2_fancy(s, H, W):
    """libjpeg h2v2 fancy upsampling: output pixel = (9*near + 3*horiz + 3*vert + 1*diag) / 16."""
    p = np.pad(s, 1, mode='edge')
    h, w = s.shape
    out = np.zeros((2 * h, 2 * w))
    c = p[1:-1, 1:-1]
    for dy, oy in ((-1, 0), (1, 1)):
        for dx, ox in ((-1, 0), (1, 1)):
            v = p[1 + dy:1 + dy + h, 1:-1]          # vertical neighbour
            hz = p[1:-1, 1 + dx:1 + dx + w]         # horizontal neighbour
            dg = p[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
            out[oy::2, ox::2] = (9 * c + 3 * hz + 3 * v + dg) / 16
    return out[:H, :W]


def jpeg420(rgb, x0=0, y0=0, clip=True):
    """Apply the chroma subsampling round trip to an RGB float image whose top-left pixel sits at
    (x0, y0) in the original (so the 2x2 blocks align with the original's). The decoder clamps to 0..255."""
    rgb = np.asarray(rgb, float)
    px, py = x0 % 2, y0 % 2
    rgb = np.pad(rgb, ((py, 0), (px, 0), (0, 0)), mode='edge')
    ycc = to_ycc(rgb)
    H, W = ycc.shape[:2]
    out = ycc.copy()
    for k in (1, 2):
        out[..., k] = up2_fancy(down2(ycc[..., k]), H, W)
    res = to_rgb(out)[py:, px:]
    return np.clip(res, 0, 255) if clip else res


def fit_ink(cov, orig, bg, x0, y0, mask=None):
    """Least-squares ink c such that jpeg420(bg + cov*(c - bg)) matches orig (over mask). Linear in c."""
    cov = np.asarray(cov, float)
    base = jpeg420(np.broadcast_to(bg, cov.shape + (3,)), x0, y0, clip=False)
    B = []
    for k in range(3):
        e = np.zeros(3); e[k] = 1.0
        B.append(jpeg420(bg + cov[..., None] * e, x0, y0, clip=False) - base)
    m = np.ones(cov.shape, bool) if mask is None else mask
    orig = np.asarray(orig, float)
    w = np.repeat(m[..., None], 3, -1)
    d = np.zeros(3)
    for _ in range(4):      # drop samples the decoder clamped (prediction outside 0..255 with orig at the rail)
        A = np.stack([b[w] for b in B], 1)
        y = (orig - base)[w]
        d, *_ = np.linalg.lstsq(A, y, rcond=None)
        pred = base + sum(d[k] * B[k] for k in range(3))
        w = np.repeat(m[..., None], 3, -1) & ~(((pred > 255) & (orig >= 254)) | ((pred < 0) & (orig <= 1)))
    return bg + d


if __name__ == '__main__':
    # self-check against a real libjpeg round trip (quality 100, 4:2:0)
    import io
    from PIL import Image
    rng = np.random.default_rng(1)
    img = np.full((40, 60, 3), 245.0)
    img[10:13, 5:50] = [27, 86, 255]
    img[20:22, 7:44] = [200, 60, 60]
    img[25:35, 30:33] = [0, 213, 255]
    buf = io.BytesIO()
    Image.fromarray(img.astype(np.uint8)).save(buf, 'JPEG', quality=100, subsampling=2)
    real = np.asarray(Image.open(buf).convert('RGB'), float)
    sim = jpeg420(img)
    err = np.abs(real - sim)
    print('sim vs libjpeg: mean abs %.3f  max %.2f' % (err.mean(), err.max()))
    assert err.mean() < 1.0 and err.max() < 12, 'jpeg420 model disagrees with libjpeg'
    print('ok')
