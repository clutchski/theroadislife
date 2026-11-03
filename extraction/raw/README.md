# Raw source archive

This directory contains original response bodies, not extracted posts. Do not edit
objects in place. Markdown conversion and comment analysis are separate later steps.

- `indexes/`: original Wayback CDX responses. The preliminary URL inventory spans
  all dates; the detailed capture inventory covers 2005–2011 around the 2010 reference.
- `objects/<prefix>/<sha256>`: exact downloaded response bodies, including failed
  responses for diagnosis. Identical bytes share an object; filenames are content hashes.
- `manifest.json`: original URLs, discovery sources, available captures, attempts,
  HTTP headers/status, final URLs, capture/retrieval times, object paths, checksums,
  and deferred work.
- `report.json`: current counts and limitations.
- `REPORT.md`: a readable summary and unresolved blog URLs.
- `post-inventory.json`: URL checklist from the blog's archive index, with download status.

`downloaded` means a nonempty HTTP 200 response passed basic error checks (and
image decoding for Flickr images). It does not establish that a post, its comments,
or a Flickr collection is complete. Failed and excluded URLs remain in the manifest.

The downloader chooses up to three captures closest to the reference date per URL,
stopping at the first usable response, with a reference-date replay fallback.
The `--history` pass additionally preserves one capture per distinct CDX digest
for 2005–2011 homepages, monthly archives, archive indexes, and feeds. These are
listed as `blog-history` records with a `#capture=timestamp` identifier.
It does not download every historical version of every individual post.
Flickr and other image URLs are recorded but deferred by default. `--include-flickr`
fetches public Flickr URLs from the live source only; no Wayback fallback is used.
`--include-images` fetches local and other external image URLs.
No original blog host is contacted.
Forum/CGI endpoints, bundled software documentation, and the unrelated band site are
excluded from downloads but retained when present in the index.

Discovery reads links and asset references only. It never rewrites stored HTML,
executes archived JavaScript, submits forms, or extracts post/comment text.

Back up this entire directory together with the recovery scripts and lockfile.
