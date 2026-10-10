# APOS project website

This directory contains the static promotional website, separate from the Python application. `index.html` and `style.css` form the landing page. Bilingual role guides are rendered from `docs/` by `scripts/build_docs.py` into ignored HTML files under `site/docs/`; `site/docs/docs.css` is their shared stylesheet. Markdown is the source of truth, so edit the guides there and rebuild instead of editing generated HTML. The illustrative tab contains invented sample orders, not patron data. No scripts, external fonts, analytics, cookies or forms are used.

The GitHub Actions workflow in `.github/workflows/pages.yml` publishes this directory on changes to `main`, or when manually dispatched. GitHub Pages must use **GitHub Actions** as its build source in repository Settings → Pages. If automatic enablement lacks permission, a repository administrator must enable Pages there before rerunning the workflow.

Expected project URL after successful deployment: https://dignin.github.io/APOS/

Build the documentation first with `.venv/bin/python scripts/build_docs.py` (requires the existing `markdown-it-py` dependency). The Pages workflow installs that renderer and builds all guides automatically when their sources change.

Preview locally from the repository root with `python3 -m http.server 8080 --directory site` and open http://localhost:8080.

Keep promotional copy aligned with the application and `docs/COMPLIANCE.md`. Do not add patron data, private codes, certification claims or invented endorsements.
