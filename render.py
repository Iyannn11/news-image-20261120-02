#!/usr/bin/env python3
"""Render the round-2 front page for Friday 20 November 2026.

A clean typographic front page drawn programmatically with Pillow, so
every letter is real text - no AI image generation, no smeared type.
What round 2 adds over round 1: every story gets a small drawn
pictogram (criterion 3: each story clear from its picture), the lead
gets a two-column layout with a schematic Dnipro + three-bridges
diagram, and ALSO TODAY becomes three mini-cards with icons instead
of one run-on footer sentence. Body type is slightly larger and
summaries are trimmed to one crisp line, so the page still reads at
~300 pixels across.

Deterministic: same input always produces the same bytes.
Run: python3 render.py  ->  entry.png (1024x1024, < 1 MiB)
"""
import hashlib
import os

from PIL import Image, ImageDraw, ImageFont

W = H = 1024
MARGIN = 36
CONTENT_W = W - 2 * MARGIN

# ---- palette ---------------------------------------------------------
PAPER = (250, 246, 236)
NAVY = (12, 35, 64)
NAVY_DARK = (8, 26, 48)
RED = (192, 57, 43)
RED_SOFT = (226, 93, 74)
GOLD = (201, 162, 39)
INK = (24, 24, 24)
GREY = (96, 96, 96)
LINE = (200, 192, 172)
CARD = (255, 255, 255)
BLUE = (31, 93, 160)
BLUE_SOFT = (214, 231, 247)
GREEN = (39, 120, 74)
ORANGE = (214, 106, 24)
TEAL = (18, 130, 122)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
SERIF_B = os.path.join(FONT_DIR, "DejaVuSerif-Bold.ttf")
SANS_B = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
SANS = os.path.join(FONT_DIR, "DejaVuSans.ttf")


def font(path, size):
    return ImageFont.truetype(path, size)


F_TITLE = font(SERIF_B, 58)
F_DATE = font(SANS_B, 26)
F_KICKER = font(SANS_B, 15)
F_HEAD = font(SANS_B, 27)
F_HEAD_SM = font(SANS_B, 19)
F_HEAD_GRID = font(SANS_B, 18)
F_BODY = font(SANS, 16)
F_BODY_SM = font(SANS, 14)
F_LABEL = font(SANS_B, 13)
F_FOOT = font(SANS, 13)
F_CAPTION = font(SANS_B, 12)


