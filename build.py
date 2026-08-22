#!/usr/bin/env python3
"""Build the proslambenomenos site from ONE source repository at a
PINNED ref. The site holds no claim prose of its own: content is
fetched from nickjoven/proslambenomenos at SOURCE_REF (an evidence
tag), so every deploy traces to a sealed, gate-green tree.

The previous pipeline aggregated four repositories from their moving
main branches on a daily schedule — presentation drift by design. It
is retired; this build is stdlib-only and deterministic given the ref.

Usage:
    python3 build.py                          # clone from GitHub at SOURCE_REF
    python3 build.py --source /path/to/repo   # use a local clone (testing)
    SOURCE_REF=link-006 python3 build.py      # build a newer sealed link
"""

import argparse
import html
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SITE_DIR = Path(__file__).parent
OUT = SITE_DIR / "site"
SOURCE_URL = os.environ.get(
    "SOURCE_URL", "https://github.com/nickjoven/proslambenomenos.git")
SOURCE_REF = os.environ.get("SOURCE_REF", "link-002")


def clone_source(src_arg):
    tmp = Path(tempfile.mkdtemp(prefix="prosl-src-"))
    url = src_arg or SOURCE_URL
    subprocess.run(["git", "clone", "-q", "--branch", SOURCE_REF,
                    "--depth", "1", url, str(tmp / "src")], check=True)
    return tmp / "src"


def claim_census(src: Path) -> str:
    r = subprocess.run([sys.executable, "scripts/check_claims.py"],
                       cwd=src, capture_output=True, text=True, check=False)
    line = (r.stdout or "").strip().splitlines()
    if r.returncode == 0 and line:
        return line[-1]
    return ("census unavailable in this build environment — "
            "run scripts/check_claims.py in the source repository")


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Proslambenomenos</title>
<style>
  body {{ background:#FAFAF7; color:#1C2025; margin:0;
    font-family: Charter, 'Bitstream Charter', Cambria, Georgia, serif;
    font-size:17px; line-height:1.55; }}
  .wrap {{ max-width: 760px; margin:0 auto; padding:3rem 1.25rem 5rem; }}
  h1 {{ font-size:2.4rem; margin:0 0 .3rem; }}
  .sub {{ color:#5A6068; margin:0 0 1.6rem; }}
  .prov {{ border:1px solid #DDDDD4; background:#F1F1EC; border-radius:6px;
    padding:1rem 1.2rem; font-size:.95rem; }}
  a {{ color:#2F4BC7; }}
  ul {{ line-height:1.9; }}
  .census {{ font-family: ui-monospace, Menlo, monospace; font-size:.82rem;
    color:#5A6068; margin-top:2rem; }}
  footer {{ margin-top:3rem; border-top:1px solid #DDDDD4; padding-top:1rem;
    color:#8A9098; font-size:.85rem; }}
</style>
</head>
<body>
<div class="wrap">
<h1>Proslambenomenos</h1>
<p class="sub">The added lowest note — mathematics first, rising only as
far as evidence carries.</p>

<div class="prov">
<strong>Provenance.</strong> An earlier physics framework published
under this name (April&ndash;August 2026) failed adversarial audit;
its physics claims are retracted. Its materials are preserved
unaltered on the
<a href="https://github.com/nickjoven/proslambenomenos/tree/archive/2026-04-framework">archive branch</a>,
and the audit trail lives in the source repository. What remains is
the mathematics that survived, each claim carrying a computed status
and a verification that runs in your browser. Statuses are derived
from recorded evidence by mechanical gates; a green gate is
consistency accounting, not truth. Reds are theorems; greens are not.
</div>

<ul>
  <li><a href="compendium.html"><strong>The compendium</strong></a> —
      every surviving result, stated in standard language, honestly
      labeled (classical / folklore / exercise), with a Verify button
      per claim that can fail.</li>
  <li><a href="{repo}/tree/{ref}">Source repository at {ref}</a> —
      the sealed tree this page was built from: claims, gates,
      fixtures, evaluations.</li>
  <li><a href="{repo}/blob/{ref}/DECLINED.md">Declined derivations</a>,
      <a href="{repo}/blob/{ref}/LITCHECKS.md">literature checks</a>,
      <a href="{repo}/blob/{ref}/LAWCHANGES.md">the constitutional ledger</a>,
      <a href="{repo}/blob/{ref}/notes/adversarial_audit_2026-08-19.md">the adversarial audit</a>.</li>
</ul>

<p class="census">{census}<br>built from {ref}</p>

<footer>This site holds no claim prose of its own; every deploy is
built from a pinned evidence tag of the source repository, after its
gates pass in CI.</footer>
</div>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=None,
                    help="local path to the source repo (testing)")
    args = ap.parse_args()

    src = clone_source(args.source)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    (OUT / ".nojekyll").write_text("")

    shutil.copy(src / "compendium" / "index.html", OUT / "compendium.html")

    repo = "https://github.com/nickjoven/proslambenomenos"
    (OUT / "index.html").write_text(PAGE.format(
        repo=repo, ref=html.escape(SOURCE_REF),
        census=html.escape(claim_census(src))))

    print(f"built site/ from {SOURCE_REF}: index.html + compendium.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
