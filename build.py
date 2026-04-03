#!/usr/bin/env python3
"""Build the unified proslambenomenos site from four source repositories.

Fetches notebooks, markdown, and walkthrough pages from proslambenomenos,
201, intersections, and harmonics, arranges them into a Jupyter Book
structure, and builds an executable HTML site.

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
            "PROOF_C_bridge.md",
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
            "cvt/synthesis.md",
            "cvt/laws/noninjectivity.md",
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
            "RESULTS.md",
            "sync_cost/FRAMEWORK.md",
            "sync_cost/derivations/INDEX.md",
            "sync_cost/derivations/PROOF_A_gravity.md",
            "sync_cost/derivations/PROOF_B_quantum.md",
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
            "sync_cost/derivations/12_continuum_limits.md",
            "sync_cost/derivations/13_einstein_from_kuramoto.md",
            "sync_cost/derivations/14_three_dimensions.md",
            "sync_cost/derivations/15_lie_group_characterization.md",
            "sync_cost/derivations/16_variable_denominator.md",
            "sync_cost/derivations/17_rank1_temporal_causation.md",
            "sync_cost/derivations/18_mobius_container.md",
            "sync_cost/derivations/19_klein_bottle.md",
            "sync_cost/derivations/20_xor_continuum_limit.md",
            "sync_cost/derivations/21_discrete_gauge.md",
            "sync_cost/derivations/22_engineering_targets.md",
            "sync_cost/derivations/23_three_zeros.md",
            "sync_cost/derivations/24_vacuum_energy.md",
            "sync_cost/derivations/25_farey_partition.md",
            "sync_cost/derivations/26_hierarchy.md",
            "sync_cost/derivations/27_exponent.md",
            "sync_cost/derivations/28_farey_proof.md",
            "sync_cost/derivations/29_mediant_derivation.md",
            "sync_cost/derivations/30_denomination_boundary.md",
            "sync_cost/derivations/31_speed_of_light.md",
            "sync_cost/derivations/32_minkowski_signature.md",
            "sync_cost/derivations/33_duty_cycle_dictionary.md",
            "sync_cost/derivations/34_generation_mechanism.md",
            "sync_cost/derivations/35_cosmological_cycle.md",
            "sync_cost/derivations/36_conservation_computability.md",
            "sync_cost/derivations/37_figure_eight.md",
            "sync_cost/derivations/38_boundary_weight.md",
            "sync_cost/derivations/duty_dimension_proof.md",
            "sync_cost/derivations/isotropy_lemma.md",
            "sync_cost/derivations/xor_derivation.md",
            # Python scripts (needed for link resolution and execution)
            "sync_cost/derivations/circle_map.py",
            "sync_cost/derivations/born_rule_tongues.py",
            "sync_cost/derivations/golden_ratio_pivot.py",
            "sync_cost/derivations/stern_brocot_map.py",
            "sync_cost/derivations/phi_squared_zoom.py",
            "sync_cost/derivations/k_omega_mapping.py",
            "sync_cost/derivations/field_equation_cmb.py",
            "sync_cost/derivations/klein_bottle_kuramoto.py",
            "sync_cost/derivations/alphabet_check.py",
            "sync_cost/derivations/sigma_squared.py",
            "sync_cost/derivations/alphabet_depth21.py",
        ],
        "order": 4,
        "title": "Harmonics",
        "subtitle": "Synchronization cost and the mode-locking substrate",
    },
    "stribeck-optics": {
        "github": "nickjoven/stribeck-optics",
        "files": [],
        "order": 5,
        "title": "Stribeck Optics",
        "subtitle": "Optical friction and mode-locking in lenses",
    },
}

# Extra data files needed for notebook execution
DATA_FILES = {
    "201": [
        "data/NGC2403_rotmod.dat",
    ],
    "proslambenomenos": [
        "docs/img/phase_newtonian.png",
        "docs/img/phase_boundary.png",
        "docs/img/phase_deep_mond.png",
        "docs/img/ngc2403_score.png",
        "docs/img/oa_potential.png",
    ],
}

# -- Derivation metadata for machine-readable graph and glossary -----------

DERIVATIONS = {
    0:  {"title": "Recurrence Survival", "status": "derived",
         "claim": "The mediant rule applied to its own first output returns that output: "
                  "F(2) = F(1) + F(0) = 1. The recurrence is a fixed point of itself at "
                  "step zero, establishing that the rule survives self-application before "
                  "the tree begins. D0 is D9 with an empty tree; D9 is D0 with a full tree.",
         "depends": [29]},
    1:  {"title": "Born Rule", "status": "derived",
         "claim": "P = |psi|^2 from basin measure and tongue geometry",
         "depends": [10]},
    2:  {"title": "Spectral Tilt (Original)", "status": "superseded",
         "claim": "CMB tilt from synchronization cost gradient",
         "depends": [],
         "note": "Superseded by Derivation 4"},
    3:  {"title": "MOND Acceleration Scale", "status": "derived",
         "claim": "a_0 = 1.25e-10 m/s^2 from synchronization cost",
         "depends": [9, 11]},
    4:  {"title": "Spectral Tilt (Reframed)", "status": "derived",
         "claim": "n_s from mode-locking structure on Stern-Brocot tree",
         "depends": [10]},
    5:  {"title": "Two Forces", "status": "derived",
         "claim": "Coherence and decoherence as the two structural forces",
         "depends": [10]},
    6:  {"title": "Planck Scale", "status": "derived",
         "claim": "Planck scale from N=3 minimum self-sustaining loop",
         "depends": [10, 14]},
    7:  {"title": "Measurement Collapse", "status": "derived",
         "claim": "Collapse as tongue traversal with duration tau ~ 1/sqrt(epsilon)",
         "depends": [1, 10]},
    8:  {"title": "High-z MOND", "status": "testable",
         "claim": "a_0(z) = cH(z)/(2*pi) tested against high-z surveys",
         "depends": [3, 9]},
    9:  {"title": "Fidelity Bound", "status": "derived",
         "claim": "Self-referential fidelity bound unifying MOND and collapse. "
                  "The mature fixed point: D9 is D0 with a full tree.",
         "depends": [0, 1, 7, 10, 11]},
    10: {"title": "Minimum Alphabet", "status": "derived",
         "claim": "Four irreducible primitives: integers, mediant, fixed-point, parabola",
         "depends": [29]},
    11: {"title": "Rational Field Equation", "status": "derived",
         "claim": "Self-consistency on Stern-Brocot tree in exact rational arithmetic",
         "depends": [10]},
    12: {"title": "Two Continuum Limits", "status": "derived",
         "claim": "K=1 gives ADM/Einstein; K<1 linearized gives Schrodinger/Madelung",
         "depends": [11, 14]},
    13: {"title": "Einstein from Kuramoto", "status": "derived",
         "claim": "Exact ADM from Kuramoto at K=1; uniqueness via Lovelock",
         "depends": [12, 14, 15]},
    14: {"title": "Three Dimensions", "status": "derived",
         "claim": "d=3 forced by mediant -> SL(2,Z) -> SL(2,R) and self-consistent adjacency",
         "depends": [10, 11]},
    15: {"title": "Lie Group Characterization", "status": "derived",
         "claim": "SL(2,R) is the unique continuum substrate via four entrance conditions",
         "depends": [14]},
    16: {"title": "Variable Denominator", "status": "derived",
         "claim": "Hz with changing denominator; de Sitter as orientable fixed point",
         "depends": [9, 11]},
    17: {"title": "Rank-1 Temporal Causation", "status": "derived",
         "claim": "Arrow of time is the rank-1 Frechet factorization of the update map",
         "depends": [11]},
    18: {"title": "Mobius Container", "status": "derived",
         "claim": "Antiperiodic BC forces rational phase divisions from single perturbation",
         "depends": [11, 14]},
    19: {"title": "Klein Bottle", "status": "derived",
         "claim": "XOR parity collapses 1764 mode pairs to 4 survivors at (q1,q2)=(2,3),(3,2)",
         "depends": [18]},
    20: {"title": "XOR Continuum Limit", "status": "derived",
         "claim": "XOR filter dissolves in continuum; frame bundle gives Pin+(3) not SU(3)",
         "depends": [19],
         "note": "Honest negative: does not produce the Standard Model gauge group"},
    21: {"title": "Two Open Paths", "status": "proposed",
         "claim": "Five binary-outcome computations to resolve discrete vs continuous gauge",
         "depends": [20]},
    22: {"title": "Engineering Targets", "status": "proposed",
         "claim": "Four physical devices from established results",
         "depends": [18, 19]},
    23: {"title": "Three Zeros", "status": "derived",
         "claim": "Three structurally distinct zeros yield 1+3 decomposition",
         "depends": [19]},
    24: {"title": "Vacuum Energy", "status": "derived",
         "claim": "Cosmological constant problem dissolves: Klein bottle has exactly 4 modes",
         "depends": [19]},
    25: {"title": "Farey Partition", "status": "derived",
         "claim": "Omega_Lambda = |F_6|/(|F_6|+6) = 13/19 = 0.6842 (observed: 0.685)",
         "depends": [19, 28]},
    26: {"title": "Hierarchy", "status": "derived",
         "claim": "Planck/Hubble ratio R = 6 * 13^54 (residual 0.48%)",
         "depends": [25, 27]},
    27: {"title": "Exponent", "status": "derived",
         "claim": "Exponent 54 = q2 * q3^d derived from spatial dimension and Klein bottle",
         "depends": [14, 19]},
    28: {"title": "Farey Proof", "status": "derived",
         "claim": "SO(2) structure at locked/unlocked boundary forces Farey counting",
         "depends": [19, 11]},
    29: {"title": "Mediant Derivation", "status": "derived",
         "claim": "Mediant is the unique operation satisfying three simultaneous constraints",
         "depends": []},
}

GLOSSARY = {
    "proslambenomenos": {
        "symbol": "nu_Lambda",
        "definition": "The reference frequency set by the cosmological constant: "
                      "nu_Lambda = c*sqrt(Lambda/3). The lowest tone in the system, from "
                      "which the Hubble rate and MOND scale are overtones. Named after the "
                      "lowest tone in the ancient Greek Greater Perfect System.",
    },
    "golden ratio": {
        "symbol": "phi",
        "definition": "The positive root of x^2 - x - 1 = 0, equal to (1+sqrt(5))/2. "
                      "The most irrational number; sits at the widest gap in the devil's staircase.",
        "aka": ["phi"],
    },
    "Stern-Brocot tree": {
        "definition": "The complete binary tree of all positive rationals, built by iterated "
                      "mediants starting from 0/1 and 1/0. The natural coordinate system for "
                      "the devil's staircase.",
    },
    "devil's staircase": {
        "definition": "The winding number W(Omega) of the circle map as a function of driving "
                      "frequency. A continuous, monotone function that is locally constant almost "
                      "everywhere (on the Arnold tongues) yet maps [0,1] onto [0,1].",
    },
    "Arnold tongue": {
        "definition": "A region in (Omega, K) parameter space where the circle map locks to "
                      "a rational winding number p/q. Width scales as K^q at small coupling.",
    },
    "mode-locking": {
        "definition": "The phenomenon where a driven oscillator synchronizes to a rational "
                      "multiple of the driving frequency. The locked states form the Arnold tongues.",
    },
    "Kuramoto model": {
        "definition": "A system of N coupled phase oscillators: d(theta_i)/dt = omega_i + "
                      "(K/N) sum sin(theta_j - theta_i). The mean-field model of synchronization.",
    },
    "mediant": {
        "definition": "The operation (a+c)/(b+d) on two fractions a/b and c/d. Derived in D29 "
                      "as the unique operation satisfying monotonicity, denominator-additivity, "
                      "and convergent-stability.",
        "derivation": 29,
    },
    "Born rule": {
        "definition": "The quantum measurement postulate P = |psi|^2. Here derived (D1) from "
                      "saddle-node universality at Arnold tongue boundaries: Delta(theta) ~ sqrt(epsilon).",
        "derivation": 1,
    },
    "order parameter": {
        "symbol": "r",
        "definition": "The magnitude of the mean field r*exp(i*psi) = (1/N) sum exp(i*theta_j). "
                      "r=1 means full synchronization (K=1, gravity); r<1 means partial (K<1, QM).",
    },
    "ADM formalism": {
        "definition": "The Arnowitt-Deser-Misner 3+1 decomposition of general relativity. "
                      "Spacetime is foliated into spatial slices with lapse N, shift N^i, "
                      "and 3-metric gamma_ij.",
    },
    "Lovelock theorem": {
        "definition": "In 4D, the only divergence-free symmetric rank-2 tensor built from the "
                      "metric and its first two derivatives is G_mu_nu + Lambda*g_mu_nu. "
                      "Forces Einstein's equation uniquely at K=1 (D13).",
        "derivation": 13,
    },
    "Madelung transform": {
        "definition": "Writing Psi = sqrt(rho)*exp(iS/hbar), converting Schrodinger into "
                      "continuity + Hamilton-Jacobi with a quantum pressure term. "
                      "The K<1 continuum limit of the field equation (D12).",
        "derivation": 12,
    },
    "Farey sequence": {
        "symbol": "F_n",
        "definition": "The ascending sequence of reduced fractions p/q in [0,1] with q <= n. "
                      "|F_6| = 13 determines the dark energy fraction Omega_Lambda = 13/19 (D25).",
        "derivation": 25,
    },
    "Klein bottle": {
        "definition": "A closed non-orientable surface: two antiperiodic directions with XOR "
                      "parity. The configuration space that collapses 1764 mode pairs to exactly "
                      "4 survivors (D19).",
        "derivation": 19,
    },
    "fidelity bound": {
        "definition": "The self-referential constraint: the measurement instrument IS the "
                      "measured dynamics. Unifies MOND transition and wavefunction collapse (D9).",
        "derivation": 9,
    },
    "MOND": {
        "definition": "Modified Newtonian Dynamics. Below acceleration a_0, gravitational "
                      "dynamics deviate from Newton. Here a_0 = cH_0/(2*pi) is derived from "
                      "the proslambenomenos frequency, not postulated (D3).",
        "derivation": 3,
    },
    "spectral tilt": {
        "symbol": "n_s",
        "definition": "The scalar spectral index of primordial perturbations. n_s = 1 is "
                      "scale-invariant; observed n_s ~ 0.965. Derived from Stern-Brocot "
                      "level sampling rate (D4).",
        "derivation": 4,
    },
    "SL(2,R)": {
        "definition": "The group of 2x2 real matrices with determinant 1. The unique "
                      "continuum substrate: mediant -> SL(2,Z) -> SL(2,R). Its dimension "
                      "(2^2 - 1 = 3) forces d=3 spatial dimensions (D14, D15).",
        "derivation": 15,
    },
    "circle map": {
        "definition": "theta_{n+1} = theta_n + Omega - (K/2*pi)*sin(2*pi*theta_n). "
                      "The simplest model exhibiting mode-locking, Arnold tongues, "
                      "and the devil's staircase.",
    },
    "rational field equation": {
        "definition": "N(p/q) = N_total * g(p/q) * w(p/q, K_0*F[N]) on the Stern-Brocot "
                      "tree. The self-consistency condition whose K=1 limit is Einstein "
                      "and K<1 limit is Schrodinger (D11).",
        "derivation": 11,
    },
    "recurrence survival": {
        "definition": "D0: the mediant rule applied to its own first output returns that "
                      "output. F(2) = F(1) + F(0) = 1. The rule survives self-application "
                      "before the tree begins. D0 is D9 with an empty tree.",
        "derivation": 0,
    },
    "Stribeck curve": {
        "definition": "The friction coefficient as a function of sliding velocity. "
                      "Exhibits stick-slip transitions analogous to synchronization "
                      "onset in the Kuramoto model.",
    },
    "Lyapunov functional": {
        "definition": "A function that decreases monotonically along system trajectories, "
                      "proving convergence to a unique steady state. Used to establish "
                      "uniqueness of the proslambenomenos frequency (D9).",
    },
    "Ott-Antonsen reduction": {
        "definition": "An exact dimensional reduction for Kuramoto systems with Lorentzian "
                      "frequency distributions. Reduces infinite-dimensional dynamics to a "
                      "single complex ODE for the order parameter.",
    },
    "cosmological constant": {
        "symbol": "Lambda",
        "definition": "The vacuum energy density parameter Lambda ~ 1.1e-52 m^-2. Sets the "
                      "proslambenomenos frequency and, through it, the Hubble rate and MOND scale.",
    },
    "SPARC": {
        "definition": "Spitzer Photometry and Accurate Rotation Curves. A database of 175 "
                      "galaxies with high-quality rotation curves used to test the framework's "
                      "predictions against observed dynamics.",
    },
}

# -- Static assets to include (HTMLs, GIFs, PNGs, scripts) -------------------

STATIC_ASSETS = {
    "harmonics": {
        "github": "nickjoven/harmonics",
        "files": [
            # GIF animations
            "stairs.gif",
            "triangles.gif",
            "orbit.gif",
            "spiral.gif",
            "rose.gif",
            # Interactive HTML apps
            "sync_cost/applications/stern_brocot_walk.html",
            "sync_cost/applications/ontology.html",
            "sync_cost/applications/mobius_views.html",
            "sync_cost/applications/mobius_projector.html",
            "sync_cost/derivations/our_address.html",
            # Key Python scripts (referenced in derivation docs)
            "sync_cost/derivations/circle_map.py",
            "sync_cost/derivations/born_rule_tongues.py",
            "sync_cost/derivations/golden_ratio_pivot.py",
            "sync_cost/derivations/stern_brocot_map.py",
            "sync_cost/derivations/phi_squared_zoom.py",
            "sync_cost/derivations/k_omega_mapping.py",
            "sync_cost/derivations/field_equation_cmb.py",
            "sync_cost/derivations/klein_bottle_kuramoto.py",
            "sync_cost/derivations/alphabet_check.py",
            "sync_cost/derivations/sigma_squared.py",
            "sync_cost/derivations/alphabet_depth21.py",
        ],
    },
    "proslambenomenos": {
        "github": "nickjoven/proslambenomenos",
        "files": [
            "docs/img/phase_newtonian.png",
            "docs/img/phase_boundary.png",
            "docs/img/phase_deep_mond.png",
            "docs/img/ngc2403_score.png",
            "docs/img/oa_potential.png",
        ],
    },
    "stribeck-optics": {
        "github": "nickjoven/stribeck-optics",
        "files": [
            "docs/index.html",
            "stribeck_optics_results.png",
        ],
    },
}

# Mapping from repo name to GitHub base URL for script link resolution
REPO_GITHUB_URLS = {
    "harmonics": "https://github.com/nickjoven/harmonics/blob/main",
    "proslambenomenos": "https://github.com/nickjoven/proslambenomenos/blob/main",
    "201": "https://github.com/nickjoven/201/blob/main",
    "intersections": "https://github.com/nickjoven/intersections/blob/main",
    "rfe": "https://github.com/nickjoven/rfe/blob/main",
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


def fetch_static_assets(local_root: Path | None = None) -> dict:
    """Fetch static assets (HTML, GIF, PNG). Returns {repo: {path: bytes}}."""
    result = {}
    for name, cfg in STATIC_ASSETS.items():
        result[name] = {}
        slug = cfg["github"]
        for path in cfg["files"]:
            try:
                if local_root:
                    data = fetch_file_local(local_root, name, path)
                else:
                    data = fetch_file_github(slug, path)
                result[name][path] = data
                print(f"  {name}/{path} (static)")
            except (FileNotFoundError, URLError, OSError) as e:
                print(f"  {name}/{path} — MISSING ({e})")
    return result


def copy_static_assets(static_sources: dict):
    """Copy fetched static assets into book/_static/."""
    static_dir = BOOK_DIR / "_static"
    static_dir.mkdir(parents=True, exist_ok=True)
    for repo, files in static_sources.items():
        for path, data in files.items():
            # Flatten into _static/ using just the filename
            filename = Path(path).name
            dest = static_dir / filename
            dest.write_bytes(data)
            print(f"  _static/{filename}")


def write_book_sources(sources: dict):
    """Write fetched sources into the Jupyter Book directory structure."""
    if BOOK_DIR.exists():
        shutil.rmtree(BOOK_DIR)

    for repo, files in sources.items():
        for path, data in files.items():
            dest = BOOK_DIR / repo / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)

    # Copy local content files
    content_dir = SITE_DIR / "content"
    if content_dir.exists():
        for f in content_dir.iterdir():
            dest = BOOK_DIR / f.name
            shutil.copy2(f, dest)
            print(f"  {f.name} (local)")


def resolve_script_references():
    """Rewrite .py script references and internal .md cross-references in book markdown.

    After write_book_sources() copies raw files into the book directory, local
    references like `born_rule_tongues.py` or `[text](PROOF_A_gravity.md)` break
    because those files aren't in the book.  This pass converts them to GitHub
    links or corrected relative paths.
    """
    import re

    # --- GitHub URL mappings keyed by book subdirectory prefix ---
    SCRIPT_MAPS = [
        ("harmonics/sync_cost/derivations/",
         "https://github.com/nickjoven/harmonics/blob/main/sync_cost/derivations/"),
        ("harmonics/seed/src/",
         "https://github.com/nickjoven/harmonics/blob/main/seed/src/"),
        ("harmonics/",
         "https://github.com/nickjoven/harmonics/blob/main/"),
        ("201/",
         "https://github.com/nickjoven/201/blob/main/"),
        ("intersections/",
         "https://github.com/nickjoven/intersections/blob/main/"),
        ("proslambenomenos/",
         "https://github.com/nickjoven/proslambenomenos/blob/main/"),
    ]

    def _github_url_for(book_rel_path, script_name):
        """Given a file's path relative to BOOK_DIR, return the GitHub URL for a script."""
        for prefix, base_url in SCRIPT_MAPS:
            if book_rel_path.startswith(prefix):
                return base_url + script_name
        return None

    # Build a lookup: filename -> book-relative path for all .md files in the book
    md_index = {}
    for md_path in BOOK_DIR.rglob("*.md"):
        rel = md_path.relative_to(BOOK_DIR).as_posix()
        md_index.setdefault(md_path.name, []).append(rel)

    def _resolve_md_ref(book_rel_path, target):
        """Resolve a .md reference to a correct relative path within the book."""
        target_name = Path(target).name
        candidates = md_index.get(target_name, [])
        if not candidates:
            return None
        current_dir = str(Path(book_rel_path).parent)
        # Same directory? Already correct as a bare filename.
        for c in candidates:
            if str(Path(c).parent) == current_dir:
                return target_name
        # Otherwise compute relative path from the file's directory
        from_dir = Path(book_rel_path).parent
        best = Path(candidates[0])
        return os.path.relpath(best, from_dir)

    count_scripts = 0
    count_md_refs = 0

    for md_file in BOOK_DIR.rglob("*.md"):
        book_rel = md_file.relative_to(BOOK_DIR).as_posix()
        text = md_file.read_text(encoding="utf-8", errors="replace")
        original = text

        # 1) Fix markdown links to .py files: [text](script.py) -> [text](github_url)
        def _replace_link_py(m):
            nonlocal count_scripts
            full_match = m.group(0)
            link_text = m.group(1)
            script = m.group(2)
            if script.startswith(("http://", "https://")):
                return full_match
            url = _github_url_for(book_rel, script)
            if url:
                count_scripts += 1
                return f"[{link_text}]({url})"
            return full_match

        text = re.sub(r'\[([^\]]*)\]\(([^)]*\.py)\)', _replace_link_py, text)

        # 2) Fix backtick-wrapped .py references: `script.py` -> [`script.py`](github_url)
        #    Skip if already inside a markdown link [...](...) structure
        def _replace_backtick_py(m):
            nonlocal count_scripts
            prefix = m.group(1)
            script = m.group(2)
            if prefix.endswith("](") or prefix.endswith("["):
                return m.group(0)
            url = _github_url_for(book_rel, script)
            if url:
                count_scripts += 1
                return f"{prefix}[`{script}`]({url})"
            return m.group(0)

        text = re.sub(r'(^|[^[\](])`([a-zA-Z_]\w*\.py)`', _replace_backtick_py, text,
                       flags=re.MULTILINE)

        # 3) Fix internal .md cross-references: [text](file.md) -> corrected relative path
        #    Only fix bare filenames or simple relative refs, not URLs
        def _replace_link_md(m):
            nonlocal count_md_refs
            full_match = m.group(0)
            link_text = m.group(1)
            target = m.group(2)
            if target.startswith(("http://", "https://")):
                return full_match
            target_name = Path(target).name
            if not target_name.endswith(".md"):
                return full_match
            resolved = _resolve_md_ref(book_rel, target)
            if resolved and resolved != target:
                count_md_refs += 1
                return f"[{link_text}]({resolved})"
            return full_match

        text = re.sub(r'\[([^\]]*)\]\(([^)]*\.md)\)', _replace_link_md, text)

        if text != original:
            md_file.write_text(text, encoding="utf-8")

    print(f"  Resolved {count_scripts} script references, {count_md_refs} internal .md cross-references")


