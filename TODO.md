# Blog recovery TODO

## Milestone 1: A portable Markdown and photo archive

Recover the blog, supporting pages, comments, and public Flickr photo collection
from public sources. Static-site design, generation, and hosting are deferred.

Current priority was to download raw blog responses into `raw/`. The raw capture
pass is complete for this checkpoint: 253 responses are saved, including 175 of
the 186 individual posts in the archive index. Eleven indexed post URLs remain
unresolved; see `raw/REPORT.md`. Image downloads and alternate historical captures
are deferred. Original pages retain the image URLs. Parsing, Markdown conversion,
comment extraction, and spam analysis are later steps.

Reference capture: https://web.archive.org/web/20100406044023/http://theroadislife.com/

The inspected site identifies itself as Movable Type. Its archive index lists
186 individual posts from July 2005 through June 2007. Monthly archive pages are
not a recovery priority.

### 1. Set up Python with mise

- [x] Configure and pin a project Python version using mise.
- [x] Create a project-local `.venv` using the mise-managed Python.
- [x] Ignore `.venv` and Python caches in Git.
- [x] Declare and pin recovery/extraction dependencies (`pyproject.toml` and `uv.lock`).
- [x] Document environment setup and running commands through mise.

### 2. Discover content

- [x] Inventory Wayback captures for both bare and `www` domains using the CDX API.
- [x] Combine archive-index, feed, and internal links into a post/page checklist.
- [x] Record links to Flickr pages and embedded photo URLs in the raw manifest.
- [x] Record discovery sources and distinguish confirmed post totals from unknown Flickr coverage.

### 3. Download originals

- [x] Implement resumable downloads with cached successes, conservative pacing,
      bounded retries, rate-limit backoff, and a persistent failure log.
- [x] Preserve raw HTML before extraction or rewriting in `raw/objects/`.
- [x] Prefer captures near April 6, 2010, record actual capture dates, and retain
      failed/alternate capture attempts in the manifest.
- [ ] (Deferred) Recover Flickr images from the live source if desired; use external
      links for the first Markdown pass unless later asked to save image files.
- [ ] (Deferred) Download local site images and historical assets if needed.
- [x] Record original URL, capture URL/date, retrieval date, local path, checksum,
      and recovery status in machine-readable manifests.
- [x] Detect HTTP errors, empty responses, invalid images, redirects, and failed
      captures rather than silently counting them as recovered content.

### 4. Extract Markdown

- [x] Create UTF-8 Markdown files for recovered individual posts in `content/` (173 created).
- [x] Include title, original publication date, author when available, original URL,
      and capture provenance in metadata.
- [x] Preserve post wording, links, captions, and meaningful formatting.
- [x] Deduplicate extracted entries by their original archive-index permalink.
- [ ] Prefer complete individual posts; use homepage, monthly archive, or feed copies
      when needed and explicitly label partial recoveries.
- [x] Keep Flickr images linked to Flickr; copy the already recovered local image
      referenced by a post into `photos/` and use a relative path.
- [ ] Deduplicate identical image files by checksum without losing source associations.
- [x] Retain external image URLs in Markdown where photo downloads were deferred.
- [x] Keep generated Markdown under `content/` and raw source captures unchanged.
- [ ] Recover two malformed/partial 2005 post captures; see `content/extraction-report.json`.

### 5. Preserve comments and photo metadata

- [ ] Extract comments separately as JSON with available author, date, body,
      identifiers, and provenance; keep original captured pages in `archive/`.
- [ ] (Deferred) Preserve Flickr photo IDs, titles, descriptions, dates, attribution,
      album membership, and source URLs alongside the photo set.
- [ ] Perform basic comment spam analysis: duplicate text, repeated domains,
      link density, and suspicious posting bursts.
- [ ] Produce reviewable spam flags without deleting comments. Defer publication decisions.

### 6. Validate and package

- [x] Account for each archive-index post as downloaded or unresolved with a reason.
- [x] Verify local Markdown image links resolve; external Flickr image links remain online references.
- [x] Spot check early, middle, and final posts against source captures; verify
      title/date metadata, raw checksums, body text, and image links.
- [ ] Test alternate-source recovery, malformed HTML, accented text, and comments.
- [x] Verify interrupted downloads resume without re-downloading successful files.
- [x] Produce a coverage report listing unresolved URLs and deferred work.
- [x] Preserve 253 raw responses, capture indexes, and manifests in the separate
      data commit `5822b53`; recovery code is in `6b72e6b`.
- [ ] Produce a coverage report listing partial text,
      conflicting captures, and remaining recovery tasks.
- [x] Record extraction results and the two captured pages with no usable content
      region in `content/extraction-report.json`.
- [ ] Report Flickr completeness as unknown unless a reliable inventory establishes the total.
- [ ] Document scripts, dependencies, rerun instructions, archive structure, and known gaps.
- [ ] Package `content/`, `photos/`, `archive/`, `manifests/`, scripts, and reports
      with checksums and instructions for maintaining independent backup copies.

Completion means every discovered item is accounted for and recovered content is
independently readable. It does not imply the source services preserved everything.
