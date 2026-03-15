#!/usr/bin/env python3
"""Build the unified proslambenomenos site from three source repositories.

Fetches notebooks and walkthrough pages from 201, intersections, and
proslambenomenos, converts notebooks to HTML via nbconvert, and assembles
a static site with shared navigation.

Usage:
    python build.py                  # fetch from GitHub + build
    python build.py --local ../      # use local sibling repos + build
    python build.py --check-only     # just verify sources are reachable
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

SITE_DIR = Path(__file__).parent
BUILD_DIR = SITE_DIR / "_build"
SOURCES_DIR = SITE_DIR / "_sources"

REPOS = {
    "proslambenomenos": {
        "github": "nickjoven/proslambenomenos",
        "notebooks": [
            "notebooks/01_proslambenomenos_derivation.ipynb",
            "notebooks/02_lyapunov_functional.ipynb",
            "notebooks/03_renzo_from_kuramoto.ipynb",
            "notebooks/04_phase_portrait.ipynb",
        ],
        "walkthrough": "docs/index.html",
        "order": 1,
        "title": "Proslambenomenos",
        "subtitle": "From \u039b to a\u2080: one frequency, zero free parameters",
    },
    "201": {
        "github": "nickjoven/201",
        "notebooks": [
            "quantum_stribeck.ipynb",
        ],
        "walkthrough": "docs/index.html",
        "order": 2,
        "title": "201 \u2014 The Unifying Framework",
        "subtitle": "Gravity as synchronization in a frictional medium",
    },
    "intersections": {
        "github": "nickjoven/intersections",
        "notebooks": [
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
        "walkthrough": "index.html",
        "order": 3,
        "title": "Intersections",
        "subtitle": "Stick-slip dynamics and galaxy rotation",
    },
}

# Files in source repos that should trigger a site rebuild
WATCH_PATTERNS = [
    "*.ipynb",
    "*.md",
    "docs/**",
    "*.html",
]


def fetch_file_github(repo_slug: str, path: str) -> bytes:
    """Fetch a file from GitHub raw content."""
    url = f"https://raw.githubusercontent.com/{repo_slug}/main/{path}"
    req = Request(url)
    return urlopen(req, timeout=15).read()


def fetch_file_local(local_root: Path, repo_name: str, path: str) -> bytes:
    """Read a file from local sibling repo."""
    fp = local_root / repo_name / path
    return fp.read_bytes()


def fetch_sources(local_root: Path | None = None) -> dict:
    """Fetch all notebook and walkthrough files. Returns {repo: {path: bytes}}."""
    result = {}
    for name, cfg in REPOS.items():
        result[name] = {}
        paths = cfg["notebooks"] + [cfg["walkthrough"]]
        for path in paths:
            try:
                if local_root:
                    data = fetch_file_local(local_root, name, path)
                else:
                    data = fetch_file_github(cfg["github"], path)
                result[name][path] = data
                print(f"  {name}/{path}")
            except (FileNotFoundError, URLError, OSError) as e:
                print(f"  {name}/{path} — MISSING ({e})")
    return result


def write_sources(sources: dict):
    """Write fetched sources to _sources/ directory."""
    if SOURCES_DIR.exists():
        shutil.rmtree(SOURCES_DIR)
    for repo, files in sources.items():
        for path, data in files.items():
            dest = SOURCES_DIR / repo / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)


def convert_notebooks():
    """Convert all .ipynb files in _sources/ to HTML via nbconvert."""
    notebooks = list(SOURCES_DIR.rglob("*.ipynb"))
    if not notebooks:
        print("No notebooks found.")
        return []

    converted = []
    for nb in notebooks:
        out_dir = BUILD_DIR / nb.relative_to(SOURCES_DIR).parent
        out_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            sys.executable, "-m", "nbconvert",
            "--to", "html",
            "--no-input",
            "--output-dir", str(out_dir),
            "--template", "lab",
            str(nb),
        ]
        print(f"  Converting {nb.relative_to(SOURCES_DIR)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # Retry with input cells included (some notebooks need it)
            cmd.remove("--no-input")
            result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"    FAILED: {result.stderr[:200]}")
        else:
            html_name = nb.stem + ".html"
            converted.append(out_dir / html_name)
    return converted


def copy_walkthroughs():
    """Copy walkthrough HTML files to build directory."""
    for name, cfg in REPOS.items():
        wt = cfg["walkthrough"]
        src = SOURCES_DIR / name / wt
        if src.exists():
            dest = BUILD_DIR / name / "walkthrough.html"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            print(f"  {name}/walkthrough.html")


def generate_index(converted: list):
    """Generate the unified site index page."""
    sections = []
    for name, cfg in sorted(REPOS.items(), key=lambda x: x[1]["order"]):
        nb_links = []
        for nb_path in cfg["notebooks"]:
            html_name = Path(nb_path).stem + ".html"
            # Find the converted HTML
            rel = Path(name) / Path(nb_path).parent / html_name
            nb_links.append(f'<li><a href="{rel}">{Path(nb_path).stem}</a></li>')

        wt_link = f'<a href="{name}/walkthrough.html">Walkthrough</a>'

        sections.append(f"""
    <section class="card" id="{name}">
      <h2>{cfg['title']}</h2>
      <p class="subtitle">{cfg['subtitle']}</p>
      <p>{wt_link} ·
         <a href="https://github.com/{cfg['github']}">GitHub</a></p>
      <h3>Notebooks</h3>
      <ul>
        {''.join(nb_links)}
      </ul>
    </section>""")

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Proslambenomenos — Synchronization Gravity</title>
<style>
  :root {{
    --bg: #0d1117; --surface: #161b22; --border: #30363d;
    --text: #e6edf3; --muted: #8b949e;
    --accent: #58a6ff; --accent2: #7ee787; --accent3: #d2a8ff; --accent4: #ffa657;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: var(--bg); color: var(--text); line-height: 1.7; font-size: 16px;
  }}
  .container {{ max-width: 860px; margin: 0 auto; padding: 3rem 1.5rem; }}
  h1 {{ font-size: 2.2rem; color: var(--accent); margin-bottom: 0.3rem; }}
  h2 {{ font-size: 1.4rem; color: var(--accent2); margin-bottom: 0.5rem; }}
  h3 {{ font-size: 1.05rem; color: var(--accent3); margin: 1rem 0 0.5rem; }}
  .subtitle {{ color: var(--muted); font-size: 1rem; margin-bottom: 1rem; }}
  .author {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 2.5rem; }}
  .card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 1.5rem; margin: 1.5rem 0;
  }}
  a {{ color: var(--accent); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  ul {{ margin: 0.5rem 0 0 1.5rem; }}
  li {{ margin: 0.3rem 0; }}
  .chain {{
    font-family: 'Courier New', monospace; background: var(--surface);
    border: 1px solid var(--border); border-radius: 8px;
    padding: 1.2rem; margin: 1.5rem 0; text-align: center;
    font-size: 1rem; line-height: 2;
  }}
  .chain .arrow {{ color: var(--accent); }}
  .chain .label {{ color: var(--muted); font-size: 0.8rem; }}
  .meta {{ color: var(--muted); font-size: 0.8rem; margin-top: 3rem;
           padding-top: 1rem; border-top: 1px solid var(--border); text-align: center; }}
</style>
</head>
<body>
<div class="container">

<h1>Proslambenomenos</h1>
<p class="subtitle">The added tone: a fundamental reference frequency for synchronization gravity.</p>
<p class="author">N. Joven — 2026 —
  <a href="https://orcid.org/0009-0008-0679-0812">ORCID 0009-0008-0679-0812</a> — CC0 1.0</p>

<div class="chain">
  <span style="color:var(--accent3)">&Lambda;</span>
  <span class="arrow">&nbsp;&rarr;&nbsp;</span>
  <span class="label">c&radic;(&middot;/3)</span>
  <span class="arrow">&nbsp;&rarr;&nbsp;</span>
  <span style="color:var(--accent)">&nu;<sub>&Lambda;</sub> &asymp; H<sub>0</sub></span>
  <span class="arrow">&nbsp;&rarr;&nbsp;</span>
  <span class="label">c/2&pi;</span>
  <span class="arrow">&nbsp;&rarr;&nbsp;</span>
  <span style="color:var(--accent2)">a<sub>0</sub></span>
  <br>
  <span class="label">Three constants. One frequency. Zero free parameters.</span>
</div>

{''.join(sections)}

<p class="meta">
  Built from
  <a href="https://github.com/nickjoven/proslambenomenos">proslambenomenos</a>,
  <a href="https://github.com/nickjoven/201">201</a>, and
  <a href="https://github.com/nickjoven/intersections">intersections</a>.
  CC0 1.0 — No rights reserved.
</p>

</div>
</body>
</html>"""

    index_path = BUILD_DIR / "index.html"
    index_path.write_text(index_html)
    print(f"  index.html")


