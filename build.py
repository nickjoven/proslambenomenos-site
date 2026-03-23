#!/usr/bin/env python3
"""Build the unified proslambenomenos site from three source repositories.

Fetches notebooks, markdown, and walkthrough pages from 201, intersections,
and proslambenomenos, arranges them into a Jupyter Book structure, and builds
an executable HTML site.

Usage:
    python build.py                  # fetch from GitHub + build
    python build.py --local ../      # use local sibling repos + build
    python build.py --fetch-only     # fetch sources, skip jb build
    python build.py --check-only     # just verify sources are reachable
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

SITE_DIR = Path(__file__).parent
BOOK_DIR = SITE_DIR / "book"

REPOS = {
    "proslambenomenos": {
        "github": "nickjoven/proslambenomenos",
        "files": [
            "proslambenomenos.md",
            "kuramoto_einstein_mapping.md",
            "lyapunov_uniqueness.md",
            "renzos_rule_from_kuramoto.md",
            "notebooks/01_proslambenomenos_derivation.ipynb",
            "notebooks/02_lyapunov_functional.ipynb",
            "notebooks/03_renzo_from_kuramoto.ipynb",
            "notebooks/04_phase_portrait.ipynb",
        ],
        "order": 1,
        "title": "Proslambenomenos",
        "subtitle": "From \u039b to a\u2080: one frequency, zero free parameters",
    },
    "201": {
        "github": "nickjoven/201",
        "files": [
            "joven_unifying_framework.md",
            "kuramoto_einstein_mapping.md",
            "renzos_rule_derivation.md",
            "quantum_stribeck.ipynb",
        ],
        "order": 2,
        "title": "201 \u2014 The Unifying Framework",
        "subtitle": "Gravity as synchronization in a frictional medium",
    },
    "intersections": {
        "github": "nickjoven/intersections",
        "files": [
            "joven_stick_slip_dark_matter.md",
            "fundamental_forces_planck_scale.md",
            "stick_slip_lagrangian.ipynb",
            "stick_slip_galaxy.ipynb",
            "cone_topology.ipynb",
            "dispersion_rolling.ipynb",
            "08_square_wave_bifurcation.ipynb",
            "09_cylinder_stick_slip.ipynb",
            "10_qcd_stribeck_comparison.ipynb",
            "cvt/notebooks/01_sparc_mode_decomposition.ipynb",
            "cvt/notebooks/02_gravitational_fundamental.ipynb",
            "cvt/notebooks/03_inharmonicity_diagnostic.ipynb",
            "cvt/notebooks/04_mode_coupling_cascade.ipynb",
            "cvt/notebooks/05_cmb_overtone_comparison.ipynb",
            "cvt/notebooks/06_feigenbaum_cascade.ipynb",
            "cvt/notebooks/07_equipartition_uv_cutoff.ipynb",
        ],
        "order": 3,
        "title": "Intersections",
        "subtitle": "Stick-slip dynamics and galaxy rotation",
    },
    "harmonics": {
        "github": "nickjoven/harmonics",
        "files": [
            "sync_cost/FRAMEWORK.md",
            "sync_cost/derivations/INDEX.md",
            "sync_cost/derivations/01_born_rule.md",
            "sync_cost/derivations/02_spectral_tilt.md",
            "sync_cost/derivations/03_a0_threshold.md",
            "sync_cost/derivations/04_spectral_tilt_reframed.md",
            "sync_cost/derivations/05_two_forces.md",
            "sync_cost/derivations/06_planck_scale.md",
            "sync_cost/derivations/07_measurement_collapse.md",
            "sync_cost/derivations/08_high_z_mond.md",
            "sync_cost/derivations/09_fidelity_bound.md",
            "sync_cost/derivations/10_minimum_alphabet.md",
            "sync_cost/derivations/11_rational_field_equation.md",
        ],
        "order": 4,
        "title": "Harmonics",
        "subtitle": "Synchronization cost and the mode-locking substrate",
    },
}

# Extra data files needed for notebook execution
DATA_FILES = {
    "201": [
        "data/NGC2403_rotmod.dat",
    ],
}


def fetch_file_github(repo_slug: str, path: str) -> bytes:
    """Fetch a file from GitHub raw content."""
    url = f"https://raw.githubusercontent.com/{repo_slug}/main/{path}"
    return urlopen(Request(url), timeout=30).read()


def fetch_file_local(local_root: Path, repo_name: str, path: str) -> bytes:
    """Read a file from local sibling repo."""
    return (local_root / repo_name / path).read_bytes()


def fetch_sources(local_root: Path | None = None) -> dict:
    """Fetch all files. Returns {repo: {path: bytes}}."""
    result = {}
    for name, cfg in REPOS.items():
        result[name] = {}
        for path in cfg["files"]:
            try:
                if local_root:
                    data = fetch_file_local(local_root, name, path)
                else:
                    data = fetch_file_github(cfg["github"], path)
                result[name][path] = data
                print(f"  {name}/{path}")
            except (FileNotFoundError, URLError, OSError) as e:
                print(f"  {name}/{path} — MISSING ({e})")

    # Fetch data files needed for execution
    for name, paths in DATA_FILES.items():
        if name not in result:
            result[name] = {}
        cfg = REPOS[name]
        for path in paths:
            try:
                if local_root:
                    data = fetch_file_local(local_root, name, path)
                else:
                    data = fetch_file_github(cfg["github"], path)
                result[name][path] = data
                print(f"  {name}/{path} (data)")
            except (FileNotFoundError, URLError, OSError) as e:
                print(f"  {name}/{path} — MISSING ({e})")

    return result


def write_book_sources(sources: dict):
    """Write fetched sources into the Jupyter Book directory structure."""
    if BOOK_DIR.exists():
        shutil.rmtree(BOOK_DIR)

    for repo, files in sources.items():
        for path, data in files.items():
            dest = BOOK_DIR / repo / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)


def generate_toc():
    """Generate _toc.yml for Jupyter Book."""
    toc = {
        "format": "jb-book",
        "root": "intro",
        "parts": [],
    }

    for name, cfg in sorted(REPOS.items(), key=lambda x: x[1]["order"]):
        chapters = []
        md_files = [f for f in cfg["files"] if f.endswith(".md")]
        nb_files = [f for f in cfg["files"] if f.endswith(".ipynb")]

        for f in md_files:
            chapters.append({"file": f"{name}/{f.removesuffix('.md')}"})
        for f in nb_files:
            chapters.append({"file": f"{name}/{f.removesuffix('.ipynb')}"})

        toc["parts"].append({
            "caption": cfg["title"],
            "chapters": chapters,
        })

    # Write as YAML manually (avoid pyyaml dependency)
    lines = [
        "format: jb-book",
        "root: intro",
        "parts:",
    ]
    for part in toc["parts"]:
        lines.append(f"  - caption: \"{part['caption']}\"")
        lines.append("    chapters:")
        for ch in part["chapters"]:
            lines.append(f"      - file: {ch['file']}")

    toc_path = BOOK_DIR / "_toc.yml"
    toc_path.write_text("\n".join(lines) + "\n")
    print(f"  _toc.yml ({sum(len(p['chapters']) for p in toc['parts'])} chapters)")


def generate_config():
    """Generate _config.yml for Jupyter Book."""
    config = """\
