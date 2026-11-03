# Blog recovery TODO

## Milestone 1: Raw archive and Markdown extraction

Recover the blog, supporting pages, comments, and public Flickr photo collection
from public sources. The raw archive and Markdown extraction are committed; a
basic GitHub Pages site is now in progress as a separate change.

Current priority was to download raw blog responses into `extraction/raw/`. The raw capture
pass is complete for this checkpoint: 253 raw responses are saved. Of 186 posts
listed by the archive index, 175 have usable raw captures and 173 were extracted
to Markdown. Eleven indexed posts remain unavailable, and two captured 2005 pages
have no usable content region. See `extraction/raw/REPORT.md` and
`extraction/content/extraction-report.json`. Flickr image downloads, alternate historical
captures, comment extraction, and spam analysis remain deferred.

Reference capture: https://web.archive.org/web/20100406044023/http://theroadislife.com/

The inspected site identifies itself as Movable Type. Its archive index lists
186 individual posts from July 2005 through June 2007. Monthly archive pages are
not a recovery priority.

### 1. Set up Python with mise

- [x] Configure and pin a project Python version using mise.
- [x] Create a project-local `.venv` using the mise-managed Python.
- [x] Ignore `.venv` and Python caches in Git.
- [x] Declare and pin recovery/extraction dependencies (`extraction/pyproject.toml` and `extraction/uv.lock`).
- [x] Document environment setup and running commands through mise.

### 2. Discover content

- [x] Inventory Wayback captures for both bare and `www` domains using the CDX API.
- [x] Combine archive-index, feed, and internal links into a post/page checklist.
- [x] Record links to Flickr pages and embedded photo URLs in the raw manifest.
- [x] Record discovery sources and distinguish confirmed post totals from unknown Flickr coverage.

### 3. Download originals

- [x] Implement resumable downloads with cached successes, conservative pacing,
      bounded retries, rate-limit backoff, and a persistent failure log.
- [x] Preserve raw HTML before extraction or rewriting in `extraction/raw/objects/`.
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

- [x] Create UTF-8 Markdown files for recovered individual posts in `extraction/content/` (173 created).
- [x] Include title, original publication date, author when available, original URL,
      and capture provenance in metadata.
- [x] Preserve post wording, links, captions, and meaningful formatting.
- [x] Deduplicate extracted entries by their original archive-index permalink.
- [ ] Prefer complete individual posts; use homepage or feed copies if available
      for gaps and explicitly label partial recoveries. Monthly archive pages are
      not a priority.
- [x] Keep Flickr images linked to Flickr; copy the already recovered local image
      referenced by a post into `extraction/photos/` and use a relative path.
- [x] Use content hashes for copied photo filenames; image-source metadata remains
      in each post's frontmatter.
- [x] Retain external image URLs in Markdown where photo downloads were deferred.
- [x] Keep generated Markdown under `extraction/content/` and raw source captures unchanged.
- [x] Extract About, FAQ, and Thank You supporting pages to `extraction/content/pages/` with
      source capture metadata.
- [ ] Recover two malformed/partial 2005 post captures; see `extraction/content/extraction-report.json`.

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
      region in `extraction/content/extraction-report.json`.
- [x] Report Flickr completeness as unknown; the public collection total is not established.
- [x] Document scripts, dependencies, rerun instructions, archive structure, and known gaps.
- [ ] Package `extraction/content/`, `extraction/photos/`, `extraction/raw/`, scripts, and reports
      with checksums and instructions for maintaining independent backup copies.

## Milestone 2: Basic static site

- [x] Move the recovery tools, raw captures, Markdown, and photos into `extraction/`;
      reserve `blog/` for the Hugo site.
- [x] Pin Hugo in the root `mise.toml`; run the same pinned Hugo version locally and in GitHub Actions.
- [x] Configure Hugo to mount `extraction/content/` and `extraction/photos/` directly,
      keeping the source archive outside the published output.
- [x] Add a readable journal index, individual post pages, and supporting pages.
- [x] Add an Archives index with monthly groups and links to the recovered entries.
- [x] Restore an archive-by-category index from captured category pages and recovered posts.
- [x] Restore the Kerouac header quote and the original “What is this place?” introduction.
- [x] Add a GitHub Actions workflow to build and publish with GitHub Pages.
- [x] Build locally with the pinned Hugo version; verify the journal, supporting
      pages, and recovered local photo are present in the generated output.

The root `mise.toml` pins Hugo directly through mise's Hugo backend; Go is not
needed to build the site. The Python toolchain stays in `extraction/`.

The static build must publish only generated site files, not the raw capture archive.

Completion for milestone 1 means every discovered item is accounted for and
recovered content is independently readable. It does not imply the source services
preserved everything.