def generate_manifest(sources: dict) -> dict:
    """Generate a manifest of source hashes for drift detection."""
    import hashlib
    manifest = {}
    for repo, files in sources.items():
        for path, data in files.items():
            key = f"{repo}/{path}"
            manifest[key] = hashlib.sha256(data).hexdigest()[:16]
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Build the unified proslambenomenos site")
    parser.add_argument("--local", type=str, default=None,
                        help="Path to parent directory containing sibling repos")
    parser.add_argument("--check-only", action="store_true",
                        help="Just verify sources are reachable, don't build")
    args = parser.parse_args()

    local_root = Path(args.local).resolve() if args.local else None

    print("Fetching sources...")
    sources = fetch_sources(local_root)

    if args.check_only:
        total = sum(len(f) for f in sources.values())
        expected = sum(len(c["notebooks"]) + 1 for c in REPOS.values())
        print(f"\n{total}/{expected} files reachable.")
        return 0 if total == expected else 1

    print("\nWriting sources...")
    write_sources(sources)

    print("\nPreparing build directory...")
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)

    print("\nConverting notebooks...")
    converted = convert_notebooks()

    print("\nCopying walkthroughs...")
    copy_walkthroughs()

    print("\nGenerating index...")
    generate_index(converted)

    # Write manifest
    manifest = generate_manifest(sources)
    (BUILD_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nBuild complete: {len(converted)} notebooks, {BUILD_DIR}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
