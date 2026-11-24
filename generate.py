#!/usr/bin/env python3
"""Paint the front page for Tuesday 24 November 2026 from news.json.

The six verified stories of the day live in news.json beside this file.
This script turns them into a 1024x1024 newspaper front page (entry.png)
with Pillow alone -- no network, no random numbers, so running it twice
gives byte-identical output.

Layout happens in two passes. First `lay_out` wraps every headline and
summary with the real fonts and stacks the page into blocks, each block
knowing its own exact height. `shrink_to_fit` then drops the body sizes
a point at a time until the stack fits the height budget. Only after
the stack fits does `Painter` walk it and draw anything, so text can
never overlap and nothing can run off the bottom of the page.

Run from anywhere: `python3 generate.py` writes entry.png beside it.
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent

# Page geometry.
SIDE = 1024
MARGIN = 46
WIDTH = SIDE - 2 * MARGIN
TOP_PAD = 20
BOTTOM_PAD = 20
HEIGHT_LIMIT = 1000  # blocks plus pads must stay under this

# Colours.
PAPER = (253, 251, 245)
INK = (18, 18, 18)
GREY = (112, 110, 106)
FAINT = (205, 200, 188)

FONTS = {
    "serif": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "plain": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
}

START_SIZES = {
    "kicker": 19,
    "masthead": 60,
    "date": 25,
    "lead_head": 40,
    "lead_sum": 24,
    "head": 27,
    "summary": 22,
    "tag": 20,
    "footer": 16,
}
MIN_SUMMARY = 16
BETWEEN_STORIES = 26
LEAD_OFFSET = 22
LEAD_BAR = 6


def load_font(kind, size):
    """One DejaVu face at the requested point size."""
    return ImageFont.truetype(FONTS[kind], size)


def wrap(draw, text, font, width):
    """Greedy word wrap: pack as many words per line as fit."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= width:
            current = trial
            continue
        if current:
            lines.append(current)
        current = word
    if current:
        lines.append(current)
    return lines


def cap(lines, most):
    """Keep at most `most` lines of a wrapped block."""
    return lines[:most]


def pitch(font, leading):
    """Vertical advance of one line: the font height plus leading."""
    asc, desc = font.getmetrics()
    return asc + desc + leading


def block_height(lines, font, leading):
    """Height of a wrapped block: pitches minus the last leading."""
    if not lines:
        return 0
    return len(lines) * pitch(font, leading) - leading


def text_block(lines, font, colour, leading, after, centred=False, indent=0):
    return {
        "type": "text",
        "lines": lines,
        "font": font,
        "colour": colour,
        "leading": leading,
        "after": after,
        "centred": centred,
        "indent": indent,
    }


def rule_block(weight, colour, after):
    return {"type": "rule", "weight": weight, "colour": colour, "after": after}


def lead_piece(lines, font, colour, leading, after, indent=LEAD_OFFSET):
    return {
        "lines": lines,
        "font": font,
        "colour": colour,
        "leading": leading,
        "after": after,
        "indent": indent,
    }


def piece_height(piece):
    return block_height(piece["lines"], piece["font"], piece["leading"])


def lead_text_height(block):
    """Height of the lead block's text and inner gaps."""
    total = 0
    for piece in block["pieces"][:-1]:
        total += piece_height(piece) + piece["after"]
    return total + piece_height(block["pieces"][-1])


def block_total(block):
    """Full height of a block, including the blank space after it."""
    kind = block["type"]
    if kind == "text":
        return (
            block_height(block["lines"], block["font"], block["leading"])
            + block["after"]
        )
    if kind == "rule":
        return block["weight"] + block["after"]
    if kind == "lead":
        return lead_text_height(block) + block["after"]
    raise ValueError(f"unknown block type: {kind}")


