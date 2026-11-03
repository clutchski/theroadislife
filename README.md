# theroadislife

Recover the historical blog as Markdown and local photographs. See [TODO.md](TODO.md)
for the recovery checklist.

## Python setup

Install [mise](https://mise.jdx.dev/getting-started.html), then run:

```sh
mise trust
mise install
mise run setup
mise exec -- python --version
```

`mise.toml` pins Python 3.14.3 and automatically creates a local `.venv` using
Python's standard `venv` module. See the [mise Python documentation](https://mise.jdx.dev/lang/python).

Run Python commands in the environment with:

```sh
mise exec -- python -c 'import sys; print(sys.executable)'
mise exec -- uv run --locked python -c 'import bs4, markdownify, PIL'
```

With mise shell activation configured, the environment is activated automatically
in this directory. `.venv` and Python caches are excluded from Git.

## Dependencies

`pyproject.toml` declares direct dependencies; `uv.lock` pins the resolved versions
and artifact hashes, including transitive dependencies. Mise pins Python and uv.
`mise run setup` installs from the lock and fails if it is out of date.

- Beautiful Soup parses archived HTML.
- markdownify converts extracted content to Markdown.
- Pillow validates recovered images.

To intentionally change dependencies, edit `pyproject.toml`, then run
`mise exec -- uv lock` followed by `mise run setup`. Review and commit both
`pyproject.toml` and `uv.lock`. Do not install project dependencies with ad hoc pip commands.

## Download raw sources

The downloader uses the system `curl` executable (included with macOS).

```sh
mise exec -- python scripts/download_raw.py inventory
mise exec -- python scripts/download_raw.py download
mise exec -- python scripts/download_raw.py download --history
mise exec -- python scripts/download_raw.py verify
mise exec -- python scripts/download_raw.py report
```

Downloads checkpoint after each URL. Rerunning skips completed downloads; use
`download --retry-failed` to retry failures or `download --limit 10` for a small batch.
Two workers and pauses limit archive traffic. Responses and provenance live in
[`raw/`](raw/README.md); no Markdown conversion is performed yet.
Flickr and other image links are inventoried in the manifest but are not downloaded
by default. The raw pages preserve their original image URLs. If Flickr is needed,
recover its live photos as a separate step (`download --include-flickr`); local and
other image URLs can be fetched with `download --include-images`.
The optional `--history` pass preserves distinct 2005–2011 homepage, archive, and
feed versions for later recovery of posts whose individual pages are missing.

Run downloader tests with `mise exec -- python -m unittest discover -s tests`.
