#!/usr/bin/env python3
"""Build entry.png — a newspaper front page summing up 24 November 2026.

Reads news.json next to this script and paints a 1024x1024 PNG: a
masthead, one lead story and five more stories, each with a small
hand-drawn geometric icon, plus a sources footer.

The layout is measured before it is drawn: every headline and summary
is wrapped first, each block's height is computed from its wrapped
lines, and only then is anything painted, so text can never overlap.
The script is fully deterministic (no network, no clock, no random
input) — two runs produce a byte-identical PNG.
"""

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent

W, H = 1024, 1024
MARGIN = 48
CW = W - 2 * MARGIN
BOTTOM_LIMIT = 984

PAPER = (251, 247, 239)
INK = (22, 22, 22)
BODY = (60, 58, 52)
MUTED = (96, 92, 84)
LIGHT_RULE = (205, 198, 184)

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")

# --- vertical rhythm (pixels) -------------------------------------------
GAP_KICKER_MASTHEAD = 8
GAP_MASTHEAD_RULE = 10
GAP_RULE_DATE = 8
GAP_HEADER_LEAD = 18
GAP_LEAD_DIVIDER = 16
GAP_STORY = 18
GAP_STORIES_FOOTER = 20
LEAD_ICON = 168
STORY_ICON = 72
LEAD_ICON_TEXT_GAP = 24
STORY_ICON_TEXT_GAP = 16


def load_font(name, size):
    try:
        return ImageFont.truetype(str(FONT_DIR / name), size)
    except OSError:
        return ImageFont.load_default(size)


def line_height(f):
    asc, desc = f.getmetrics()
    return asc + desc


