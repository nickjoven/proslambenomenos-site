# proslambenomenos-site — GitHub Pages Deployment for the Unified Jupyter Book

**Purpose:** Deployed version of the unified Jupyter Book site that aggregates the synchronization-gravity framework across 201, intersections, and proslambenomenos into a single navigable resource.

[**Live site**](https://nickjoven.github.io/proslambenomenos-site/intro.html)

---

## What This Is

This is the GitHub Pages deployment target. The `build.py` script fetches papers, notebooks, and walkthroughs from three source repositories and produces a Jupyter Book. GitHub Actions rebuilds on push.

## Usage

```bash
python build.py                  # fetch from GitHub + build
python build.py --local ../      # use local sibling repos + build
python build.py --fetch-only     # fetch sources, skip jb build
python build.py --check-only     # verify sources are reachable
```

**Requirements:** `pip install -r requirements.txt`

## Structure

```
proslambenomenos-site/
├── build.py            ← Fetch + build script
├── requirements.txt    ← Jupyter Book dependencies
├── notify-site.yml     ← GitHub Actions workflow
└── (built output deployed to gh-pages branch)
```

## Source Repositories

- [201](https://github.com/nickjoven/201) — main framework, sparc_x API, SPARC galaxies
- [intersections](https://github.com/nickjoven/intersections) — stick-slip dynamics, Lagrangian relaxation, CVT
- [proslambenomenos](https://github.com/nickjoven/proslambenomenos) — proslambenomenos frequency, Lyapunov uniqueness, Renzo's Rule (Kuramoto side)