title: "Proslambenomenos"
author: "N. Joven"
copyright: "2026"
logo: ""

execute:
  execute_notebooks: cache
  timeout: 300
  allow_errors: false

launch_buttons:
  notebook_interface: classic

repository:
  url: https://github.com/nickjoven/proslambenomenos-site

html:
  use_issues_button: false
  use_repository_button: true
  use_edit_page_button: false
  favicon: ""
  extra_css:
    - _static/custom.css

sphinx:
  config:
    mathjax3_config:
      tex:
        macros:
          "RR": "\\\\mathbb{R}"
          "NN": "\\\\mathbb{N}"
    html_theme_options:
      navigation_with_keys: false
"""
    (BOOK_DIR / "_config.yml").write_text(config)

    # Custom CSS for dark-ish accents
    static_dir = BOOK_DIR / "_static"
    static_dir.mkdir(exist_ok=True)
    (static_dir / "custom.css").write_text("""\
/* Accent colors matching the walkthrough pages */
:root {
  --pst-color-primary: #58a6ff;
  --pst-color-secondary: #7ee787;
}
""")
    print("  _config.yml")


def generate_intro():
    """Generate the intro/landing page."""
    intro = """\
# Proslambenomenos

**The added tone: a fundamental reference frequency for synchronization gravity.**

