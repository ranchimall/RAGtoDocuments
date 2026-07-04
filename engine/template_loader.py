"""
Loads a template by name from either templates/pptx/ or templates/pdf/.
The caller doesn't need to know which format a template belongs to —
each template's `engine:` field (pptx|pdf) tells main.py which renderer to use.
"""
import glob
import os
import yaml

FORMAT_SUBDIRS = ["pptx", "pdf"]


def load_template(template_name: str, base_dir: str = "./templates") -> dict:
    for subdir in FORMAT_SUBDIRS:
        path = os.path.join(base_dir, subdir, f"{template_name}.yaml")
        if os.path.exists(path):
            with open(path, "r") as f:
                return yaml.safe_load(f)

    available = list_templates(base_dir)
    raise FileNotFoundError(
        f"Template '{template_name}' not found. Available: {available}"
    )


def list_templates(base_dir: str = "./templates") -> dict:
    """Returns {template_name: format} for every template found."""
    result = {}
    for subdir in FORMAT_SUBDIRS:
        for f in glob.glob(os.path.join(base_dir, subdir, "*.yaml")):
            name = os.path.splitext(os.path.basename(f))[0]
            result[name] = subdir
    return result
