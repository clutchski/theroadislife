#!/usr/bin/env python3
"""Resumable raw capture. Never extracts or rewrites blog content."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import re
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
TARGET = "20100406044023"
FIELDS = "timestamp,original,mimetype,statuscode,digest"


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temp.replace(path)


def key(url):
    """Collapse only known scheme/host aliases, keeping path and query intact."""
    url = re.sub(r"^https?://web\.archive\.org/web/\d+[a-z_]*/", "", url)
    p = urlsplit(url)
    host = (p.hostname or "").lower()
    if host in {"www.theroadislife.com", "theroadislife.com"}:
        host = "theroadislife.com"
    return urlunsplit(("https", host, p.path or "/", p.query, ""))


def scope(url):
    p = urlsplit(key(url))
    if p.hostname != "theroadislife.com":
        return False
    if p.path.startswith("/archives/"):
        return bool(re.fullmatch(
            r"/archives/(?:[A-Za-z0-9_%~-]+/)*(?:[A-Za-z0-9_%~-]+\.(?:html?|gif|jpe?g|png|css|ico))?",
            p.path)) and not p.query
    return not p.path.startswith(("/cgi-", "/mt-static/", "/phpBB2", "/forum/",
                                  "/thesmokestacks", "/your-account-suspended"))


def parse_index(body):
    rows, end = json.JSONDecoder().raw_decode(body.lstrip())
    # CDX appends a blank line and resume key outside its JSON array.
    resume = body.lstrip()[end:].strip()
    return [dict(zip(rows[0], row)) for row in rows[1:]], resume


def request(url, timeout=45):
    """curl handles TLS with the platform trust store. Preserve response bytes."""
    with tempfile.TemporaryDirectory() as temp:
        body = Path(temp) / "body"
        headers = Path(temp) / "headers"
        result = subprocess.run([
            "curl", "--silent", "--show-error", "--location", "--max-redirs", "5",
            "--connect-timeout", "15", "--max-time", str(timeout),
            "--user-agent", "TheRoadIsLife-preservation/0.1 (public archive recovery)",
            "--dump-header", str(headers), "--output", str(body),
            "--write-out", "%{json}", url,
        ], capture_output=True)
        info = json.loads(result.stdout or b"{}")
        return (body.read_bytes() if body.exists() else b"", {
            "requested_url": url, "final_url": info.get("url_effective", url),
            "http_status": info.get("http_code", 0),
            "content_type": info.get("content_type"), "curl_exit": result.returncode,
            "error": result.stderr.decode(errors="replace"),
            "headers": headers.read_text(errors="replace") if headers.exists() else "",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        })


def store_response(body, meta):
    digest = hashlib.sha256(body).hexdigest()
    path = RAW / "objects" / digest[:2] / digest
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temp:
            temp.write(body)
            temp_path = Path(temp.name)
        temp_path.replace(path)
    meta.update(path=str(path.relative_to(ROOT)), sha256=digest, size=len(body))
    match = re.search(r"/web/(\d{14})", meta["final_url"])
    meta["capture_timestamp"] = match.group(1) if match else None
    return meta


def acceptable(body, meta, kind):
    if meta["curl_exit"] or meta["http_status"] != 200 or not body:
        return False
    head = body[:200000].lower()
    if any(s in head for s in [b"wayback machine has not archived that url",
                              b"this url has been excluded", b"this site has been excluded",
                              b"account suspended", b"<title>wayback machine</title>"]):
        return False
    if kind == "image" or (meta.get("content_type") or "").startswith("image/"):
        from PIL import Image
        import io
        try:
            with Image.open(io.BytesIO(body)) as im:
                im.verify()
        except Exception:
            return False
    return True


def inventory():
    initial = RAW / "indexes" / "initial-url-inventory.json"
    if not initial.exists():
        params = dict(url="theroadislife.com", matchType="domain", output="json",
                      filter="statuscode:200", collapse="urlkey", fl=FIELDS,
                      limit=5000, showResumeKey="true")
        body, meta = request("https://web.archive.org/cdx/search/cdx?" + urlencode(params), 90)
        store_response(body, meta)
        write_json(RAW / "indexes" / "initial-url-inventory.response.json", meta)
        if not acceptable(body, meta, "index"):
            raise RuntimeError("Unable to fetch all-date URL inventory; see response metadata")
        _, more = parse_index(body.decode())
        if more:
            raise RuntimeError("All-date inventory exceeds 5000 URLs; pagination must be extended before proceeding")
        initial.write_bytes(body)
    resume = ""
    page = 0
    while True:
        path = RAW / "indexes" / f"captures-{page:04}.json"
        if path.exists():
            rows, resume = parse_index(path.read_text())
        else:
            params = dict(url="theroadislife.com", matchType="domain", output="json",
                          filter="statuscode:200", **{"from": "2005", "to": "2011"},
                          fl=FIELDS, limit=5000, showResumeKey="true")
            if resume:
                params["resumeKey"] = resume
            body, meta = request("https://web.archive.org/cdx/search/cdx?" + urlencode(params), 90)
            store_response(body, meta)
            write_json(RAW / "indexes" / f"captures-{page:04}.response.json", meta)
            if not acceptable(body, meta, "index"):
                raise RuntimeError(f"CDX failed: {meta['http_status']} {meta['error']}")
            rows, resume = parse_index(body.decode())
            path.write_bytes(body)
        print(f"Inventory page {page}: {len(rows)} captures", flush=True)
        if not resume:
            break
        page += 1
        time.sleep(2)


def load_queue():
    path = RAW / "manifest.json"
    return json.loads(path.read_text()) if path.exists() else {}


def seed(queue):
    paths = sorted((RAW / "indexes").glob("captures-[0-9][0-9][0-9][0-9].json"))
    initial = RAW / "indexes" / "initial-url-inventory.json"
    if initial.exists():
        paths.append(initial)
    for path in paths:
        rows, _ = parse_index(path.read_text())
        for row in rows:
            url = row["original"]
            k = key(url)
            if k not in queue:
                queue[k] = dict(original_url=url, kind="blog", sources=[str(path.relative_to(ROOT))],
                                captures=[], status="pending" if scope(url) else "excluded",
                                reason=None if scope(url) else "Outside blog: forum, software, unrelated site, or CGI endpoint")
            if row not in queue[k]["captures"]:
                queue[k]["captures"].append(row)
    for suffix in ["/", "/archives.htm", "/about.htm", "/faq.htm", "/latest.htm",
                   "/contact.php", "/shop.htm", "/index.xml", "/index.rdf", "/atom.xml"]:
        add(queue, "http://www.theroadislife.com" + suffix, "blog", "seed")
    add(queue, "https://www.flickr.com/photos/theroadislife/", "flickr", "seed")
    add(queue, "https://www.flickr.com/photos/theroadislife/albums/", "flickr", "seed")


def add(queue, url, kind, source):
    k = key(url)
    if k not in queue:
        queue[k] = dict(original_url=url, kind=kind, sources=[], captures=[], status="pending")
    if source not in queue[k]["sources"]:
        queue[k]["sources"].append(source)


def seed_history(queue):
    """Keep distinct aggregate versions that may contain otherwise lost posts."""
    for url, entry in list(queue.items()):
        if entry["kind"] != "blog" or not scope(entry["original_url"]):
            continue
        path = urlsplit(url).path
        if path not in {"/", "/archives.htm", "/index.xml", "/index.rdf", "/atom.xml"} and not re.fullmatch(
                r"/archives/(?:[A-Za-z0-9_%~-]+/)+index\.html?", path):
            continue
        captures_by_digest = {}
        for capture in sorted(entry["captures"], key=lambda c: c["timestamp"]):
            if "2005" <= capture["timestamp"][:4] <= "2011":
                captures_by_digest.setdefault(capture["digest"], capture)
        for capture in captures_by_digest.values():
            identifier = url + "#capture=" + capture["timestamp"]
            queue.setdefault(identifier, dict(original_url=capture["original"], kind="blog-history",
                             sources=["Historical aggregate capture from CDX"], captures=[capture], status="pending"))


def discover(queue, entry):
    """Extract URLs only, not post bodies or comments."""
    meta = entry.get("response")
    if not meta:
        return
    body = (ROOT / meta["path"]).read_bytes()
    content_type = meta.get("content_type") or ""
    if not any(t in content_type for t in ["html", "xml", "css"]):
        return
    base = entry["original_url"]
    urls = []
    if "xml" in content_type:
        try:
            tree = ET.fromstring(body)
            for element in tree.iter():
                name = element.tag.rsplit("}", 1)[-1]
                if name in {"link", "guid"} and (element.text or "").strip().startswith(("http://", "https://")):
                    urls.append((element.text.strip(), "a", "href"))
                for attr in ("href", "src"):
                    if element.get(attr):
                        urls.append((element.get(attr), name, attr))
        except ET.ParseError:
            # Preserve malformed XML; known absolute URLs can still seed discovery.
            urls.extend((value, "a", "href") for value in re.findall(
                r'https?://[^\s<>"\x27]+', body.decode(errors="replace")))
    else:
        soup = BeautifulSoup(body, "html.parser")
        urls = [(tag.get(attr), tag.name, attr) for tag in soup.find_all(True)
                for attr in ("href", "src", "data") if tag.get(attr)]
    urls += [(m, "asset", "src") for m in re.findall(r'url\([\s\"\x27]*([^\s)\"\x27]+)', body.decode(errors="replace"))]
    for value, tag, attr in urls:
        url = urljoin(base, value)
        if urlsplit(url).scheme not in ("http", "https"):
            continue
        url = key(url)
        host = urlsplit(url).hostname or ""
        path = urlsplit(url).path
        if scope(url):
            add(queue, url, "blog", base)
        elif host.endswith("static.flickr.com") or host.endswith("staticflickr.com"):
            add(queue, url, "image", base)
        elif host in {"www.flickr.com", "flickr.com"} and path.startswith("/photos/theroadislife/"):
            # Avoid login, comment, favorites, and slideshow action URLs.
            if re.fullmatch(r"/photos/theroadislife/(?:\d+/?|(?:sets|albums)(?:/\d+)?/?|page\d+/?|)", path):
                add(queue, url, "flickr", base)
        elif tag in {"img", "asset", "object"}:
            add(queue, url, "external-asset", base)


def download(item):
    k, entry = item
    if entry["kind"] in {"flickr", "image"}:
        urls = [key(entry["original_url"])]
    else:
        target_date = datetime.strptime(TARGET, "%Y%m%d%H%M%S")
        captures = sorted(entry["captures"], key=lambda c: abs(
            (datetime.strptime(c["timestamp"], "%Y%m%d%H%M%S") - target_date).total_seconds()))
        urls = [f"https://web.archive.org/web/{c['timestamp']}id_/{c['original']}" for c in captures[:3]]
        if not urls:
            urls = [f"https://web.archive.org/web/{TARGET}id_/{entry['original_url']}"]
        # A different replay date/host spelling may recover a failed indexed capture.
        if entry["kind"] != "blog-history":
            urls.append(f"https://web.archive.org/web/{TARGET}id_/{key(entry['original_url']).replace('https://theroadislife.com', 'http://www.theroadislife.com')}")
    entry.setdefault("attempts", [])
    for url in dict.fromkeys(urls):
        for retry in range(2):
            body, meta = request(url)
            store_response(body, meta)
            entry["attempts"].append(meta)
            if acceptable(body, meta, entry["kind"]):
                entry.update(status="downloaded", response=meta)
                entry.pop("reason", None)
                return k, entry
            if body and meta["http_status"] not in (0, 429, 500, 502, 503, 504):
                break
            time.sleep(5 * (retry + 1))
        time.sleep(2)
    last = entry["attempts"][-1]
    if last["curl_exit"]:
        reason = f"Transport error {last['curl_exit']}: {last['error'].strip()}"
    elif last["http_status"] != 200:
        origin = "Archived origin" if "x-archive-orig-" in last["headers"].lower() else "Server"
        reason = f"{origin} HTTP {last['http_status']}; no usable attempted capture"
    else:
        reason = "Empty response, archive error page, or invalid image despite HTTP 200"
    entry.update(status="failed", reason=reason)
    return k, entry


def report(queue):
    from collections import Counter
    counts = Counter(e["status"] for e in queue.values())
    posts = {url: {"status": e["status"], "response": e.get("response"), "reason": e.get("reason")}
             for url, e in sorted(queue.items())
             if re.search(r"/archives/\d{4}/\d{2}/(?!index\.)[^/]+\.htm$", url)
             and any(key(source) == "https://theroadislife.com/archives.htm" for source in e["sources"])}
    write_json(RAW / "post-inventory.json", posts)
    summary = {"counts": dict(counts), "flickr_completeness": "unknown",
               "archive_index_posts": {"total": len(posts),
                                       "statuses": dict(Counter(e["status"] for e in posts.values()))},
               "reference_capture": TARGET,
               "inventory_window": "All-date URL inventory plus detailed 2005–2011 captures",
               "note": "Raw responses only. Downloaded does not guarantee complete post text or comments.",
               "by_kind": {kind: dict(Counter(e["status"] for e in queue.values() if e["kind"] == kind))
                           for kind in sorted({e["kind"] for e in queue.values()})}}
    write_json(RAW / "report.json", summary)
    lines = ["# Raw download report", "", summary["note"], "",
             "Flickr is deferred to live-source recovery; collection completeness is unknown.", "",
             f"Archive index: {len(posts)} post URLs; " +
             f"{sum(e['status'] == 'downloaded' for e in posts.values())} downloaded. " +
             "See `post-inventory.json` for the checklist.", "",
             "| Kind | Downloaded | Pending | Failed | Deferred | Excluded |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for kind, counts_by_kind in summary["by_kind"].items():
        lines.append(f"| {kind} | " + " | ".join(str(counts_by_kind.get(s, 0)) for s in
                     ["downloaded", "pending", "failed", "deferred", "excluded"]) + " |")
    lines += ["", "## Unresolved blog URLs", ""]
    for url, e in sorted(queue.items()):
        if e["kind"] == "blog" and e["status"] in {"pending", "failed"}:
            lines.append(f"- {url} — {e['status']}: {e.get('reason', 'not yet downloaded')}")
    (RAW / "REPORT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summary), flush=True)


def verify(queue):
    checked = 0
    seen = set()
    for entry in queue.values():
        for meta in entry.get("attempts", []):
            if meta["path"] not in seen:
                body = (ROOT / meta["path"]).read_bytes()
                assert hashlib.sha256(body).hexdigest() == meta["sha256"], meta["path"]
                seen.add(meta["path"])
        if entry["status"] == "downloaded":
            meta = entry["response"]
            body = (ROOT / meta["path"]).read_bytes()
            assert hashlib.sha256(body).hexdigest() == meta["sha256"], meta["path"]
            assert acceptable(body, meta, entry["kind"]), meta["path"]
            checked += 1
    print(f"Verified {checked} downloaded responses and {len(seen)} unique attempt objects", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["inventory", "download", "report", "verify"])
    parser.add_argument("--limit", type=int, default=0, help="Maximum downloads this run; 0 means all")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--include-flickr", action="store_true", help="Also fetch live public Flickr pages and images")
    parser.add_argument("--include-images", action="store_true", help="Also fetch local and external image URLs")
    parser.add_argument("--history", action="store_true", help="Also preserve distinct historical homepages, monthly archives, and feeds")
    args = parser.parse_args()
    if args.limit < 0:
        parser.error("--limit must be nonnegative")
    RAW.mkdir(exist_ok=True)
    if args.command == "inventory":
        inventory()
    queue = load_queue()
    seed(queue)
    if args.history:
        seed_history(queue)
    for entry in queue.values():
        if entry["kind"] == "blog" and not scope(entry["original_url"]):
            entry.update(status="excluded", reason="Outside blog URL structure or excluded historical subsystem")
        elif entry["kind"] == "blog" and entry["status"] == "excluded":
            entry.update(status="downloaded" if entry.get("response") else "pending")
            entry.pop("reason", None)
    if args.retry_failed:
        for entry in queue.values():
            if entry["status"] == "failed":
                entry["status"] = "pending"
    if args.command == "download":
        for entry in list(queue.values()):
            if entry["status"] == "downloaded":
                meta = entry["response"]
                path = ROOT / meta["path"]
                if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != meta["sha256"]:
                    entry.update(status="pending", reason="Cached object missing or checksum mismatch")
                else:
                    discover(queue, entry)
        done = 0
        # Four parallel requests keeps archive traffic useful while staying modest.
        workers = 4
        with ThreadPoolExecutor(max_workers=workers) as pool:
            while True:
                pending = [(k, e) for k, e in queue.items() if e["status"] == "pending"
                           and (e["kind"].startswith("blog")
                                or (args.include_flickr and e["kind"] == "flickr")
                                or (args.include_images and e["kind"] in {"image", "external-asset"}))]
                # Blog pages first, then Flickr metadata and images.
                pending.sort(key=lambda item: (item[1]["kind"] != "blog", item[0]))
                batch = pending[:min(workers, args.limit - done) if args.limit else workers]
                if not batch:
                    break
                for k, entry in pool.map(download, batch):
                    queue[k] = entry
                    if entry["status"] == "downloaded":
                        discover(queue, entry)
                    done += 1
                    write_json(RAW / "manifest.json", queue)
                    print(f"{done}: {entry['status']} {k}", flush=True)
                time.sleep(1)
                if args.limit and done >= args.limit:
                    break
    write_json(RAW / "manifest.json", queue)
    if args.command == "verify":
        verify(queue)
    report(queue)


if __name__ == "__main__":
    RAW.mkdir(exist_ok=True)
    with (RAW / ".download.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("Another raw recovery command is running; wait for it to finish.")
        main()