def resolve_doc_crossrefs():
    """Rewrite Sphinx {doc} cross-references to plain markdown links.

    Reference pages (equations.md etc.) fetched from submediant-site use
    {doc}`category/filename` syntax that assumes a directory layout this
    book doesn't have.  Convert them to relative markdown links pointing
    at the actual book paths.
    """
    import re

    # Build a lookup: bare filename (no extension) -> book-relative path
    page_index = {}
    for md_path in BOOK_DIR.rglob("*.md"):
        rel = md_path.relative_to(BOOK_DIR).as_posix()
        stem = md_path.stem
        page_index.setdefault(stem, []).append(rel)

    count = 0
    for md_file in BOOK_DIR.glob("*.md"):  # reference pages live at book root
        text = md_file.read_text(encoding="utf-8", errors="replace")
        original = text

        def _replace_doc_ref(m):
            nonlocal count
            ref_path = m.group(1)
            # Extract the filename stem (last component, no extension)
            stem = ref_path.rsplit("/", 1)[-1]
            candidates = page_index.get(stem, [])
            if candidates:
                target = candidates[0]
                count += 1
                return f"[{stem}]({target})"
            # If not found, try proslambenomenos repo mapping
            if stem == "proslambenomenos":
                candidates = page_index.get("proslambenomenos", [])
                if candidates:
                    target = candidates[0]
                    count += 1
                    return f"[{stem}]({target})"
            # Convert to plain text to avoid Sphinx build errors
            return stem.replace("_", " ").title()

        text = re.sub(r'\{doc\}`([^`]+)`', _replace_doc_ref, text)

        if text != original:
            md_file.write_text(text, encoding="utf-8")

    print(f"  Resolved {count} {{doc}} cross-references in reference pages")


