"""
Shared content-driven layout selection, used by both the pptx and pdf
renderers so a given ContentItem maps to the same layout choice regardless
of output format.
"""
import re

from engine.content import ContentItem


def choose_layout(item: ContentItem, template: dict, index: int, valid_layouts: set) -> str:
    # 1. Explicit per-item override wins
    if item.layout and item.layout in valid_layouts:
        return item.layout

    # 2. Template can force a fixed rotation, bypassing content-based decisions
    sequence = template.get("layout_sequence")
    if sequence:
        return sequence[index % len(sequence)]

    # 3. Inspect content signals
    text = item.text.strip()
    word_count = len(text.split())
    image_count = (1 if item.image_path else 0) + len(item.image_paths)

    is_quote = (
        text.startswith(('"', "\u201c", "'")) and text.rstrip().endswith(('"', "\u201d", "'"))
    )
    has_digit = bool(re.search(r"\d", text))
    is_stat = word_count <= 8 and has_digit  # short + numeric, e.g. "42% retention"
    is_list = (
        text.count("\n") >= 2
        or text.count(";") >= 2
        or re.search(r"(^|\n)\s*[-•]\s", text) is not None
    )

    if image_count >= 2 and "image_grid" in valid_layouts:
        return "image_grid"
    if is_quote and "quote" in valid_layouts:
        return "quote"
    if is_stat and "stat_callout" in valid_layouts:
        return "stat_callout"
    if is_list and "bulleted_list" in valid_layouts:
        return "bulleted_list"
    if image_count == 1:
        if word_count <= 15 and "full_bleed_image" in valid_layouts:
            return "full_bleed_image"
        if "two_column_image" in valid_layouts:
            return "two_column_image"
    return "text_block"
