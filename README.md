# Maple's blog

This repository was restored from the published `gh-pages` output of `maple-pwn.github.io`.

## What was recovered

- A standard local MkDocs project layout
- Recovered Markdown pages under `docs/`
- Static assets and custom resources preserved under `docs/`
- Pinned MkDocs versions based on the deployed site metadata
- A GitHub Actions deployment workflow for a source branch -> `gh-pages` flow

## Important limitation

The original Markdown source files and original `mkdocs.yml` were not present in the published branch.
This repository was reconstructed from the deployed site output, so the recovered Markdown is best-effort rather than byte-for-byte identical to the original authoring source.

In other words:

- `docs/` is now a source-style tree again
- most article pages were recovered back into `index.md`
- some links and formatting may still need manual cleanup

## Local build

1. Install Python
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Build locally:

   ```bash
   mkdocs build
   ```

4. Serve locally:

   ```bash
   mkdocs serve
   ```

## Reconstruction tooling

If you need to rerun the HTML -> Markdown recovery pipeline:

```bash
pip install -r requirements-recover.txt
python scripts/recover_mkdocs_source.py
```

## Repository note

The remote repository currently exposes only a deployed `gh-pages` branch.
The intended next-step layout is:

- `main`: source branch with `docs/`, `mkdocs.yml`, workflow
- `gh-pages`: generated site published by `mkdocs gh-deploy`

If you later recover the original Markdown authoring source from another backup or branch, you can replace the reconstructed pages under `docs/` and keep the rest of this repository layout.