def fetch_static_assets(local_root: Path | None = None) -> dict:
    """Fetch static assets (GIFs, HTMLs, PNGs, scripts). Returns {repo: {path: bytes}}."""
    result = {}
    for name, cfg in STATIC_ASSETS.items():
        result[name] = {}
        slug = cfg["github"]
        for path in cfg["files"]:
            try:
                if local_root:
                    data = fetch_file_local(local_root, name, path)
                else:
                    data = fetch_file_github(slug, path)
                result[name][path] = data
                print(f"  {name}/{path} (static)")
            except (FileNotFoundError, URLError, OSError) as e:
                print(f"  {name}/{path} — MISSING ({e})")
    return result


def copy_static_assets(static_sources: dict):
    """Copy fetched static assets into book/_static/assets/."""
    static_dir = BOOK_DIR / "_static" / "assets"
    static_dir.mkdir(parents=True, exist_ok=True)
    for repo, files in static_sources.items():
        for path, data in files.items():
            filename = Path(path).name
            dest = static_dir / filename
            dest.write_bytes(data)
            print(f"  _static/assets/{filename}")


def _sidebar_title(file_key: str) -> str | None:
    """Return a clean sidebar title if the filename has a numeric prefix.

    Strips leading 'NN_' from the basename and converts to title case.
    Returns None if no cleanup is needed (no numeric prefix).
    """
    import re
    basename = file_key.rsplit("/", 1)[-1]
    m = re.match(r"^\d+_(.+)$", basename)
    if not m:
        return None
    clean = m.group(1).replace("_", " ").title()
    # Fix common acronyms/terms that title-case mangles
    fixes = {
        "Sparc": "SPARC", "Cmb": "CMB", "Qcd": "QCD", "Uv": "UV",
        "A0": "a₀", "Born": "Born", "Mond": "MOND",
    }
    for wrong, right in fixes.items():
        clean = clean.replace(wrong, right)
    return clean


