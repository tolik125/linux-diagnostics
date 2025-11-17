#!/usr/bin/env python3
"""Render terminal-like GIFs from captured text snippets."""
from __future__ import annotations

import textwrap
from pathlib import Path
from typing import List

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_SIZE = 24
LINE_HEIGHT = FONT_SIZE + 10
WIDTH = 1600
MARGIN = 40
BG_COLOR = (5, 6, 8)
DEFAULT_COLOR = (231, 244, 255)
PROMPT_COLOR = (173, 214, 255)
OK_COLOR = (129, 243, 191)
WARN_COLOR = (255, 233, 137)
FAIL_COLOR = (255, 153, 153)
SUGGESTION_COLOR = (186, 210, 255)
JSON_KEY_COLOR = (173, 214, 255)

MAX_CHARS = 115


def wrap_lines(text: str) -> List[str]:
    lines: List[str] = []
    for raw in text.splitlines():
        if not raw:
            lines.append("")
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        prefix = raw[:indent]
        body = raw[indent:]
        wrapped = textwrap.wrap(
            body,
            width=max(10, MAX_CHARS - indent),
            break_long_words=False,
            drop_whitespace=False,
        )
        if not wrapped:
            lines.append(prefix)
            continue
        for idx, chunk in enumerate(wrapped):
            lines.append((prefix if idx == 0 else " " * indent) + chunk.rstrip())
    return lines


def color_for(line: str) -> tuple[int, int, int]:
    stripped = line.lstrip()
    if stripped.startswith("$"):
        return PROMPT_COLOR
    if stripped.startswith("["):
        if "[OK]" in stripped:
            return OK_COLOR
        if "[WARN]" in stripped:
            return WARN_COLOR
        if "[FAIL]" in stripped:
            return FAIL_COLOR
    if stripped.startswith("-") or stripped.startswith("Sugest"):
        return SUGGESTION_COLOR
    if stripped.startswith("\"") and stripped.endswith(":"):
        return JSON_KEY_COLOR
    if stripped.startswith("{") or stripped.startswith("}") or stripped.startswith("["):
        return DEFAULT_COLOR
    if stripped.startswith("\""):
        return SUGGESTION_COLOR
    return DEFAULT_COLOR


def render_image(lines: List[str]) -> Image.Image:
    height = max(LINE_HEIGHT + MARGIN * 2, MARGIN * 2 + LINE_HEIGHT * len(lines))
    image = Image.new("RGB", (WIDTH, height), color=BG_COLOR)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    draw = ImageDraw.Draw(image)
    y = MARGIN
    if not lines:
        lines = [""]
    for line in lines:
        draw.text((MARGIN, y), line, font=font, fill=color_for(line))
        y += LINE_HEIGHT
    return image


def build_frames(lines: List[str]) -> List[Image.Image]:
    frames: List[Image.Image] = []
    for idx in range(1, len(lines) + 1):
        # Slow start for the first few lines, then accelerate.
        if idx <= 4 or idx == len(lines) or idx % 2 == 0:
            frames.append(render_image(lines[:idx]))
    # Pause at the end for readability.
    frames.extend([render_image(lines)] * 2)
    return frames


def render_gif(text_path: Path, gif_path: Path) -> None:
    text = text_path.read_text().rstrip()
    lines = wrap_lines(text)
    frames = build_frames(lines)
    if not frames:
        frames = [render_image(["(vazio)"])]
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=200,
        loop=0,
        disposal=2,
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Render GIFs from terminal snippets.")
    parser.add_argument("text", type=Path, help="Input text file")
    parser.add_argument("gif", type=Path, help="Output GIF path")
    args = parser.parse_args()

    render_gif(args.text, args.gif)


if __name__ == "__main__":
    main()
