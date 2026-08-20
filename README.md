# proslambenomenos-site

Presentation layer for [proslambenomenos](https://github.com/nickjoven/proslambenomenos).
This repo holds chrome and a build script only — **no claim prose of
its own**. Every deploy is built from a *pinned evidence tag*
(`SOURCE_REF` in the workflow) of the source repository, and the
deploy job runs only after the source's full gate suite passes in CI.
Updating the site's content is a one-line diff: bump the ref to a
newer sealed link.

The previous pipeline (Jupyter Book aggregation of four repositories
from moving branches, daily cron) is retired — it was presentation
drift by design; its history remains in git. The framework content it
served is preserved on the source repo's `archive/2026-04-framework`
branch and is retracted; see the provenance note on the site itself.

Local test:

    SOURCE_REF=link-002 python3 build.py --source /path/to/proslambenomenos
    # output in site/