def generate_glossary_page():
    """Generate glossary.md — copy from submediant canonical if available, else generate."""
    # Prefer submediant canonical glossary (with semantic categories)
    ref_source = SITE_DIR.parent / "submediant" / "reference" / "glossary.md"
    if ref_source.exists():
        (BOOK_DIR / "glossary.md").write_text(ref_source.read_text())
        print("  glossary.md (local)")
        return

    # Fallback: fetch from GitHub
    url = "https://raw.githubusercontent.com/nickjoven/submediant-site/main/reference/glossary.md"
    try:
        content = urlopen(Request(url), timeout=15).read().decode("utf-8")
        (BOOK_DIR / "glossary.md").write_text(content)
        print("  glossary.md (github)")
        return
    except (URLError, OSError):
        pass

    # Last resort: generate from GLOSSARY dict
    lines = ["# Glossary", "", "Terms defined in the context of the synchronization framework.", "", "---", ""]
    for term in sorted(GLOSSARY.keys(), key=str.lower):
        entry = GLOSSARY[term]
        lines.append(f"**{term}**")
        lines.append(f": {entry['definition']}")
        lines.append("")
    (BOOK_DIR / "glossary.md").write_text("\n".join(lines))
    print("  glossary.md (generated)")


def generate_reference_pages():
    """Copy reference pages from submediant — local first, then GitHub."""
    ref_source = SITE_DIR.parent / "submediant" / "reference"
    for fname in ["graph.md", "equations.md", "visuals.md"]:
        content = None
        # Try local sibling first
        src = ref_source / fname if ref_source.exists() else None
        if src and src.exists():
            content = src.read_text()
            print(f"  {fname} (local)")
        else:
            # Fetch from GitHub raw
            url = f"https://raw.githubusercontent.com/nickjoven/submediant-site/main/reference/{fname}"
            try:
                content = urlopen(Request(url), timeout=15).read().decode("utf-8")
                print(f"  {fname} (github)")
            except (URLError, OSError) as e:
                print(f"  {fname} — FAILED ({e})")
        if content:
            (BOOK_DIR / fname).write_text(content)
        else:
            title = fname.replace(".md", "").replace("_", " ").title()
            (BOOK_DIR / fname).write_text(f"# {title}\n\nReference page not available.\n")
            print(f"  {fname} (stub)")