def lay_out(data, draw, sizes):
    """Wrap the stories into blocks; return (blocks, total height)."""
    font = {
        "kicker": load_font("bold", sizes["kicker"]),
        "masthead": load_font("serif", sizes["masthead"]),
        "date": load_font("bold", sizes["date"]),
        "tag": load_font("bold", sizes["tag"]),
        "lead_head": load_font("serif", sizes["lead_head"]),
        "lead_sum": load_font("plain", sizes["lead_sum"]),
        "head": load_font("bold", sizes["head"]),
        "summary": load_font("plain", sizes["summary"]),
        "footer": load_font("plain", sizes["footer"]),
    }

    blocks = [
        text_block(
            wrap(draw, data["kicker"], font["kicker"], WIDTH),
            font["kicker"], GREY, 4, 8, centred=True,
        ),
        text_block(
            wrap(draw, data["title"], font["masthead"], WIDTH),
            font["masthead"], INK, 4, 5, centred=True,
        ),
        text_block(
            wrap(draw, data["date_line"], font["date"], WIDTH),
            font["date"], INK, 4, 12, centred=True,
        ),
        rule_block(3, INK, 5),
        rule_block(1, INK, 14),
    ]

    top = data["stories"][0]
    top_colour = tuple(top["color"])
    top_width = WIDTH - LEAD_OFFSET
    blocks.append(
        {
            "type": "lead",
            "colour": top_colour,
            "after": 14,
            "pieces": [
                lead_piece([top["tag"]], font["tag"], top_colour, 2, 5),
                lead_piece(
                    cap(
                        wrap(draw, top["headline"], font["lead_head"], top_width),
                        2,
                    ),
                    font["lead_head"], INK, 6, 6,
                ),
                lead_piece(
                    cap(
                        wrap(draw, top["summary"], font["lead_sum"], top_width),
                        2,
                    ),
                    font["lead_sum"], INK, 5, 0,
                ),
            ],
        }
    )
    blocks.append(rule_block(1, FAINT, 12))

    for story in data["stories"][1:]:
        colour = tuple(story["color"])
        head = cap(wrap(draw, story["headline"], font["head"], WIDTH), 2)
        # A single-line headline leaves room for two summary lines.
        summary = cap(
            wrap(draw, story["summary"], font["summary"], WIDTH),
            2 if len(head) == 1 else 1,
        )
        blocks.append(text_block([story["tag"]], font["tag"], colour, 2, 4))
        blocks.append(text_block(head, font["head"], INK, 4, 4))
        blocks.append(
            text_block(summary, font["summary"], INK, 4, BETWEEN_STORIES)
        )

    blocks.append(rule_block(1, FAINT, 8))
    blocks.append(
        text_block(
            wrap(draw, data["footer"], font["footer"], WIDTH),
            font["footer"], GREY, 3, 0, centred=True,
        )
    )

    total = TOP_PAD + sum(block_total(b) for b in blocks) + BOTTOM_PAD
    return blocks, total


def shrink_to_fit(data, draw):
    """Lay the page out, shrinking body type until it fits the budget."""
    sizes = dict(START_SIZES)
    blocks, total = lay_out(data, draw, sizes)
    while total > HEIGHT_LIMIT and sizes["summary"] > MIN_SUMMARY:
        sizes["summary"] -= 1
        sizes["head"] -= 1
        sizes["lead_sum"] -= 1
        blocks, total = lay_out(data, draw, sizes)
    if total > HEIGHT_LIMIT:
        # Never paint an overflowing page: fail loudly here so the bad
        # image is caught now, not at submission time.
        raise SystemExit(
            f"page still {total}px tall at minimum body size "
            f"(limit {HEIGHT_LIMIT}); refusing to overflow"
        )
    return blocks, total, sizes


class Painter:
    """Walks the laid-out blocks and draws them onto the canvas."""

    def __init__(self, draw):
        self.draw = draw
        self.y = TOP_PAD

    def walk(self, blocks):
        for block in blocks:
            if block["type"] == "text":
                self.draw_text(block)
            elif block["type"] == "rule":
                self.draw_rule(block)
            elif block["type"] == "lead":
                self.draw_lead(block)
            else:
                raise ValueError(f"unknown block type: {block['type']}")
        return self.y

    def draw_lines(self, lines, font, colour, leading, centred, indent):
        """Draw one paragraph's lines; advance past its text only."""
        for index, line in enumerate(lines):
            if centred:
                x = (SIDE - self.draw.textlength(line, font=font)) / 2
            else:
                x = MARGIN + indent
            self.draw.text(
                (x, self.y + index * pitch(font, leading)),
                line, font=font, fill=colour,
            )
        self.y += block_height(lines, font, leading)

    def draw_text(self, block):
        self.draw_lines(
            block["lines"], block["font"], block["colour"], block["leading"],
            block["centred"], block["indent"],
        )
        self.y += block["after"]

    def draw_rule(self, block):
        self.draw.rectangle(
            [MARGIN, self.y, SIDE - MARGIN, self.y + block["weight"] - 1],
            fill=block["colour"],
        )
        self.y += block["weight"] + block["after"]

    def draw_lead(self, block):
        body = lead_text_height(block)
        self.draw.rectangle(
            [MARGIN, self.y, MARGIN + LEAD_BAR - 1, self.y + body - 1],
            fill=block["colour"],
        )
        for piece in block["pieces"][:-1]:
            self.draw_lines(
                piece["lines"], piece["font"], piece["colour"],
                piece["leading"], False, piece["indent"],
            )
            self.y += piece["after"]
        last = block["pieces"][-1]
        self.draw_lines(
            last["lines"], last["font"], last["colour"], last["leading"],
            False, last["indent"],
        )
        self.y += block["after"]


def main():
    data = json.loads((HERE / "news.json").read_text())
    img = Image.new("RGB", (SIDE, SIDE), PAPER)
    draw = ImageDraw.Draw(img)

    blocks, total, fitted = shrink_to_fit(data, draw)
    painter = Painter(draw)
    end_y = painter.walk(blocks)

    out = HERE / "entry.png"
    img.save(out)
    print(
        f"wrote {out} ({out.stat().st_size} bytes); "
        f"measured total={total}, content ends y={end_y}, "
        f"body sizes head={fitted['head']} summary={fitted['summary']} "
        f"lead_sum={fitted['lead_sum']}"
    )


if __name__ == "__main__":
    main()