def wrap(draw, text, fnt, max_w):
    """Wrap text into lines that fit max_w pixels."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text_block(draw, x, y, lines, fnt, fill, leading=None):
    """Draw lines of text; return y after the last line."""
    if leading is None:
        leading = int(fnt.size * 1.28)
    for ln in lines:
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += leading
    return y


def rounded_card(draw, box, fill=CARD, outline=LINE, width=1):
    draw.rounded_rectangle(box, radius=10, fill=fill, outline=outline, width=width)


# ---- pictograms (all drawn shapes, no images) ------------------------

def icon_plane(draw, cx, cy, s, color=BLUE):
    # Paper-plane dart, nose to the right.
    draw.polygon([(cx - s * 0.5, cy - s * 0.28), (cx + s * 0.5, cy),
                  (cx - s * 0.5, cy + s * 0.28), (cx - s * 0.12, cy)],
                 fill=color)
    draw.line([(cx - s * 0.5, cy - s * 0.28), (cx - s * 0.12, cy)],
              fill=(255, 255, 255), width=2)


def icon_flame(draw, cx, cy, s, color=ORANGE):
    # Flame silhouette: outer orange teardrop, inner yellow core.
    outer = [(cx - s * 0.34, cy + s * 0.38), (cx - s * 0.42, cy + s * 0.02),
             (cx - s * 0.2, cy - s * 0.18), (cx - s * 0.02, cy - s * 0.5),
             (cx + s * 0.16, cy - s * 0.14), (cx + s * 0.42, cy + s * 0.08),
             (cx + s * 0.36, cy + s * 0.38), (cx, cy + s * 0.46)]
    draw.polygon(outer, fill=color)
    inner = [(cx - s * 0.16, cy + s * 0.3), (cx - s * 0.2, cy + s * 0.02),
             (cx, cy - s * 0.22), (cx + s * 0.18, cy + s * 0.02),
             (cx + s * 0.16, cy + s * 0.3), (cx, cy + s * 0.36)]
    draw.polygon(inner, fill=(255, 210, 63))


def icon_fence(draw, cx, cy, s, color=NAVY):
    # Border fence: vertical bars + two rails.
    w = s
    draw.rectangle([cx - w // 2, cy - s * 0.28, cx + w // 2, cy - s * 0.14],
                   fill=color)
    draw.rectangle([cx - w // 2, cy + s * 0.14, cx + w // 2, cy + s * 0.28],
                   fill=color)
    for i in range(5):
        x = cx - w // 2 + i * (w // 4)
        draw.rectangle([x - 2, cy - s * 0.42, x + 2, cy + s * 0.42], fill=color)


def icon_shield(draw, cx, cy, s, color=TEAL):
    pts = [(cx, cy - s // 2), (cx + s // 2, cy - s // 4),
           (cx + s // 2, cy + s // 6), (cx, cy + s // 2),
           (cx - s // 2, cy + s // 6), (cx - s // 2, cy - s // 4)]
    draw.polygon(pts, fill=color)
    draw.text((cx, cy - s // 6), "!", font=font(SANS_B, int(s * 0.42)),
              fill=(255, 255, 255), anchor="mm")


def icon_pin(draw, cx, cy, s, color=RED):
    # Map pin with a dashed yellow line under it.
    draw.ellipse([cx - s * 0.32, cy - s * 0.5, cx + s * 0.32, cy + s * 0.15],
                 fill=color)
    draw.polygon([(cx - s * 0.32, cy), (cx + s * 0.32, cy), (cx, cy + s * 0.5)],
                 fill=color)
    draw.ellipse([cx - s * 0.13, cy - s * 0.32, cx + s * 0.13, cy - s * 0.06],
                 fill=(255, 255, 255))


def icon_bars(draw, cx, cy, s, color=RED):
    # Falling bars: heights descend left to right.
    heights = [0.42, 0.34, 0.24, 0.14]
    bw = s // 6
    for i, h in enumerate(heights):
        x0 = cx - s // 2 + i * (bw + 4)
        y0 = cy + s // 2 - int(s * h)
        draw.rectangle([x0, y0, x0 + bw, cy + s // 2], fill=color)
    draw.line([(cx - s // 2, cy + s // 2), (cx + s // 2, cy + s // 2)],
              fill=INK, width=2)


def icon_globe(draw, cx, cy, s, color=GREEN):
    draw.ellipse([cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2],
                 outline=color, width=3)
    draw.ellipse([cx - s // 4, cy - s // 2, cx + s // 4, cy + s // 2],
                 outline=color, width=2)
    draw.line([(cx - s // 2, cy), (cx + s // 2, cy)], fill=color, width=2)


def icon_cross(draw, cx, cy, s, color=RED):
    draw.ellipse([cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2],
                 fill=(255, 255, 255), outline=color, width=3)
    draw.rectangle([cx - s * 0.1, cy - s * 0.3, cx + s * 0.1, cy + s * 0.3],
                   fill=color)
    draw.rectangle([cx - s * 0.3, cy - s * 0.1, cx + s * 0.3, cy + s * 0.1],
                   fill=color)


def icon_spiral(draw, cx, cy, s, color=BLUE):
    # Cyclone: three concentric arcs, shrinking.
    for i, r in enumerate([s // 2, s // 3, s // 5]):
        draw.arc([cx - r, cy - r, cx + r, cy + r],
                 start=20 + i * 40, end=320 + i * 20, fill=color, width=3)


def icon_rocket(draw, cx, cy, s, color=NAVY):
    draw.polygon([(cx, cy - s // 2), (cx + s * 0.22, cy + s * 0.1),
                  (cx - s * 0.22, cy + s * 0.1)], fill=color)
    draw.ellipse([cx - s * 0.09, cy - s * 0.12, cx + s * 0.09, cy + s * 0.06],
                 fill=(255, 255, 255))
    draw.polygon([(cx - s * 0.22, cy + s * 0.05), (cx - s * 0.38, cy + s * 0.3),
                  (cx - s * 0.1, cy + s * 0.22)], fill=RED)
    draw.polygon([(cx + s * 0.22, cy + s * 0.05), (cx + s * 0.38, cy + s * 0.3),
                  (cx + s * 0.1, cy + s * 0.22)], fill=RED)
    draw.polygon([(cx - s * 0.1, cy + s * 0.22), (cx + s * 0.1, cy + s * 0.22),
                  (cx, cy + s * 0.5)], fill=ORANGE)


def icon_arrow_up(draw, cx, cy, s, color=GREEN):
    draw.ellipse([cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2],
                 fill=(255, 255, 255), outline=color, width=3)
    draw.polygon([(cx, cy - s * 0.32), (cx + s * 0.28, cy),
                  (cx + s * 0.1, cy), (cx + s * 0.1, cy + s * 0.32),
                  (cx - s * 0.1, cy + s * 0.32), (cx - s * 0.1, cy),
                  (cx - s * 0.28, cy)], fill=color)


def blast_star(draw, cx, cy, r, color=RED):
    """Small 8-point blast marker."""
    pts = []
    import math
    for i in range(16):
        ang = math.pi * i / 8
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    draw.polygon(pts, fill=color)


def draw_lead_diagram(draw, x, y, w, h):
    """Schematic of the Dnipro river in Kyiv with three bridges.

    A vertical blue river band, three bridge decks crossing it, red
    blast markers on two decks, labels KYIV and DNIPRO RIVER.
    """
    rounded_card(draw, (x, y, x + w, y + h), fill=BLUE_SOFT, outline=LINE)
    # River: vertical wavy band down the middle.
    import math
    river_pts = []
    for yy in range(y + 8, y + h - 8, 8):
        off = int(10 * math.sin((yy - y) / 40.0))
        river_pts.append((x + w // 2 - 34 + off, yy))
    for yy in range(y + h - 8, y + 8, -8):
        off = int(10 * math.sin((yy - y) / 40.0))
        river_pts.append((x + w // 2 + 34 + off, yy))
    draw.polygon(river_pts, fill=(64, 140, 210))
    # City label on the left bank.
    draw.text((x + 14, y + 12), "KYIV", font=F_LABEL, fill=NAVY)
    draw.text((x + 14, y + 30), "west bank", font=F_FOOT, fill=GREY)
    # Three bridges.
    for i, by in enumerate([y + h * 0.28, y + h * 0.52, y + h * 0.76]):
        by = int(by)
        draw.rectangle([x + 16, by - 4, x + w - 16, by + 4], fill=(255, 255, 255),
                       outline=NAVY, width=1)
        draw.text((x + w - 62, by - 20), f"BRIDGE {i + 1}", font=F_CAPTION,
                  fill=NAVY)
    # Blast markers on bridges 1 and 3.
    blast_star(draw, x + w // 2 + 6, int(y + h * 0.28), 13)
    blast_star(draw, x + w // 2 - 8, int(y + h * 0.76), 13)
    draw.text((x + 14, y + h - 26), "DNIPRO RIVER", font=F_CAPTION, fill=NAVY)


# ---- page ------------------------------------------------------------

def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # Masthead.
    d.rectangle([0, 0, W, 118], fill=NAVY)
    d.text((W // 2, 14), "THE WORLD IN ONE DAY", font=F_TITLE, fill=(255, 255, 255),
           anchor="ma")
    d.text((W // 2, 76), "FRIDAY, 20 NOVEMBER 2026", font=F_DATE, fill=(255, 214, 90),
           anchor="ma")
    d.rectangle([MARGIN, 122, W - MARGIN, 126], fill=GOLD)

    # ---- Lead: two columns ------------------------------------------
    lead_y = 140
    lead_h = 224
    lead_w = 560
    diag_x = MARGIN + lead_w + 16
    diag_w = W - MARGIN - diag_x

    d.text((MARGIN, lead_y), "UKRAINE WAR  ·  LEAD", font=F_KICKER, fill=RED)
    y = lead_y + 26
    y = text_block(d, MARGIN, y,
                   wrap(d, "Russian strikes hit three Kyiv bridges", F_HEAD, lead_w),
                   F_HEAD, INK)
    y += 6
    y = text_block(d, MARGIN, y,
                   wrap(d, "Overnight missiles targeted bridges across the Dnipro in Kyiv. "
                           "Eight people were killed and 28 injured in attacks across nine "
                           "regions; a strike on a railway station in Lviv killed two more.",
                        F_BODY, lead_w),
                   F_BODY, INK)
    # Key figures strip under the lead text.
    fig_y = lead_y + lead_h - 34
    d.rectangle([MARGIN, fig_y, MARGIN + lead_w, fig_y + 30], fill=NAVY_DARK)
    d.text((MARGIN + 12, fig_y + 6), "8 KILLED  ·  28 INJURED  ·  3 BRIDGES HIT",
           font=F_LABEL, fill=(255, 255, 255))
    draw_lead_diagram(d, diag_x, lead_y, diag_w, lead_h)

    # ---- Row 2: two half-width cards ---------------------------------
    half_y = 380
    half_h = 122
    half_w = (CONTENT_W - 16) // 2

    def half_card(x, icon_fn, kicker, head, body, icon_color):
        rounded_card(d, (x, half_y, x + half_w, half_y + half_h))
        icon_fn(d, x + 34, half_y + 34, 46, icon_color)
        tx = x + 66
        d.text((tx, half_y + 12), kicker, font=F_KICKER, fill=RED)
        head_lines = wrap(d, head, F_HEAD_SM, half_w - 82)
        y = text_block(d, tx, half_y + 34, head_lines, F_HEAD_SM, INK)
        text_block(d, tx, y + 4,
                   wrap(d, body, F_BODY_SM, half_w - 82), F_BODY_SM, INK)

    half_card(MARGIN, icon_plane, "EUROPE",
              "Russia violates Polish airspace",
              "Three objects overnight — said to be two missiles and a drone.",
              BLUE)
    half_card(MARGIN + half_w + 16, icon_flame, "MIDDLE EAST",
              "Riyadh tower hit; tanker fire",
              "Houthi missiles damage the PIF tower; a tanker burns in Hormuz.",
              ORANGE)

    # ---- Row 3: 3x2 grid of story cards ------------------------------
    grid_y = 518
    grid_h = 118
    grid_gap = 12
    col_w = (CONTENT_W - 2 * grid_gap) // 3

    def grid_card(col, row, icon_fn, kicker, head, body, icon_color):
        x = MARGIN + col * (col_w + grid_gap)
        y = grid_y + row * (grid_h + grid_gap)
        rounded_card(d, (x, y, x + col_w, y + grid_h))
        icon_fn(d, x + 30, y + 30, 40, icon_color)
        tx = x + 58
        d.text((tx, y + 10), kicker, font=F_KICKER, fill=RED)
        head_lines = wrap(d, head, F_HEAD_GRID, col_w - 72)
        y2 = text_block(d, tx, y + 30, head_lines, F_HEAD_GRID, INK)
        text_block(d, tx, y2 + 4,
                   wrap(d, body, F_BODY_SM, col_w - 72), F_BODY_SM, INK)

    grid_card(0, 0, icon_fence, "EUROPE", "Estonia closes border",
              "Border with Russia shut for at least six months.", NAVY)
    grid_card(1, 0, icon_shield, "IRAQ", "Iraq moves on militia",
              "Forces deploy in Jurf al-Sakhar, limiting Kataib Hezbollah.",
              TEAL)
    grid_card(2, 0, icon_pin, "GAZA", "Troops cross the line",
              "First incursion across the ceasefire line since the truce.", RED)
    grid_card(0, 1, icon_bars, "MARKETS", "Stocks fall, fifth day",
              "S&P 500 −2%; Nikkei −4.8%; gold −4.2%.", RED)
    grid_card(1, 1, icon_globe, "CLIMATE · COP31", "Draft drops fuel exit",
              "Antalya draft omits any fossil-fuel phase-out reference.",
              GREEN)
    grid_card(2, 1, icon_cross, "AFRICA", "Last Ebola patient out",
              "Discharged 37 days after the first case; 42-day countdown.",
              RED)

    # ---- ALSO TODAY: three mini-cards ---------------------------------
    also_y = 786
    also_h = 104
    mini_w = (CONTENT_W - 2 * grid_gap) // 3

    d.text((MARGIN, also_y), "ALSO TODAY", font=F_KICKER, fill=NAVY)
    also_y += 24

    def mini_card(col, icon_fn, head, body, icon_color):
        x = MARGIN + col * (mini_w + grid_gap)
        rounded_card(d, (x, also_y, x + mini_w, also_y + also_h))
        icon_fn(d, x + 28, also_y + 30, 38, icon_color)
        tx = x + 54
        head_lines = wrap(d, head, F_HEAD_SM, mini_w - 66)
        y2 = text_block(d, tx, also_y + 12, head_lines, F_HEAD_SM, INK)
        text_block(d, tx, y2 + 4,
                   wrap(d, body, F_BODY_SM, mini_w - 66), F_BODY_SM, INK)

    mini_card(0, icon_spiral, "Cyclone Akvan",
              "Makes landfall in Odisha, India.", BLUE)
    mini_card(1, icon_rocket, "BepiColombo",
              "Reaches Mercury after eight years.", NAVY)
    mini_card(2, icon_arrow_up, "Anthropic IPO",
              "Closes 17% above its IPO price.", GREEN)

    # ---- Footer -------------------------------------------------------
    foot_y = 924
    d.rectangle([MARGIN, foot_y, W - MARGIN, foot_y + 1], fill=LINE)
    d.text((MARGIN, foot_y + 10),
           "Sources: One Turn · Just Security (Early Edition) · Reuters · BBC — 20 Nov 2026",
           font=F_FOOT, fill=GREY)
    d.text((W - MARGIN, foot_y + 10), "THE WORLD IN ONE DAY",
           font=F_FOOT, fill=GREY, anchor="ra")

    return img


def main():
    img = build()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    img.save(out, "PNG", optimize=True)
    data = open(out, "rb").read()
    print(f"entry.png: {len(data)} bytes, sha256 {hashlib.sha256(data).hexdigest()}")


if __name__ == "__main__":
    main()
