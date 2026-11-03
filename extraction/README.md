# Recovery archive

This directory contains the Python recovery environment and all recovered source
material. Raw responses in `raw/` are immutable inputs. Extracted Markdown and
photos live in `content/` and `photos/`.

## Set up Python

Install [mise](https://mise.jdx.dev/getting-started.html), then from this directory:

```sh
mise trust
mise install
mise run setup
```

`mise.toml` pins Python 3.14.3 and uv 0.11.6, and creates a local `.venv`.
`pyproject.toml` declares dependencies and `uv.lock` pins their exact versions.

## Recover and extract

The downloader uses the system `curl` executable.

```sh
mise run raw:inventory
mise run raw:download
mise run raw:verify
mise run test
mise exec -- python scripts/extract_markdown.py
```

Downloads resume from `raw/manifest.json`. Flickr URLs are recorded but deferred;
the raw captures preserve the original links. `download --include-flickr` fetches
public Flickr URLs, and `download --include-images` fetches other image URLs.
The `--history` option preserves distinct older homepages, archive pages, and feeds.

The extractor writes post Markdown to `content/`, supporting pages to
`content/pages/`, images to `photos/`, and its report to
`content/extraction-report.json`. Use `--supporting-only` to refresh About, FAQ,
and Thank You without reprocessing the posts. Use `--clean` to regenerate all
Markdown and photos from the saved raw archive.