N. Joven — 2026 — [ORCID 0009-0008-0679-0812](https://orcid.org/0009-0008-0679-0812) — CC0 1.0

---

In ancient Greek music theory, the *proslambenomenos* was the lowest pitch in the
Greater Perfect System — the reference from which every interval was measured.

This site presents a physical analogue: the cosmological constant $\\Lambda$ sets a
fundamental oscillation frequency, and the MOND acceleration scale, the Hubble rate,
and the galactic synchronization threshold are all overtones of this single reference.

$$\\Lambda \\;\\xrightarrow{c\\sqrt{\\cdot/3}}\\; \\nu_\\Lambda \\;\\xrightarrow{\\div\\sqrt{\\Omega_\\Lambda}}\\; H_0 \\;\\xrightarrow{c/2\\pi}\\; a_0$$

Three constants. One frequency. Zero free parameters.

## Reading order

1. **Proslambenomenos** — derives $a_0$ from $\\Lambda$ via Kuramoto critical coupling,
   proves uniqueness via Lyapunov dissipation, derives Renzo's Rule from self-consistency
2. **201** — the unifying framework: gravity as synchronization in a frictional medium,
   SPARC-X numerical verification on 175 galaxies
3. **Intersections** — the physical mechanism: stick-slip dynamics, Lagrangian relaxation,
   QCD parallels, Feigenbaum universality
4. **Harmonics** — the synchronization cost framework: mode-locking substrate, Born rule
   from basin geometry, $a_0$ as cost equality, spectral tilt, Planck scale thresholds

## Source repositories

- [proslambenomenos](https://github.com/nickjoven/proslambenomenos) — the self-contained preprint
- [201](https://github.com/nickjoven/201) — the numerical framework
- [intersections](https://github.com/nickjoven/intersections) — the physical substrate
- [harmonics](https://github.com/nickjoven/harmonics) — the synchronization cost derivations

All notebooks on this site are **executed during build** — outputs are computed,
not pre-rendered. The source is the truth.
"""
    (BOOK_DIR / "intro.md").write_text(intro)
    print("  intro.md")


def generate_manifest(sources: dict) -> dict:
    """Generate a manifest of source hashes for drift detection."""
    manifest = {}
    for repo, files in sources.items():
        for path, data in files.items():
            manifest[f"{repo}/{path}"] = hashlib.sha256(data).hexdigest()[:16]
    return manifest


def build_book():
    """Run jupyter-book build."""
    # jupyter-book v1 doesn't support -m invocation; use the CLI entry point
    cmd = [
        sys.executable, "-c",
        "from jupyter_book.cli.main import main; main()",
        "--",
        "build", str(BOOK_DIR),
    ]
    print(f"  Running jupyter-book build {BOOK_DIR}")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print("  jupyter-book build failed!")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Build the unified proslambenomenos site")
    parser.add_argument("--local", type=str, default=None,
                        help="Path to parent directory containing sibling repos")
    parser.add_argument("--fetch-only", action="store_true",
                        help="Fetch sources and generate book structure, skip build")
    parser.add_argument("--check-only", action="store_true",
                        help="Just verify sources are reachable, don't build")
    args = parser.parse_args()

    local_root = Path(args.local).resolve() if args.local else None

    print("Fetching sources...")
    sources = fetch_sources(local_root)

    if args.check_only:
        total = sum(len(f) for f in sources.values())
        expected = sum(len(c["files"]) for c in REPOS.values()) + sum(
            len(v) for v in DATA_FILES.values())
        print(f"\n{total}/{expected} files reachable.")
        return 0 if total == expected else 1

    print("\nWriting book sources...")
    write_book_sources(sources)

    print("\nGenerating Jupyter Book config...")
    generate_config()
    generate_toc()
    generate_intro()

    # Write manifest
    manifest = generate_manifest(sources)
    (BOOK_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))

    if args.fetch_only:
        print(f"\nFetch complete. Book sources at {BOOK_DIR}")
        return 0

    print("\nBuilding Jupyter Book...")
    if not build_book():
        return 1

    build_html = BOOK_DIR / "_build" / "html"
    print(f"\nBuild complete: {build_html}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
