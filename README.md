# This is AI Blockchain Contract project

This project is part of AI Blockchain Contract series of RanchiMall. A blockchain contract is a governance structure on the blockchain which enables human led supervision over blockchain projects, as opposed to Corporate incorporation in traditional businesses and purely automated Smartcontracts in DAOs (Distributed Autonomous Organisation). Funding for Blockchain Contract comes directly on blockchain.

# Deck Creator

Generate templated PowerPoint decks or PDF reports from a local Chroma DB
collection. One CLI, one template naming scheme — the format (pptx vs pdf)
is determined automatically by which template you pick.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# See available designs (shows format next to each)
python main.py --list-templates
#   deck_corporate   (pptx)
#   deck_playful     (pptx)
#   report_modern    (pdf)
#   report_minimal   (pdf)

# Generate a slide deck
python main.py \
  --query "quarterly sales trends" \
  --collection my_docs \
  --template deck_corporate \
  --title "Q2 Sales Review" \
  --out q2_review.pptx

# Generate a PDF report — same command, just a different --template
python main.py \
  --query "quarterly sales trends" \
  --collection my_docs \
  --template report_modern \
  --title "Q2 Sales Review" \
  --out q2_review.pdf
```

If `--out` is omitted, output defaults to `output.pptx` or `output.pdf`
based on the template's format.

## How it works

1. `data/chroma_query.py` queries your Chroma collection and normalizes
   each hit into a `ContentItem` (text, title, optional image_path(s), source).
2. `engine/image_resolver.py` resolves image_path (local or remote) to a
   usable file, or returns None so the layout falls back to text-only.
3. `engine/template_loader.py` loads a YAML design config from
   `templates/pptx/` or `templates/pdf/` by name — it searches both, so
   you don't need to know a template's format in advance.
4. `engine/layout_selector.py` picks a layout per content item based on
   content signals, shared by both renderers so pptx and pdf output use
   identical layout logic:
   - 2+ images -> `image_grid`
   - quoted text -> `quote`
   - short + numeric -> `stat_callout`
   - multi-line / semicolon-separated -> `bulleted_list`
   - 1 image, short caption -> `full_bleed_image`
   - 1 image, longer text -> `two_column_image`
   - otherwise -> `text_block`

   Priority: explicit `ContentItem.layout` override > template's
   `layout_sequence` (forces a fixed rotation) > content heuristics.
5. `engine/pptx_renderer.py` (python-pptx) or `engine/pdf_renderer.py`
   (reportlab canvas) draws each item using its chosen layout.

## Adding a new design

Copy a file in `templates/pptx/` or `templates/pdf/`, change the `theme`
values, give it a new filename — it's immediately selectable via
`--template <name>`. No code changes needed for palette/font changes.

Template schema:
```yaml
name: my_template
engine: pptx        # or pdf — determines which renderer is used
theme:
  primary_color: "1E2761"
  secondary_color: "CADCFC"
  background: "FFFFFF"
  text_color: "212121"
  muted_color: "6E6E6E"
  on_primary: "FFFFFF"
  font_header: "Cambria"        # pdf templates use reportlab base fonts,
  font_body: "Calibri"          # e.g. Helvetica, Helvetica-Bold, Times-Roman
# pdf-only:
# page_size: LETTER  # or A4
# margin_inches: 0.75
```

## Chroma metadata convention

For images to appear automatically, store an `image_path` field (and
optionally `image_paths` for multiple) in each document's metadata when
you ingest into Chroma:

```python
collection.add(
    documents=[...],
    metadatas=[{"title": "...", "image_path": "https://...", "source": "..."}],
    ids=[...],
)
```

## Adding a new layout

Write a `_layout_<name>(...)` function in both `pptx_renderer.py` and
`pdf_renderer.py`, register it in each file's `LAYOUT_REGISTRY`, and (if
it should be picked automatically) add the trigger condition to
`engine/layout_selector.py`.
