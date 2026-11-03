# Blog recovery TODO

## Milestone 1: A portable Markdown and photo archive

Recover the blog, supporting pages, comments, and public Flickr photo collection
from public sources. Static-site design, generation, and hosting are deferred.

Current priority: download original blog responses into `raw/` first. Parsing,
Markdown conversion, comment extraction, and spam analysis are separate later steps.
Record Flickr URLs during blog recovery; download Flickr from its live source separately.

Reference capture: https://web.archive.org/web/20100406044023/http://theroadislife.com/

The inspected site identifies itself as Movable Type. Its archive index includes
posts from July 2005 through June 2007; individual content recovery is not yet verified.

### 1. Set up Python with mise

- [x] Configure and pin a project Python version using mise.
- [x] Create a project-local `.venv` using the mise-managed Python.
- [x] Ignore `.venv` and Python caches in Git.
- [x] Declare and pin recovery/extraction dependencies (`pyproject.toml` and `uv.lock`).
- [x] Document environment setup and running commands through mise.

### 2. Discover content

- [x] Inventory Wayback captures for both bare and `www` domains using the CDX API.
- [ ] Combine archive-index, feed, and internal links into a post/page checklist.
- [ ] Inventory the linked public Flickr account, albums, and embedded photo URLs.
- [ ] Record discovery sources and distinguish confirmed totals from unknown coverage.

### 3. Download originals

- [x] Implement resumable downloads with cached successes, conservative pacing,
      bounded retries, rate-limit backoff, and a persistent failure log.
- [x] Preserve raw HTML before extraction or rewriting in `raw/objects/`.
- [ ] Prefer complete captures nearest April 6, 2010; use other captures to fill
      gaps, record actual capture dates, and flag conflicting versions.
- [ ] (Deferred) Recover Flickr images from the live source if desired; retain the
      highest available resolution and any smaller version that is the only copy.
- [ ] Download other relevant images and historical assets referenced by the blog.
- [x] Record original URL, capture URL/date, retrieval date, local path, checksum,
      and recovery status in machine-readable manifests.
- [ ] Detect error pages, redirects, temporary failures, and incomplete captures
      rather than silently counting them as recovered content.

### 4. Extract Markdown

- [ ] Create one UTF-8 Markdown file per post or supporting page in `content/`.
- [ ] Include title, original publication date, author when available, original URL,
      and capture provenance in metadata.
- [ ] Preserve original wording, punctuation, links, captions, and meaningful formatting.
- [ ] Deduplicate posts by original permalink, retaining alternate-source associations.
- [ ] Prefer complete individual posts; use homepage, monthly archive, or feed copies
      when needed and explicitly label partial recoveries.
- [ ] Store images in `photos/` and rewrite Markdown image links to relative local paths.
- [ ] Deduplicate identical image files by checksum without losing source associations.
- [ ] Mark unavailable images explicitly instead of leaving unexplained broken links.
- [ ] Keep generated extraction and manual corrections separate so reruns preserve review work.

### 5. Preserve comments and photo metadata

- [ ] Extract comments separately as JSON with available author, date, body,
      identifiers, and provenance; keep original captured pages in `archive/`.
- [ ] (Deferred) Preserve Flickr photo IDs, titles, descriptions, dates, attribution,
      album membership, and source URLs alongside the photo set.
- [ ] Perform basic comment spam analysis: duplicate text, repeated domains,
      link density, and suspicious posting bursts.
- [ ] Produce reviewable spam flags without deleting comments. Defer publication decisions.

### 6. Validate and package

- [ ] Account for every discovered post/page as recovered, partial, or unresolved with a reason.
- [ ] Verify local Markdown image links and successful image decoding.
- [ ] Test representative extraction cases: full posts, alternate-source recovery,
      malformed HTML, accented text, images, and comments.
- [ ] Compare representative early, middle, and final posts against source captures.
- [ ] Verify interrupted downloads resume without re-downloading successful files.
- [ ] Produce a coverage report listing missing pages/photos, partial text,
      conflicting captures, and remaining recovery tasks.
- [ ] Report Flickr completeness as unknown unless a reliable inventory establishes the total.
- [ ] Document scripts, dependencies, rerun instructions, archive structure, and known gaps.
- [ ] Package `content/`, `photos/`, `archive/`, `manifests/`, scripts, and reports
      with checksums and instructions for maintaining independent backup copies.

Completion means every discovered item is accounted for and recovered content is
independently readable. It does not imply the source services preserved everything.