def generate_toc():
    """Generate _toc.yml for Jupyter Book.

    Sidebar rule: ≤8 items visible at any level. First file in each repo
    is the top-level chapter; rest nest as sections (collapsed by default).
    """
    lines = [
        "format: jb-book",
        "root: intro",
        "parts:",
    ]

    for name, cfg in sorted(REPOS.items(), key=lambda x: x[1]["order"]):
        all_files = []
        for f in cfg["files"]:
            if f.endswith(".md"):
                all_files.append(f"{name}/{f.removesuffix('.md')}")
            elif f.endswith(".ipynb"):
                all_files.append(f"{name}/{f.removesuffix('.ipynb')}")

        if not all_files:
            continue

        lines.append(f"  - caption: \"{cfg['title']}\"")
        lines.append("    chapters:")

        # First file is the entry point (visible in sidebar)
        entry = all_files[0]
        lines.append(f"      - file: {entry}")
        title = _sidebar_title(entry)
        if title:
            lines.append(f"        title: \"{title}\"")

        # Rest nest as sections under the entry (collapsed)
        if len(all_files) > 1:
            lines.append("        sections:")
            for f in all_files[1:]:
                lines.append(f"          - file: {f}")
                t = _sidebar_title(f)
                if t:
                    lines.append(f"            title: \"{t}\"")

    # Local content (Observatory)
    content_dir = SITE_DIR / "content"
    if content_dir.exists():
        local_files = sorted(content_dir.iterdir())
        if local_files:
            lines.append('  - caption: "Observatory"')
            lines.append("    chapters:")
            for f in local_files:
                lines.append(f"      - file: {f.stem}")

    # Reference: graph, equations, visuals, glossary
    lines.append('  - caption: "Reference"')
    lines.append("    chapters:")
    lines.append('      - file: graph')
    lines.append('        title: "Derivation Graph"')
    lines.append('      - file: equations')
    lines.append('        title: "Key Equations"')
    lines.append('      - file: visuals')
    lines.append('        title: "Visual Assets"')
    lines.append("      - file: glossary")

    toc_path = BOOK_DIR / "_toc.yml"
    toc_path.write_text("\n".join(lines) + "\n")
    print(f"  _toc.yml")


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
  url: https://github.com/nickjoven/proslambenomenos

