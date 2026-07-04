from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ContentItem:
    text: str
    title: Optional[str] = None
    image_path: Optional[str] = None       # primary image
    image_paths: list[str] = field(default_factory=list)  # additional images -> triggers grid layout
    source: Optional[str] = None
    score: float = 0.0
    layout: Optional[str] = None  # explicit override, e.g. "stat_callout", "quote"
