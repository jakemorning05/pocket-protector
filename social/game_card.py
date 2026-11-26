"""Share image (1200x630) for one game page: the matchup, the model's pick and win chance, and the score once it's final.

Built by gamepages.py for every game, so a link to a game page previews with that game's own card on X, iMessage and
elsewhere. Pure Pillow with fonts bundled in assets/fonts (subset Inter, OFL), so it runs the same in the GitHub Action.
The output is byte-for-byte stable for the same inputs, so unchanged games don't show up as changed files in git.
"""
import datetime, io, os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
FONT = lambda name, size: ImageFont.truetype(os.path.join(ROOT, 'assets', 'fonts', name + '.otf'), size)
W, H, PAD = 1200, 630, 64
BG, SURF, LINE = '#0D1120', '#161C34', '#353F6B'
INK, INK2, MUTED = '#F2F4FF', '#B9C1DF', '#828BB0'
ACCENT, ON_ACCENT, AWAY, HOME, MINT, PINK = '#FFD23F', '#191304', '#3987e5', '#d95926', '#3DDC97', '#FF5D8F'
_logo = None


def win_tag(p):
    return 'Strong' if p >= 0.75 else 'Solid' if p >= 0.65 else 'Lean' if p >= 0.55 else 'Toss-up'


def fmt_line(a, h, m):
    if m is None: return ''
    v = round(abs(m) * 2) / 2
    if v < 0.25: return "Pick'em"
    return f"{h if m > 0 else a} −{v:g}"


def fit(draw, text, name, size, max_w, min_size=40):
    while size > min_size and draw.textlength(text, font=FONT(name, size)) > max_w:
        size -= 2
    return FONT(name, size)


def pill(draw, x, y, text, font, fill, ink, border=None, right=False, padx=18, h=48):
    w = draw.textlength(text, font=font) + 2 * padx
    if right: x -= w
    draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=fill, outline=border, width=2 if border else 0)
    draw.text((x + padx, y + h / 2), text, font=font, fill=ink, anchor='lm')
    return x + w


def make_card(g, nick, pick_p=None):
    """g: a game from site_data.json; nick: team -> nickname; pick_p: home win chance locked at kickoff, if any."""
    global _logo
    a, h = g['a'], g['h']
    done = g.get('hs') is not None and g.get('as') is not None
    p = pick_p if pick_p is not None else g['p']
    pick = h if p >= 0.5 else a
    conf = max(p, 1 - p)
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    # brand row
    if _logo is None:
        _logo = Image.open(os.path.join(ROOT, 'docs', 'apple-touch-icon.png')).convert('RGBA').resize((56, 56), Image.LANCZOS)
    im.paste(_logo, (PAD, 44), _logo)
    f_brand = FONT('InterDisplay-Black', 36)
    d.text((PAD + 72, 72), 'Pocket', font=f_brand, fill=INK, anchor='lm')
    d.text((PAD + 72 + d.textlength('Pocket ', font=f_brand), 72), 'Protector', font=f_brand, fill=ACCENT, anchor='lm')
    day = datetime.date.fromisoformat(g['day'])
    when = f"WEEK {g['wk']} · {day.strftime('%a %b').upper()} {day.day}"
    pill(d, W - PAD, 48, when, FONT('Inter-Bold', 22), SURF, INK2, border=LINE, right=True)
    # headline
    if done:
        win_t, lose_t = (h, a) if g['hs'] > g['as'] else (a, h)
        ws, ls = max(g['hs'], g['as']), min(g['hs'], g['as'])
        head = f"{nick(win_t)} {ws}, {nick(lose_t)} {ls}" if ws != ls else f"{nick(a)} {g['as']}, {nick(h)} {g['hs']}"
    else:
        head = f"{nick(a)} at {nick(h)}"
    f_head = fit(d, head, 'InterDisplay-Black', 92, W - 2 * PAD)
    d.text((PAD, 205), head, font=f_head, fill=INK, anchor='ls')
    # subline
    f_sub = FONT('Inter-SemiBold', 30)
    if done:
        right = (g['hs'] > g['as']) == (p >= 0.5) if g['hs'] != g['as'] else None
        x = PAD
        d.text((x, 262), 'Final · Model picked ', font=f_sub, fill=INK2, anchor='ls')
        x += d.textlength('Final · Model picked ', font=f_sub)
        t = f"{pick} ({round(conf * 100)}%)"
        d.text((x, 262), t, font=FONT('Inter-Bold', 30), fill=INK, anchor='ls')
        x += d.textlength(t + '  ', font=FONT('Inter-Bold', 30))
        if right is not None:
            d.text((x, 262), '✓ Right' if right else '✗ Wrong', font=FONT('Inter-Bold', 30), fill=MINT if right else PINK, anchor='ls')
    else:
        hh, mm = map(int, (g.get('time') or '13:00').split(':'))
        kick = f"{day.strftime('%A')} {(hh % 12) or 12}{':%02d' % mm if mm else ''} {'AM' if hh < 12 else 'PM'} ET"
        qbs = f" · {g['qa']} vs {g['qh']}" if g.get('qa') and g.get('qh') else ''
        sub = kick + qbs
        d.text((PAD, 262), sub, font=fit(d, sub, 'Inter-SemiBold', 30, W - 2 * PAD, 22), fill=INK2, anchor='ls')
    # win-chance bar (the model's chance before kickoff)
    f_lab = FONT('Inter-Bold', 34)
    y0 = 330
    d.text((PAD, y0), f"{a} {round((1 - p) * 100)}%", font=f_lab, fill=INK, anchor='lt')
    d.text((W - PAD, y0), f"{round(p * 100)}% {h}", font=f_lab, fill=INK, anchor='rt')
    by, bh, gap = y0 + 58, 26, 6
    split = PAD + (W - 2 * PAD) * (1 - p)
    d.rounded_rectangle([PAD, by, max(PAD + bh, split - gap / 2), by + bh], radius=bh // 2, fill=AWAY)
    d.rounded_rectangle([min(W - PAD - bh, split + gap / 2), by, W - PAD, by + bh], radius=bh // 2, fill=HOME)
    d.text((PAD, by + bh + 16), 'Model win chance' + (' before kickoff' if done else ''), font=FONT('Inter-SemiBold', 22), fill=MUTED, anchor='lt')
    # bottom row
    yb = 520
    if done:
        x = pill(d, PAD, yb, f"Model {fmt_line(a, h, g.get('m'))}", FONT('Inter-Bold', 26), SURF, INK, border=LINE, h=56)
        if g.get('mk_spread') is not None:
            pill(d, x + 14, yb, f"Market {fmt_line(a, h, g['mk_spread'])}", FONT('Inter-Bold', 26), SURF, INK2, border=LINE, h=56)
    else:
        x = pill(d, PAD, yb, f"Model pick {pick} · {round(conf * 100)}% · {win_tag(conf)}", FONT('Inter-Bold', 26), ACCENT, ON_ACCENT, h=56)
        pill(d, x + 14, yb, f"Line {fmt_line(a, h, g.get('m'))} · total {round(g['tot'] * 2) / 2:g}", FONT('Inter-Bold', 26), SURF, INK, border=LINE, h=56)
    buf = io.BytesIO()
    # 64-color palette: looks the same on these flat cards and cuts the file to ~18 KB
    im.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(buf, 'PNG', optimize=True)
    return buf.getvalue()


def write_if_changed(path, data):
    try:
        if open(path, 'rb').read() == data: return False
    except FileNotFoundError:
        pass
    open(path, 'wb').write(data)
    return True