html:
  use_issues_button: false
  use_repository_button: true
  use_edit_page_button: false
  favicon: ""
  extra_css:
    - _static/glossary.css

sphinx:
  config:
    mathjax3_config:
      tex:
        macros:
          "RR": "\\\\mathbb{R}"
          "NN": "\\\\mathbb{N}"
    html_css_files:
      - https://nickjoven.github.io/submediant-site/_static/mobius-theme.css
      - _static/custom.css
    html_js_files:
      - glossary.js
      - https://nickjoven.github.io/submediant-site/_static/mobius-theme.js
    html_theme_options:
      navigation_with_keys: false
      collapse_navigation: true
      show_nav_level: 1
      navigation_depth: 2
      icon_links:
        - name: GitHub
          url: https://github.com/nickjoven
          icon: fa-brands fa-github
"""
    (BOOK_DIR / "_config.yml").write_text(config)

    # Custom CSS for dark-ish accents
    static_dir = BOOK_DIR / "_static"
    static_dir.mkdir(exist_ok=True)
    (static_dir / "custom.css").write_text("""\
/* Prevent mobile browsers from resizing text on scroll (address-bar collapse) */
html {
  -webkit-text-size-adjust: 100%;
  text-size-adjust: 100%;
}

/* Accent colors matching the walkthrough pages */
:root {
  --pst-color-primary: #58a6ff;
  --pst-color-secondary: #7ee787;
}

/* Scrollable math blocks on narrow screens (display math only) */
@media screen and (max-width: 992px) {
  mjx-container[display="true"] {
    overflow-x: auto;
    display: block;
  }
}

/* Mobile portrait */
@media screen and (max-width: 768px) and (orientation: portrait) {
  .bd-main .bd-content .bd-article-container {
    padding-left: 0.75rem;
    padding-right: 0.75rem;
  }
}

/* Mobile / tablet landscape */
@media screen and (max-width: 992px) and (orientation: landscape) {
  .bd-main .bd-content .bd-article-container {
    padding-left: 1rem;
    padding-right: 1rem;
  }
  .bd-main .bd-content .bd-article-container .bd-article {
    max-width: min(65ch, 100%);
    margin: 0 auto;
  }
  .bd-sidebar-primary {
    display: none !important;
  }
  .bd-header .navbar-header-items {
    display: flex !important;
  }
  #glossary-toggle {
    bottom: 8px;
    right: 8px;
    padding: 4px 8px;
    font-size: 0.7rem;
  }
}
""")

    # Mobius theme loaded from submediant-site canonical URL (no local copy)

    print("  _config.yml")


def generate_intro():
    """Generate the intro/landing page."""
    intro = """\
# Proslambenomenos