def wrap_lines(f, text, max_w):
    """Greedy word wrap measured with the real font; never splits words."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if f.getlength(trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def tint(color, amount=0.88):
    """Mix a story colour towards white for the icon tile background."""
    return tuple(int(c + (255 - c) * amount) for c in color)


def shade(color, delta):
    return tuple(max(0, min(255, c + delta)) for c in color)


# --- geometric icons (drawn from scratch, centred on cx, cy) ------------
def _icon_chart(d, cx, cy, s, color):
    base = cy + s * 0.42
    bw = s * 0.17
    for i, frac in enumerate((0.34, 0.58, 0.86)):
        x0 = cx - s * 0.42 + i * s * 0.30
        d.rectangle([x0, base - s * frac, x0 + bw, base], fill=color)
    p0 = (cx - s * 0.42, base - s * 0.30)
    p1 = (cx - s * 0.12, base - s * 0.55)
    p2 = (cx + s * 0.42, base - s * 0.88)
    d.line([p0, p1, p2], fill=color, width=max(3, int(s * 0.055)), joint="curve")
    d.polygon(
        [(p2[0], p2[1]), (p2[0] - s * 0.17, p2[1] + s * 0.02),
         (p2[0] - s * 0.02, p2[1] + s * 0.17)],
        fill=color,
    )


def _icon_summit(d, cx, cy, s, color):
    d.polygon(
        [(cx - s * 0.48, cy + s * 0.40), (cx - s * 0.08, cy - s * 0.42),
         (cx + s * 0.30, cy + s * 0.40)],
        fill=color,
    )
    d.polygon(
        [(cx - s * 0.05, cy + s * 0.40), (cx + s * 0.28, cy - s * 0.18),
         (cx + s * 0.48, cy + s * 0.40)],
        fill=shade(color, 45),
    )
    d.polygon(
        [(cx - s * 0.20, cy - s * 0.18), (cx - s * 0.08, cy - s * 0.42),
         (cx + s * 0.04, cy - s * 0.18)],
        fill=(255, 255, 255),
    )


def _icon_burst(d, cx, cy, s, color):
    pts = []
    for i in range(24):
        ang = math.pi * i / 12
        r = s * 0.48 if i % 2 == 0 else s * 0.20
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    d.polygon(pts, fill=color)
    r = s * 0.10
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255))


def _icon_globe(d, cx, cy, s, color):
    r = s * 0.44
    w = max(3, int(s * 0.05))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=w)
    d.ellipse(
        [cx - r * 0.45, cy - r, cx + r * 0.45, cy + r],
        outline=color, width=max(2, w - 1),
    )
    d.line([(cx - r, cy), (cx + r, cy)], fill=color, width=max(2, w - 1))


def _icon_senate(d, cx, cy, s, color):
    d.polygon(
        [(cx - s * 0.46, cy - s * 0.10), (cx, cy - s * 0.44),
         (cx + s * 0.46, cy - s * 0.10)],
        fill=color,
    )
    cw = s * 0.11
    for i in (-1, 0, 1):
        x0 = cx + i * s * 0.30 - cw / 2
        d.rectangle([x0, cy - s * 0.06, x0 + cw, cy + s * 0.30], fill=color)
    d.rectangle(
        [cx - s * 0.48, cy + s * 0.32, cx + s * 0.48, cy + s * 0.42],
        fill=color,
    )


def _icon_crown(d, cx, cy, s, color):
    d.polygon(
        [
            (cx - s * 0.46, cy + s * 0.34),
            (cx - s * 0.46, cy - s * 0.22),
            (cx - s * 0.20, cy + s * 0.02),
            (cx, cy - s * 0.40),
            (cx + s * 0.20, cy + s * 0.02),
            (cx + s * 0.46, cy - s * 0.22),
            (cx + s * 0.46, cy + s * 0.34),
        ],
        fill=color,
    )
    d.rectangle(
        [cx - s * 0.46, cy + s * 0.34, cx + s * 0.46, cy + s * 0.44],
        fill=color,
    )
    for tx, ty in ((-s * 0.46, -s * 0.22), (0.0, -s * 0.40), (s * 0.46, -s * 0.22)):
        r = s * 0.055
        d.ellipse(
            [cx + tx - r, cy + ty - r, cx + tx + r, cy + ty + r], fill=color
        )


def paint_icon(d, kind, cx, cy, size, color):
    fn = {
        "chart": _icon_chart,
        "summit": _icon_summit,
        "burst": _icon_burst,
        "globe": _icon_globe,
        "senate": _icon_senate,
        "crown": _icon_crown,
    }.get(kind)
    if fn is None:
        r = size * 0.40
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
        return
    fn(d, cx, cy, size, color)


# --- painting helpers -----------------------------------------------------
def paint_lines(d, x, y, lines, f, fill, leading):
    """Draw wrapped lines left-aligned (anchor 'la'); return bottom y."""
    lh = line_height(f)
    for ln in lines:
        d.text((x, y), ln, font=f, fill=fill, anchor="la")
        y += lh + leading
    return y - leading


def paint_lines_centered(d, y, lines, f, fill, leading):
    lh = line_height(f)
    for ln in lines:
        d.text((W / 2, y), ln, font=f, fill=fill, anchor="ma")
        y += lh + leading
    return y - leading


def block_height(n_lines, f, leading):
    return n_lines * line_height(f) + max(0, n_lines - 1) * leading


# --- measure pass ---------------------------------------------------------
def measure(data, ft):
    plan = {}
    y = MARGIN
    plan["kicker_y"] = y
    y += line_height(ft["kicker"]) + GAP_KICKER_MASTHEAD
    plan["masthead_y"] = y
    y += line_height(ft["masthead"]) + GAP_MASTHEAD_RULE
    plan["rule_y"] = y
    y += 7 + GAP_RULE_DATE  # 3px rule + 1px rule 5px below
    plan["date_y"] = y
    y += line_height(ft["date"]) + GAP_HEADER_LEAD
    plan["header_bottom"] = y

    lead = data["stories"][0]
    lead_w = CW - LEAD_ICON - LEAD_ICON_TEXT_GAP
    lead_head = wrap_lines(ft["lead_head"], lead["headline"], lead_w)
    lead_sum = wrap_lines(ft["lead_sum"], lead["summary"], lead_w)
    lead_text_h = (
        line_height(ft["lead_tag"])
        + 8
        + block_height(len(lead_head), ft["lead_head"], 4)
        + 10
        + block_height(len(lead_sum), ft["lead_sum"], 4)
    )
    lead_h = max(LEAD_ICON, lead_text_h)
    plan["lead"] = {"y": y, "h": lead_h, "head": lead_head, "sum": lead_sum}
    y += lead_h + GAP_LEAD_DIVIDER
    plan["divider_y"] = y
    y += 2 + GAP_STORY

    rows = []
    for story in data["stories"][1:]:
        text_w = CW - STORY_ICON - STORY_ICON_TEXT_GAP
        head = wrap_lines(ft["head"], story["headline"], text_w)
        summ = wrap_lines(ft["sum"], story["summary"], text_w)
        text_h = (
            line_height(ft["tag"])
            + 5
            + block_height(len(head), ft["head"], 3)
            + 6
            + block_height(len(summ), ft["sum"], 3)
        )
        row_h = max(STORY_ICON, text_h)
        rows.append({"y": y, "h": row_h, "head": head, "sum": summ})
        y += row_h + GAP_STORY
    y -= GAP_STORY
    y += GAP_STORIES_FOOTER
    plan["rows"] = rows

    plan["footer_rule_y"] = y
    y += 1 + 8
    foot_lines = wrap_lines(ft["foot"], data["footer"], CW)
    plan["footer_lines"] = foot_lines
    y += block_height(len(foot_lines), ft["foot"], 2)
    plan["content_end"] = y
    return plan


# --- draw pass ------------------------------------------------------------
def draw(data, ft, plan):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([24, 24, W - 25, H - 25], outline=INK, width=2)

    d.text((W / 2, plan["kicker_y"]), data["kicker"], font=ft["kicker"],
           fill=MUTED, anchor="ma")
    d.text((W / 2, plan["masthead_y"]), data["title"], font=ft["masthead"],
           fill=INK, anchor="ma")
    ry = plan["rule_y"]
    d.line([(MARGIN, ry), (W - MARGIN, ry)], fill=INK, width=3)
    d.line([(MARGIN, ry + 5), (W - MARGIN, ry + 5)], fill=INK, width=1)
    d.text((W / 2, plan["date_y"]), data["date_line"], font=ft["date"],
           fill=INK, anchor="ma")

    lead = data["stories"][0]
    color = tuple(lead["color"])
    ly = plan["lead"]["y"]
    tx = MARGIN
    d.rectangle([tx, ly + 2, tx + 12, ly + 14], fill=color)
    d.text((tx + 20, ly), lead["tag"], font=ft["lead_tag"], fill=color,
           anchor="la")
    hy = ly + line_height(ft["lead_tag"]) + 8
    hy = paint_lines(d, tx, hy, plan["lead"]["head"], ft["lead_head"], INK, 4)
    hy += 10
    paint_lines(d, tx, hy, plan["lead"]["sum"], ft["lead_sum"], BODY, 4)
    ix = W - MARGIN - LEAD_ICON
    d.rectangle([ix, ly, ix + LEAD_ICON, ly + LEAD_ICON], fill=tint(color))
    paint_icon(d, lead["icon"], ix + LEAD_ICON / 2, ly + LEAD_ICON / 2,
               LEAD_ICON * 0.72, color)

    dy = plan["divider_y"]
    d.line([(MARGIN, dy), (W - MARGIN, dy)], fill=INK, width=2)

    for i, (story, row) in enumerate(zip(data["stories"][1:], plan["rows"])):
        color = tuple(story["color"])
        ry = row["y"]
        d.rectangle([MARGIN, ry, MARGIN + STORY_ICON, ry + STORY_ICON],
                    fill=tint(color))
        paint_icon(d, story["icon"], MARGIN + STORY_ICON / 2,
                   ry + STORY_ICON / 2, STORY_ICON * 0.66, color)
        tx = MARGIN + STORY_ICON + STORY_ICON_TEXT_GAP
        d.rectangle([tx, ry + 1, tx + 10, ry + 11], fill=color)
        d.text((tx + 16, ry), story["tag"], font=ft["tag"], fill=color,
               anchor="la")
        hy = ry + line_height(ft["tag"]) + 5
        hy = paint_lines(d, tx, hy, row["head"], ft["head"], INK, 3)
        hy += 6
        paint_lines(d, tx, hy, row["sum"], ft["sum"], BODY, 3)
        if i < len(plan["rows"]) - 1:
            mid = ry + row["h"] + GAP_STORY // 2
            d.line([(MARGIN, mid), (W - MARGIN, mid)], fill=LIGHT_RULE, width=1)

    fy = plan["footer_rule_y"]
    d.line([(MARGIN, fy), (W - MARGIN, fy)], fill=INK, width=1)
    paint_lines_centered(d, fy + 1 + 8, plan["footer_lines"], ft["foot"],
                         MUTED, 2)
    return img


def load_data():
    with open(HERE / "news.json", encoding="utf-8") as fh:
        return json.load(fh)


def main():
    ft = {
        "kicker": load_font("DejaVuSans-Bold.ttf", 15),
        "masthead": load_font("DejaVuSerif-Bold.ttf", 64),
        "date": load_font("DejaVuSans.ttf", 17),
        "lead_tag": load_font("DejaVuSans-Bold.ttf", 16),
        "lead_head": load_font("DejaVuSerif-Bold.ttf", 34),
        "lead_sum": load_font("DejaVuSans.ttf", 21),
        "tag": load_font("DejaVuSans-Bold.ttf", 14),
        "head": load_font("DejaVuSerif-Bold.ttf", 23),
        "sum": load_font("DejaVuSans.ttf", 18),
        "foot": load_font("DejaVuSans.ttf", 13),
    }
    data = load_data()
    plan = measure(data, ft)
    print(
        "layout: header_bottom=%d lead_h=%d rows=%s content_end=%d "
        "(limit %d)"
        % (
            plan["header_bottom"],
            plan["lead"]["h"],
            [r["h"] for r in plan["rows"]],
            plan["content_end"],
            BOTTOM_LIMIT,
        )
    )
    if plan["content_end"] > BOTTOM_LIMIT:
        raise SystemExit(
            "layout overflow: content ends at y=%d, limit is %d"
            % (plan["content_end"], BOTTOM_LIMIT)
        )
    img = draw(data, ft, plan)
    out = HERE / "entry.png"
    img.save(out, format="PNG")
    print("saved %s (%d bytes)" % (out, out.stat().st_size))


if __name__ == "__main__":
    main()
