import argparse
import os

from data.chroma_query import query_chroma
from engine.template_loader import load_template, list_templates
from engine.pptx_renderer import render_pptx
from engine.pdf_renderer import render_pdf


def main():
    parser = argparse.ArgumentParser(description="Generate a templated deck or report from Chroma DB content.")
    parser.add_argument("--query", help="Query to run against the Chroma collection")
    parser.add_argument("--collection", help="Chroma collection name")
    parser.add_argument("--persist-dir", default="./chroma_data", help="Chroma persistent storage dir")
    parser.add_argument("--template", default=None, help="Template name (see --list-templates)")
    parser.add_argument("--list-templates", action="store_true", help="List available templates and exit")
    parser.add_argument("--title", default="Generated Document", help="Title slide/page text")
    parser.add_argument("--subtitle", default="", help="Subtitle text")
    parser.add_argument("--n-results", type=int, default=6, help="Number of Chroma results to include")
    parser.add_argument("--out", default=None, help="Output file path (defaults to output.<ext> based on template format)")
    args = parser.parse_args()

    if args.list_templates:
        templates = list_templates()
        if not templates:
            print("No templates found.")
        for name, fmt in sorted(templates.items()):
            print(f"  {name}  ({fmt})")
        return

    if not args.template:
        parser.error("--template is required (use --list-templates to see options)")

    if not args.query or not args.collection:
        parser.error("--query and --collection are required unless using --list-templates")

    items = query_chroma(
        query=args.query,
        collection_name=args.collection,
        persist_dir=args.persist_dir,
        n_results=args.n_results,
    )

    template = load_template(args.template)
    engine_type = template.get("engine", "pptx")

    default_ext = 'pdf' if engine_type == 'pdf' else 'pptx'
    base, ext = os.path.splitext(args.out) if args.out else ("output", f".{default_ext}")
    if not ext:
        ext = f".{default_ext}"

    # e.g. "report_minimal" -> "minimal", "deck_corporate" -> "corporate"
    template_suffix = args.template.split("_", 1)[-1] if "_" in args.template else args.template

    output_path = f"{base}_{template_suffix}_template{ext}"

    if engine_type == "pdf":
        render_pdf(items=items, template=template, deck_title=args.title, subtitle=args.subtitle, output_path=output_path)
    elif engine_type == "pptx":
        render_pptx(items=items, template=template, deck_title=args.title, subtitle=args.subtitle, output_path=output_path)
    else:
        raise ValueError(f"Unknown template engine '{engine_type}' in template '{args.template}'")

    print(f"Document written to {output_path}")


if __name__ == "__main__":
    main()
