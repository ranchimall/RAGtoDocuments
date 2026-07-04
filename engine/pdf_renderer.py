"""
Renders ContentItems into a templated PDF using reportlab's canvas API.
Mirrors engine/pptx_renderer.py: same template schema, same layout names,
same content-driven layout selection (engine/layout_selector.py).
"""
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth

from engine.content import ContentItem
from engine.image_resolver import resolve_image
from engine.layout_selector import choose_layout

PAGE_SIZES = {"A4": A4, "LETTER": LETTER}


def _hex(color: str):
    color = color if color.startswith("#") else f"#{color}"
    return HexColor(color)


def _wrap_text(c, text, font_name, font_size, max_width):
    """Greedy word-wrap for canvas.drawString (no Paragraph/Platypus flow)."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if stringWidth(trial, font_name, font_size) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_wrapped(c, text, x, y, max_width, font_name, font_size, color, leading=None, align="left"):
    leading = leading or font_size * 1.3
    c.setFont(font_name, font_size)
    c.setFillColor(color)
    lines = _wrap_text(c, text, font_name, font_size, max_width)
    for line in lines:
        if align == "center":
            line_width = stringWidth(line, font_name, font_size)
            c.drawString(x + (max_width - line_width) / 2, y, line)
        else:
            c.drawString(x, y, line)
        y -= leading
    return y  # returns the y position after the last line


def _caption(c, theme, source, page_w, margin):
    if not source:
        return
    c.setFont(theme.get("font_body", "Helvetica"), 9)
    c.setFillColor(_hex(theme.get("muted_color", "888888")))
    c.drawString(margin, 0.5 * 72, f"Source: {source}")


# ---------------------------------------------------------------------------
# Layout implementations. Each takes (c, theme, item, page_w, page_h, margin).
# ---------------------------------------------------------------------------

def _layout_title(c, theme, deck_title, subtitle, page_w, page_h):
    c.setFillColor(_hex(theme["primary_color"]))
    c.rect(0, 0, page_w, page_h, fill=True, stroke=False)

    c.setFont(theme.get("font_header", "Helvetica-Bold"), 32)
    c.setFillColor(_hex(theme.get("on_primary", "FFFFFF")))
    c.drawString(0.9 * 72, page_h / 2 + 0.3 * 72, deck_title)

    if subtitle:
        c.setFont(theme.get("font_body", "Helvetica"), 14)
        c.setFillColor(_hex(theme.get("secondary_color", "CADCFC")))
        c.drawString(0.9 * 72, page_h / 2 - 0.1 * 72, subtitle)


def _layout_two_column_image(c, theme, item, page_w, page_h, margin):
    image_path = resolve_image(item.image_path)
    text_col_w = page_w * 0.55 - margin * 1.5 if image_path else page_w - 2 * margin

    y = page_h - margin
    c.setFont(theme.get("font_header", "Helvetica-Bold"), 20)
    c.setFillColor(_hex(theme["primary_color"]))
    c.drawString(margin, y, item.title or "Untitled")
    y -= 0.5 * 72

    _draw_wrapped(
        c, item.text, margin, y, text_col_w,
        theme.get("font_body", "Helvetica"), 11,
        _hex(theme.get("text_color", "212121")),
    )

    if image_path:
        img = ImageReader(image_path)
        iw, ih = img.getSize()
        max_w = page_w * 0.4
        max_h = page_h * 0.5
        scale = min(max_w / iw, max_h / ih)
        c.drawImage(
            image_path,
            page_w - margin - iw * scale, page_h - margin - ih * scale,
            width=iw * scale, height=ih * scale, preserveAspectRatio=True,
        )

    _caption(c, theme, item.source, page_w, margin)


def _layout_full_bleed_image(c, theme, item, page_w, page_h, margin):
    image_path = resolve_image(item.image_path)
    if image_path:
        img = ImageReader(image_path)
        iw, ih = img.getSize()
        band_w = page_w * 0.45
        scale = band_w / iw
        c.drawImage(image_path, 0, 0, width=band_w, height=page_h, preserveAspectRatio=False)
        text_x = band_w + margin
        text_w = page_w - band_w - 2 * margin
    else:
        text_x = margin
        text_w = page_w - 2 * margin

    y = page_h - margin
    c.setFont(theme.get("font_header", "Helvetica-Bold"), 18)
    c.setFillColor(_hex(theme["primary_color"]))
    y = _draw_wrapped(c, item.title or "Untitled", text_x, y, text_w,
                       theme.get("font_header", "Helvetica-Bold"), 18, _hex(theme["primary_color"]))
    y -= 0.2 * 72

    _draw_wrapped(
        c, item.text, text_x, y, text_w,
        theme.get("font_body", "Helvetica"), 11,
        _hex(theme.get("text_color", "212121")),
    )

    _caption(c, theme, item.source, page_w, margin)


def _layout_text_block(c, theme, item, page_w, page_h, margin):
    y = page_h - margin
    c.setFont(theme.get("font_header", "Helvetica-Bold"), 22)
    c.setFillColor(_hex(theme["primary_color"]))
    c.drawString(margin, y, item.title or "Untitled")
    y -= 0.55 * 72

    _draw_wrapped(
        c, item.text, margin, y, page_w - 2 * margin,
        theme.get("font_body", "Helvetica"), 12,
        _hex(theme.get("text_color", "212121")),
    )

    _caption(c, theme, item.source, page_w, margin)


def _layout_stat_callout(c, theme, item, page_w, page_h, margin):
    c.setFont(theme.get("font_body", "Helvetica"), 13)
    c.setFillColor(_hex(theme.get("muted_color", "888888")))
    label = (item.title or "").upper()
    label_w = stringWidth(label, theme.get("font_body", "Helvetica"), 13)
    c.drawString((page_w - label_w) / 2, page_h * 0.58, label)

    c.setFont(theme.get("font_header", "Helvetica-Bold"), 48)
    c.setFillColor(_hex(theme["primary_color"]))
    stat_w = stringWidth(item.text, theme.get("font_header", "Helvetica-Bold"), 48)
    c.drawString((page_w - stat_w) / 2, page_h * 0.48, item.text)

    _caption(c, theme, item.source, page_w, margin)


def _layout_quote(c, theme, item, page_w, page_h, margin):
    quote_text = f"\u201c{item.text}\u201d"
    c.setFont(theme.get("font_header", "Helvetica-Oblique"), 20)
    c.setFillColor(_hex(theme["primary_color"]))
    y = _draw_wrapped(
        c, quote_text, margin + 0.5 * 72, page_h * 0.62, page_w - 2 * margin - 72,
        theme.get("font_header", "Helvetica-Oblique"), 20, _hex(theme["primary_color"]),
        align="center",
    )

    if item.title:
        attribution = f"\u2014 {item.title}"
        c.setFont(theme.get("font_body", "Helvetica"), 12)
        c.setFillColor(_hex(theme.get("muted_color", "888888")))
        attr_w = stringWidth(attribution, theme.get("font_body", "Helvetica"), 12)
        c.drawString((page_w - attr_w) / 2, y - 0.3 * 72, attribution)

    _caption(c, theme, item.source, page_w, margin)


def _layout_image_grid(c, theme, item, page_w, page_h, margin):
    all_images = ([item.image_path] if item.image_path else []) + list(item.image_paths)
    resolved = [resolve_image(p) for p in all_images]
    resolved = [p for p in resolved if p][:4]

    y = page_h - margin
    c.setFont(theme.get("font_header", "Helvetica-Bold"), 20)
    c.setFillColor(_hex(theme["primary_color"]))
    c.drawString(margin, y, item.title or "Untitled")

    grid_top = page_h - margin - 0.7 * 72
    cell_w = (page_w - 2 * margin - 0.2 * 72) / 2
    cell_h = (page_h * 0.5) / 2
    positions = [
        (margin, grid_top - cell_h),
        (margin + cell_w + 0.2 * 72, grid_top - cell_h),
        (margin, grid_top - 2 * cell_h - 0.2 * 72),
        (margin + cell_w + 0.2 * 72, grid_top - 2 * cell_h - 0.2 * 72),
    ]
    for path, (x, y_pos) in zip(resolved, positions):
        c.drawImage(path, x, y_pos, width=cell_w, height=cell_h, preserveAspectRatio=True)

    if item.text:
        c.setFont(theme.get("font_body", "Helvetica"), 10)
        c.setFillColor(_hex(theme.get("text_color", "212121")))
        c.drawString(margin, grid_top - 2 * cell_h - 0.5 * 72, item.text)

    _caption(c, theme, item.source, page_w, margin)


def _layout_bulleted_list(c, theme, item, page_w, page_h, margin):
    import re as _re

    y = page_h - margin
    c.setFont(theme.get("font_header", "Helvetica-Bold"), 22)
    c.setFillColor(_hex(theme["primary_color"]))
    c.drawString(margin, y, item.title or "Untitled")
    y -= 0.6 * 72

    raw_items = _re.split(r"\n|;", item.text)
    bullets = [b.strip(" -•\t") for b in raw_items if b.strip(" -•\t")]

    c.setFont(theme.get("font_body", "Helvetica"), 13)
    c.setFillColor(_hex(theme.get("text_color", "212121")))
    for bullet in bullets:
        c.drawString(margin + 0.25 * 72, y, f"\u2022  {bullet}")
        y -= 0.35 * 72

    _caption(c, theme, item.source, page_w, margin)


LAYOUT_REGISTRY = {
    "two_column_image": _layout_two_column_image,
    "full_bleed_image": _layout_full_bleed_image,
    "text_block": _layout_text_block,
    "stat_callout": _layout_stat_callout,
    "quote": _layout_quote,
    "image_grid": _layout_image_grid,
    "bulleted_list": _layout_bulleted_list,
}


def render_pdf(
    items: list[ContentItem],
    template: dict,
    deck_title: str,
    output_path: str,
    subtitle: str = "",
):
    from reportlab.pdfgen import canvas as _canvas

    page_size = PAGE_SIZES.get(template.get("page_size", "LETTER"), LETTER)
    page_w, page_h = page_size
    margin = template.get("margin_inches", 0.75) * 72
    theme = template["theme"]

    c = _canvas.Canvas(output_path, pagesize=page_size)

    _layout_title(c, theme, deck_title, subtitle, page_w, page_h)
    c.showPage()

    for index, item in enumerate(items):
        layout_name = choose_layout(item, template, index, set(LAYOUT_REGISTRY.keys()))
        layout_fn = LAYOUT_REGISTRY[layout_name]
        c.setFillColor(_hex(theme.get("background", "FFFFFF")))
        c.rect(0, 0, page_w, page_h, fill=True, stroke=False)
        layout_fn(c, theme, item, page_w, page_h, margin)
        c.showPage()

    c.save()
    return output_path