[N. Joven](https://github.com/nickjoven) — 2026 — [ORCID 0009-0008-0679-0812](https://orcid.org/0009-0008-0679-0812) — CC0 1.0

Source: [proslambenomenos](https://github.com/nickjoven/proslambenomenos) | [harmonics](https://github.com/nickjoven/harmonics) | [201](https://github.com/nickjoven/201) | [intersections](https://github.com/nickjoven/intersections)

---

A pendulum swings. A planet orbits. A galaxy rotates.

At some point, these motions become so slow — so close to the expansion
rate of the universe itself — that the distinction between "orbiting"
and "drifting" breaks down. That threshold has a name in astronomy:
the MOND acceleration scale, $a_0 \\approx 1.2 \\times 10^{-10}$ m/s$^2$.

Below this acceleration, galaxies stop behaving the way Newton predicts.
Rotation curves flatten. The missing-mass problem appears. This has been
known since the 1980s. What hasn't been settled is *why that particular number*.

In ancient Greek music theory, the *proslambenomenos* was the lowest tone in
the Greater Perfect System — the reference pitch from which every interval
was measured. It turns out there's a physical analogue.

The cosmological constant $\\Lambda$ sets a frequency. The Hubble rate $H_0$
is an overtone. And the MOND scale is the next one down:

$$\\Lambda \\;\\xrightarrow{c\\sqrt{\\cdot/3}}\\; \\nu_\\Lambda
  \\;\\xrightarrow{\\div\\sqrt{\\Omega_\\Lambda}}\\; H_0
  \\;\\xrightarrow{c/2\\pi}\\; a_0$$

No free parameters. The predicted value is $1.04 \\times 10^{-10}$ m/s$^2$.
The measured value is $1.2 \\times 10^{-10}$ m/s$^2$. The ratio is 1.15 —
within the range set by the shape of the galactic frequency distribution.

This site presents the derivation, the numerical evidence across 175
galaxies, and the physical mechanism — oscillators synchronizing through
friction, the same dynamics that make a violin string sing or a
geological fault slip.

## Where to start

- **The short version**: [Proslambenomenos](proslambenomenos/proslambenomenos.html) —
  the derivation in one document
- **The numbers**: [201](201/joven_unifying_framework.html) —
  175 SPARC-X galaxies, predicted vs. observed rotation curves
- **The mechanism**: [Intersections](intersections/joven_stick_slip_dark_matter.html) —
  stick-slip dynamics, why synchronization produces flat rotation curves
- **The full framework**: [Harmonics](harmonics/sync_cost/FRAMEWORK.html) —
  30 derivations (D0–D29), from counting to Einstein
- **Where are we?** [Our Address](https://nickjoven.github.io/submediant-site/our_address.html) —
  the universe's computational clock on the Stern-Brocot tree
- **From scratch?** [First Principles](https://nickjoven.github.io/submediant-site/first-principles.html) —
  sin(\u03c9t) to Einstein in 10 steps
- **The math?** [Oscillations](https://nickjoven.github.io/submediant-site/oscillations.html) —
  47 oscillations, pure math of 1/\u03c6

## Source

- [proslambenomenos](https://github.com/nickjoven/proslambenomenos) — the self-contained preprint
- [201](https://github.com/nickjoven/201) — the numerical framework
- [intersections](https://github.com/nickjoven/intersections) — the physical substrate
- [harmonics](https://github.com/nickjoven/harmonics) — the synchronization cost derivations

All notebooks on this site are **executed during build** — you can verify
every number yourself.
"""
    (BOOK_DIR / "intro.md").write_text(intro)
    print("  intro.md")


def generate_derivation_graph():
    """Generate machine-readable derivation graph as JSON and JSON-LD."""
    static_dir = BOOK_DIR / "_static"
    static_dir.mkdir(exist_ok=True)

    graph = {
        "title": "Proslambenomenos Derivation Chain",
        "description": "30 derivations (D0-D29) from recurrence survival to general relativity and quantum mechanics",
        "author": "N. Joven",
        "license": "CC0 1.0",
        "derivation_count": len(DERIVATIONS),
        "free_parameters": 0,
        "free_functions": 0,
        "derivations": {},
        "edges": [],
    }
    for num, d in sorted(DERIVATIONS.items()):
        node = {
            "number": num,
            "title": d["title"],
            "status": d["status"],
            "claim": d["claim"],
            "depends_on": d["depends"],
        }
        if "note" in d:
            node["note"] = d["note"]
        graph["derivations"][str(num)] = node
        for dep in d["depends"]:
            graph["edges"].append({"from": dep, "to": num})

    (static_dir / "derivation-graph.json").write_text(
        json.dumps(graph, indent=2))
    print("  _static/derivation-graph.json")

    jsonld = {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        "name": "Proslambenomenos",
        "author": {"@type": "Person", "name": "N. Joven",
                    "identifier": "https://orcid.org/0009-0008-0679-0812"},
        "license": "https://creativecommons.org/publicdomain/zero/1.0/",
        "description": (
            "A unified site deriving the MOND acceleration scale from the "
            "cosmological constant via synchronization dynamics, with "
            "numerical evidence across 175 SPARC galaxies."
        ),
        "hasPart": [
            {"@type": "Chapter", "name": f"Derivation {n}: {d['title']}",
             "position": n, "description": d["claim"]}
            for n, d in sorted(DERIVATIONS.items())
        ],
    }
    (static_dir / "jsonld.json").write_text(json.dumps(jsonld, indent=2))
    print("  _static/jsonld.json")


def generate_glossary():
    """Generate glossary data file and tooltip JS/CSS (off by default)."""
    static_dir = BOOK_DIR / "_static"
    static_dir.mkdir(exist_ok=True)

    glossary_data = {}
    for term, entry in GLOSSARY.items():
        glossary_data[term] = {
            "definition": entry["definition"],
        }
        if "symbol" in entry:
            glossary_data[term]["symbol"] = entry["symbol"]
        if "derivation" in entry:
            glossary_data[term]["derivation"] = entry["derivation"]
        if "aka" in entry:
            glossary_data[term]["aka"] = entry["aka"]
    (static_dir / "glossary.json").write_text(
        json.dumps(glossary_data, indent=2))
    print("  _static/glossary.json")

    tooltip_css = """\
/* Glossary tooltip styles — active only when [data-glossary="on"] is set on <html> */
html[data-glossary="on"] .glossary-term {
  border-bottom: 1px dotted var(--pst-color-secondary, #7ee787);
  cursor: help;
  position: relative;
}
html:not([data-glossary="on"]) .glossary-term {
  /* No visual change when glossary is off */
}
.glossary-tooltip {
  display: none;
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: var(--pst-color-surface, #1e1e2e);
  color: var(--pst-color-text-base, #cdd6f4);
  border: 1px solid var(--pst-color-border, #45475a);
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 0.85rem;
  line-height: 1.4;
  max-width: 360px;
  min-width: 200px;
  z-index: 1000;
  white-space: normal;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  pointer-events: none;
}
html[data-glossary="on"] .glossary-term:hover .glossary-tooltip,
html[data-glossary="on"] .glossary-term:focus .glossary-tooltip {
  display: block;
}
.glossary-tooltip .glossary-ref {
  display: block;
  margin-top: 4px;
  font-size: 0.8em;
  opacity: 0.7;
}
#glossary-toggle {
  position: fixed;
  bottom: 16px;
  right: 16px;
  z-index: 999;
  background: var(--pst-color-surface, #1e1e2e);
  color: var(--pst-color-text-base, #cdd6f4);
  border: 1px solid var(--pst-color-border, #45475a);
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 0.8rem;
  cursor: pointer;
  opacity: 0.6;
  transition: opacity 0.2s;
}
#glossary-toggle:hover {
  opacity: 1;
}
"""
    (static_dir / "glossary.css").write_text(tooltip_css)
    print("  _static/glossary.css")

    tooltip_js = """\
(function() {
  "use strict";

  var GLOSSARY = null;
  var ACTIVE = localStorage.getItem("glossary") === "on";

  function applyState() {
    document.documentElement.setAttribute("data-glossary", ACTIVE ? "on" : "off");
    var btn = document.getElementById("glossary-toggle");
    if (btn) btn.textContent = ACTIVE ? "Glossary: ON" : "Glossary: OFF";
  }

  function createToggle() {
    var btn = document.createElement("button");
    btn.id = "glossary-toggle";
    btn.type = "button";
    btn.addEventListener("click", function() {
      ACTIVE = !ACTIVE;
      localStorage.setItem("glossary", ACTIVE ? "on" : "off");
      applyState();
    });
    document.body.appendChild(btn);
  }

  function escapeRegex(s) {
    return s.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&");
  }

  function annotateNode(textNode) {
    var text = textNode.nodeValue;
    if (!text || !text.trim()) return;
    var parent = textNode.parentElement;
    if (!parent) return;
    var tag = parent.tagName;
    if (tag === "CODE" || tag === "PRE" || tag === "SCRIPT" || tag === "STYLE") return;
    if (parent.closest(".glossary-term, .glossary-tooltip, .MathJax, mjx-container, .math, h1, h2, h3")) return;
    // Skip text that contains unprocessed LaTeX delimiters
    if (/\\$|\\\\[a-zA-Z]/.test(text)) return;

    var allPatterns = [];
    Object.keys(GLOSSARY).forEach(function(term) {
      allPatterns.push({ pattern: term, key: term });
      var entry = GLOSSARY[term];
      if (entry.aka) {
        entry.aka.forEach(function(a) { allPatterns.push({ pattern: a, key: term }); });
      }
    });
    allPatterns.sort(function(a, b) { return b.pattern.length - a.pattern.length; });

    var parts = allPatterns.map(function(p) { return escapeRegex(p.pattern); });
    if (!parts.length) return;
    var regex = new RegExp("\\\\b(" + parts.join("|") + ")\\\\b", "gi");
    if (!regex.test(text)) return;

    var lookup = {};
    allPatterns.forEach(function(p) { lookup[p.pattern.toLowerCase()] = p.key; });

    var fragment = document.createDocumentFragment();
    var lastIndex = 0;
    regex.lastIndex = 0;
    var match;
    var replaced = false;
    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        fragment.appendChild(document.createTextNode(text.slice(lastIndex, match.index)));
      }
      var matched = match[0];
      var key = lookup[matched.toLowerCase()];
      var entry = GLOSSARY[key];
      var span = document.createElement("span");
      span.className = "glossary-term";
      span.tabIndex = 0;
      span.textContent = matched;
      var tip = document.createElement("span");
      tip.className = "glossary-tooltip";
      tip.setAttribute("role", "tooltip");
      tip.textContent = entry.definition;
      if (entry.derivation) {
        var ref = document.createElement("span");
        ref.className = "glossary-ref";
        ref.textContent = "See Derivation " + entry.derivation;
        tip.appendChild(ref);
      }
      span.appendChild(tip);
      fragment.appendChild(span);
      lastIndex = regex.lastIndex;
      replaced = true;
    }
    if (replaced) {
      if (lastIndex < text.length) {
        fragment.appendChild(document.createTextNode(text.slice(lastIndex)));
      }
      parent.replaceChild(fragment, textNode);
    }
  }

  function annotate() {
    var main = document.querySelector("main, .bd-content, article, #main-content");
    if (!main) main = document.body;
    var walker = document.createTreeWalker(main, NodeFilter.SHOW_TEXT, null, false);
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (var i = nodes.length - 1; i >= 0; i--) {
      annotateNode(nodes[i]);
    }
  }

  function init() {
    fetch("_static/glossary.json")
      .then(function(r) { return r.json(); })
      .then(function(data) {
        GLOSSARY = data;
        createToggle();
        applyState();
        // Wait for MathJax to finish before annotating, so that
        // rendered math lives inside mjx-container elements and the
        // parent.closest("mjx-container") guard in annotateNode works.
        if (window.MathJax && MathJax.startup && MathJax.startup.promise) {
          MathJax.startup.promise.then(annotate).catch(annotate);
        } else {
          // MathJax not loaded — annotate immediately
          annotate();
        }
      })
      .catch(function() {
        // Glossary unavailable — degrade silently
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
"""
    (static_dir / "glossary.js").write_text(tooltip_js)
    print("  _static/glossary.js")


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

    print("\nFetching static assets...")
    static_sources = fetch_static_assets(local_root)

    if args.check_only:
        total = sum(len(f) for f in sources.values())
        expected = sum(len(c["files"]) for c in REPOS.values()) + sum(
            len(v) for v in DATA_FILES.values())
        static_total = sum(len(f) for f in static_sources.values())
        static_expected = sum(len(c["files"]) for c in STATIC_ASSETS.values())
        print(f"\n{total}/{expected} source files reachable.")
        print(f"{static_total}/{static_expected} static assets reachable.")
        return 0 if total == expected and static_total == static_expected else 1

    print("\nWriting book sources...")
    write_book_sources(sources)

    print("\nCopying static assets...")
    copy_static_assets(static_sources)

    print("\nResolving script references and cross-links...")
    resolve_script_references()

    print("\nGenerating Jupyter Book config...")
    generate_config()
    generate_toc()
    generate_intro()

    print("\nGenerating machine-readable metadata...")
    generate_derivation_graph()
    generate_glossary()
    generate_glossary_page()
    generate_reference_pages()

    print("\nResolving {doc} cross-references in reference pages...")
    resolve_doc_crossrefs()

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
